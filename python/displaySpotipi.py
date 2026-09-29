#!/usr/bin/env python3
"""
displaySpotipi.py -- spotipi photo-frame + Spotify display daemon.

One always-running process. Every loop it re-reads config/state.json (written
by the web UI) so brightness, mode, timer and schedule changes apply instantly
with no service restart. It does a photo slideshow and switches to Spotify
album art whenever music is playing.

Usage:
    python displaySpotipi.py <spotify_username> <path_to_.cache_token>

Matrix hardware options come from config/rgb_options.ini.
Photos come from the photos/ folder (mirrored from Apple Photos by the Mac).
"""

import os
import sys
import time
import random
import logging
from io import BytesIO
from datetime import datetime

# Runs as root (GPIO), so any __pycache__/*.pyc it writes end up root-owned and
# the non-root auto-updater can't overwrite/delete them. Don't write bytecode.
sys.dont_write_bytecode = True

import requests
from PIL import Image
from rgbmatrix import RGBMatrix, RGBMatrixOptions
import configparser

from getSongInfo import getSongInfo
from state import read_state, write_status, PREVIEW_PATH
from display_logic import compute_effective, effective_brightness, logo_image_path

STATUS_WRITE_SECONDS = 10.0    # heartbeat: refresh status.json at least this often

DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(DIR, "..", "config", "rgb_options.ini")
PHOTOS_DIR = os.path.abspath(os.path.join(DIR, "..", "photos"))

SPOTIFY_POLL_SECONDS = 2.0     # how often to ask Spotify what's playing
PHOTO_RESCAN_SECONDS = 10.0    # how often to rescan the photos folder
LOOP_SLEEP = 0.5

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    level=logging.INFO,
)
log = logging.getLogger("spotipi")


def load_matrix():
    config = configparser.ConfigParser()
    config.read(os.path.abspath(CONFIG_PATH))
    d = config["DEFAULT"]
    options = RGBMatrixOptions()
    options.rows = int(d["rows"])
    options.cols = int(d["columns"])
    options.chain_length = int(d.get("chain_length", 1))
    options.parallel = int(d.get("parallel", 1))
    options.hardware_mapping = d.get("hardware_mapping", "adafruit-hat")
    options.gpio_slowdown = int(d.get("gpio_slowdown", 2))
    options.brightness = int(d.get("brightness", 60))
    if d.get("refresh_rate"):
        options.limit_refresh_rate_hz = int(d["refresh_rate"])
    default_image = os.path.join(DIR, "..", "config", d.get("default_image", "default.png"))
    options.drop_privileges = False   # stay root so we can read state.json, photos, token cache
    matrix = RGBMatrix(options=options)
    return matrix, os.path.abspath(default_image)


LOGOS_DIR = os.path.abspath(os.path.join(DIR, "..", "config", "logos"))


def list_photos():
    try:
        names = sorted(
            f for f in os.listdir(PHOTOS_DIR)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))
        )
    except FileNotFoundError:
        names = []
    return [os.path.join(PHOTOS_DIR, n) for n in names]


def fit(image, matrix):
    image = image.convert("RGB")
    if image.size != (matrix.width, matrix.height):
        image = image.copy()
        image.thumbnail((matrix.width, matrix.height), Image.Resampling.LANCZOS)
    return image


def main():
    if len(sys.argv) < 3:
        print("Usage: %s <spotify_username> <token_path>" % sys.argv[0])
        sys.exit(1)
    username, token_path = sys.argv[1], sys.argv[2]

    matrix, default_image_path = load_matrix()

    # --- caches / timers ---
    last_brightness = matrix.brightness
    last_spotify_poll = 0.0
    spotify_info = {"is_playing": False, "image_url": None, "name": None, "artist": None}
    last_status = None           # last status dict written (to skip no-op writes)
    last_status_write = 0.0

    photos = list_photos()        # sorted, for change detection
    last_photo_scan = time.time()
    last_photo_switch = 0.0
    last_photo_advance = None     # last-seen "next photo" nonce from the web UI

    # Photos are shown in a random order. play_order is a shuffled copy of
    # `photos`; when it's exhausted we reshuffle for a fresh random pass so
    # every photo is shown once per pass (no dupes until all have shown).
    play_order = []
    play_pos = 0
    last_shown_path = None

    def reshuffle():
        nonlocal play_order, play_pos
        play_order = photos[:]
        random.shuffle(play_order)
        # Avoid immediately repeating the photo that was just on screen.
        if len(play_order) > 1 and play_order[0] == last_shown_path:
            play_order.append(play_order.pop(0))
        play_pos = 0

    reshuffle()

    rendered_key = None          # what is currently on the panel (to avoid redundant redraws)
    current_image = None         # PIL image currently shown (for brightness re-apply)

    def save_preview(image):
        """Write a tiny PNG of the current panel for the web dashboard."""
        try:
            tmp = PREVIEW_PATH + ".tmp"
            (image if image is not None
             else Image.new("RGB", (matrix.width, matrix.height))).save(tmp)
            os.replace(tmp, PREVIEW_PATH)
        except Exception as e:
            log.debug("preview save failed: %s", e)

    def show(image, key):
        nonlocal rendered_key, current_image
        current_image = image
        matrix.SetImage(image)
        rendered_key = key
        save_preview(image)

    def blank():
        nonlocal rendered_key, current_image
        if rendered_key != "off":
            matrix.Clear()
            rendered_key = "off"
            current_image = None
            save_preview(None)   # black frame

    def show_default(state):
        """The logo splash. Which logo comes from the web panel's Logo card
        (state["logo"]); it is redrawn only when that choice changes."""
        path = logo_image_path(state, max(matrix.width, matrix.height),
                               LOGOS_DIR, default_image_path)
        if rendered_key == ("default", path):
            return
        try:
            img = fit(Image.open(path), matrix)
            show(img, ("default", path))
        except Exception as e:
            log.warning("default image failed: %s", e)
            blank()

    log.info("spotipi display started. photos=%d", len(photos))

    while True:
        try:
            now = time.time()
            state = read_state()

            # --- manual "next photo" request (nonce bumped by the web UI) ---
            adv = int(state.get("photo_advance", 0) or 0)
            if last_photo_advance is None:
                last_photo_advance = adv
            advance_pending = adv != last_photo_advance
            last_photo_advance = adv

            # --- live brightness (with sunrise/sunset dimmer applied) ---
            b = max(1, min(100, int(effective_brightness(state, datetime.now()))))
            if b != last_brightness:
                matrix.brightness = b
                last_brightness = b
                if current_image is not None:      # re-apply so brightness change is visible
                    matrix.SetImage(current_image)

            # --- poll Spotify occasionally ---
            if now - last_spotify_poll >= SPOTIFY_POLL_SECONDS:
                spotify_info = getSongInfo(username, token_path)
                last_spotify_poll = now

            # --- rescan photo folder occasionally ---
            if now - last_photo_scan >= PHOTO_RESCAN_SECONDS:
                new_photos = list_photos()
                if new_photos != photos:
                    photos = new_photos
                    reshuffle()           # new/removed photos -> fresh random pass
                    rendered_key = None   # force redraw in case current photo was deleted
                last_photo_scan = now

            # --- decide what to show ---
            effective = compute_effective(state, spotify_info["is_playing"],
                                          now_epoch=now)

            if effective == "off":
                blank()

            elif effective == "spotify":
                if spotify_info["is_playing"] and spotify_info["image_url"]:
                    key = ("spotify", spotify_info["image_url"], last_brightness)
                    if key != rendered_key:
                        resp = requests.get(spotify_info["image_url"], timeout=5)
                        img = fit(Image.open(BytesIO(resp.content)), matrix)
                        show(img, key)
                else:
                    show_default(state)

            elif effective == "photos":
                if not photos:
                    show_default(state)
                else:
                    interval = max(1, int(state.get("slideshow_seconds", 8)))
                    if advance_pending or rendered_key is None \
                            or now - last_photo_switch >= interval \
                            or not (isinstance(rendered_key, tuple) and rendered_key[0] == "photo"):
                        if play_pos >= len(play_order):
                            reshuffle()             # finished a pass -> reshuffle
                        path = play_order[play_pos]
                        try:
                            img = fit(Image.open(path), matrix)
                            show(img, ("photo", path))
                            last_shown_path = path
                        except Exception as e:
                            log.warning("photo %s failed: %s", path, e)
                        last_photo_switch = now
                        play_pos += 1

            # --- publish runtime status for the web dashboard ---
            if isinstance(rendered_key, tuple) and rendered_key[0] == "photo":
                showing, cur_photo = "photo", os.path.basename(rendered_key[1])
            elif isinstance(rendered_key, tuple) and rendered_key[0] == "spotify":
                showing, cur_photo = "spotify", None
            elif isinstance(rendered_key, tuple) and rendered_key[0] == "default":
                showing, cur_photo = "default", None
            else:
                showing, cur_photo = "off", None
            status = {
                "effective": effective,
                "showing": showing,
                "photo": cur_photo,
                "photo_count": len(photos),
                "is_playing": bool(spotify_info.get("is_playing")),
                "song": spotify_info.get("name"),
                "artist": spotify_info.get("artist"),
                "brightness": last_brightness,
            }
            if status != last_status or now - last_status_write >= STATUS_WRITE_SECONDS:
                write_status(status)
                last_status = status
                last_status_write = now

            time.sleep(LOOP_SLEEP)

        except KeyboardInterrupt:
            matrix.Clear()
            sys.exit(0)
        except Exception as e:
            log.warning("loop error: %s", e)
            time.sleep(1)


if __name__ == "__main__":
    main()
