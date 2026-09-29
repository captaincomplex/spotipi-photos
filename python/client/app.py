#!/usr/bin/env python3
"""
app.py -- spotipi web control panel.

Writes config/state.json, which the always-running display daemon reads every
loop. No systemd start/stop/restart is involved, so changes are instant and
the screen timer is reliable (the daemon is always alive to enforce it).

Runs on port 80.
"""

import os
import sys
import time

# Runs as root (binds port 80), so any __pycache__/*.pyc it writes end up
# root-owned and the non-root auto-updater can't overwrite/delete them.
sys.dont_write_bytecode = True

from flask import (Flask, render_template, request, redirect, url_for,
                   jsonify, send_file, Response)

# allow importing state.py from ../ (the python/ folder)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from state import (read_state, write_state, reset_timer,  # noqa: E402
                   read_status, read_icloud_status, PREVIEW_PATH, LOGOS)
import icloud_album                                       # noqa: E402

try:
    from PIL import Image, ImageOps
except ImportError:                                       # pragma: no cover
    Image = None

try:                       # iPhone photos are HEIC; Safari usually converts to
    import pillow_heif     # JPEG on upload, but not always, so accept both.
    pillow_heif.register_heif_opener()
except ImportError:
    pass

app = Flask(__name__)
app.config["CACHE_TYPE"] = "null"

VALID_MODES = {"on", "off", "photos", "spotify"}

# Phone uploads are whole camera-roll photos: several MB each, sometimes 20
# at a time. This is only a sanity ceiling -- everything is resized to 64px
# and thrown away within the second.
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024 * 1024
UPLOAD_PREFIX = "up-"
CONFIG_INI = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "config", "rgb_options.ini"))


def panel_size():
    """Panel edge in pixels, so uploads are cropped to what actually displays."""
    try:
        import configparser
        cfg = configparser.ConfigParser()
        cfg.read(CONFIG_INI)
        return max(int(cfg["DEFAULT"]["rows"]), int(cfg["DEFAULT"]["columns"]))
    except Exception:
        return 64


PHOTOS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "photos"))
IMG_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")


def photo_count():
    try:
        return sum(1 for f in os.listdir(PHOTOS_DIR) if f.lower().endswith(IMG_EXTS))
    except FileNotFoundError:
        return 0


def last_sync_epoch():
    """Newest photo mtime = roughly when the Mac last synced the album."""
    try:
        mtimes = [
            os.path.getmtime(os.path.join(PHOTOS_DIR, f))
            for f in os.listdir(PHOTOS_DIR) if f.lower().endswith(IMG_EXTS)
        ]
        return max(mtimes) if mtimes else None
    except (FileNotFoundError, OSError):
        return None


def pi_temp_c():
    """CPU temperature in °C (Raspberry Pi), or None off-Pi."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read().strip()) / 1000.0, 1)
    except (FileNotFoundError, ValueError, OSError):
        return None


def uptime_seconds():
    try:
        with open("/proc/uptime") as f:
            return int(float(f.read().split()[0]))
    except (FileNotFoundError, ValueError, OSError):
        return None


def dashboard():
    """Everything the live dashboard needs, in one place."""
    st = read_status()
    remaining = None
    s = read_state()
    if s.get("timer_enabled") and s.get("timer_started"):
        remaining = max(0, int(s["timer_minutes"] * 60 - (time.time() - s["timer_started"])))
    # daemon is "alive" if it refreshed status within ~3 heartbeats
    alive = bool(st) and st.get("age_s", 999) <= 30
    return {
        "status": st,
        "alive": alive,
        "photo_count": photo_count(),
        "last_sync_epoch": last_sync_epoch(),
        "pi_temp_c": pi_temp_c(),
        "uptime_s": uptime_seconds(),
        "timer_remaining_s": remaining,
        "icloud": read_icloud_status(),
    }


@app.route("/")
def index():
    return render_template("index.html", s=read_state(),
                           photo_count=photo_count(), dash=dashboard())


@app.route("/preview.png")
def preview():
    # The panel snapshot written by the display daemon. 1x1 black if absent.
    if os.path.exists(PREVIEW_PATH):
        resp = send_file(PREVIEW_PATH, mimetype="image/png")
        resp.headers["Cache-Control"] = "no-store"
        return resp
    px = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
          b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc```\x00\x00"
          b"\x00\x04\x00\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82")
    return Response(px, mimetype="image/png")


# ------------------------------------------------------------------ logo -----
# Files made by image/build_logo_assets.py, one folder per logo.
LOGO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "image", "logos"))


def chosen_logo():
    key = read_state().get("logo")
    return key if key in LOGOS else LOGOS[0]


def logo_file(key, name):
    """Send image/logos/<key>/<name>; key is always checked against LOGOS."""
    path = os.path.join(LOGO_DIR, key, name)
    if key not in LOGOS or not os.path.exists(path):
        return Response(status=404)
    resp = send_file(path)
    resp.headers["Cache-Control"] = "no-cache"   # the choice can change
    return resp


@app.route("/favicon.ico")
def favicon():
    return logo_file(chosen_logo(), "favicon.ico")


@app.route("/apple-touch-icon.png")
def touch_icon():
    # what iPhone uses for "Add to Home Screen"
    return logo_file(chosen_logo(), "icon-256.png")


@app.route("/logo/<key>.png")
def logo_preview(key):
    return logo_file(key, "icon-128.png")


@app.route("/logo/<key>/small.png")
def logo_small(key):
    # solid pixels: at header size the 16-dot version turns to mush
    return logo_file(key, "icon-64.png")


@app.route("/logo", methods=["POST"])
def set_logo():
    key = request.form.get("logo", LOGOS[0])
    state = read_state()
    state["logo"] = key if key in LOGOS else LOGOS[0]
    write_state(state)
    return redirect(url_for("index"))


@app.route("/mode", methods=["POST"])
def set_mode():
    mode = request.form.get("mode", "on")
    if mode not in VALID_MODES:
        mode = "on"
    state = read_state()
    state["mode"] = mode
    # any deliberate mode change restarts the sleep-timer countdown
    reset_timer(state)
    write_state(state)
    return redirect(url_for("index"))


@app.route("/brightness", methods=["POST"])
def set_brightness():
    try:
        val = int(request.form.get("brightness", 60))
    except ValueError:
        val = 60
    val = max(1, min(100, val))
    state = read_state()
    state["brightness"] = val
    write_state(state)
    # AJAX slider posts get a tiny JSON ack; normal form posts redirect.
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(ok=True, brightness=val)
    return redirect(url_for("index"))


@app.route("/next_photo", methods=["POST"])
def next_photo():
    # Bump a nonce; the display daemon notices and jumps to the next photo.
    state = read_state()
    state["photo_advance"] = int(state.get("photo_advance", 0) or 0) + 1
    write_state(state)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(ok=True, photo_advance=state["photo_advance"])
    return redirect(url_for("index"))


@app.route("/dimmer", methods=["POST"])
def set_dimmer():
    state = read_state()
    state["dimmer_enabled"] = request.form.get("dimmer_enabled") == "on"
    try:
        state["dim_brightness"] = max(1, min(100, int(request.form.get("dim_brightness", 20))))
    except ValueError:
        state["dim_brightness"] = 20
    try:
        state["latitude"] = max(-90.0, min(90.0, float(request.form.get("latitude", 51.5074))))
    except ValueError:
        pass
    try:
        state["longitude"] = max(-180.0, min(180.0, float(request.form.get("longitude", -0.1278))))
    except ValueError:
        pass
    write_state(state)
    return redirect(url_for("index"))


@app.route("/slideshow", methods=["POST"])
def set_slideshow():
    try:
        val = int(request.form.get("slideshow_seconds", 8))
    except ValueError:
        val = 8
    state = read_state()
    state["slideshow_seconds"] = max(1, min(600, val))
    write_state(state)
    return redirect(url_for("index"))


@app.route("/timer", methods=["POST"])
def set_timer():
    state = read_state()
    state["timer_enabled"] = request.form.get("timer_enabled") == "on"
    try:
        state["timer_minutes"] = max(1, min(1440, int(request.form.get("timer_minutes", 30))))
    except ValueError:
        state["timer_minutes"] = 30
    # (re)start the countdown from now whenever the timer settings are saved
    reset_timer(state)
    write_state(state)
    return redirect(url_for("index"))


@app.route("/schedule", methods=["POST"])
def set_schedule():
    state = read_state()
    state["schedule_enabled"] = request.form.get("schedule_enabled") == "on"
    state["schedule_off"] = request.form.get("schedule_off", "23:00")
    state["schedule_on"] = request.form.get("schedule_on", "07:00")
    write_state(state)
    return redirect(url_for("index"))


@app.route("/icloud", methods=["POST"])
def set_icloud():
    """Save the shared-album link and poll interval.

    The link is validated here so a typo gives an answer straight away, rather
    than sitting in state.json failing quietly every fifteen minutes.
    """
    state = read_state()
    url = (request.form.get("icloud_url") or "").strip()
    if url:
        try:
            icloud_album.parse_token(url)
        except icloud_album.AlbumError as e:
            return render_template("index.html", s=read_state(),
                                   photo_count=photo_count(), dash=dashboard(),
                                   error=str(e)), 400
    state["icloud_url"] = url
    try:
        state["icloud_minutes"] = max(1, min(1440, int(request.form.get("icloud_minutes", 15))))
    except (TypeError, ValueError):
        state["icloud_minutes"] = 15
    write_state(state)
    return redirect(url_for("index"))


@app.route("/icloud/sync", methods=["POST"])
def icloud_sync_now():
    """Bump a nonce; the sync daemon notices within its tick and runs at once."""
    state = read_state()
    state["icloud_sync_now"] = int(state.get("icloud_sync_now", 0)) + 1
    write_state(state)
    return redirect(url_for("index"))


@app.route("/upload", methods=["POST"])
def upload():
    """Add photos straight from the browser.

    This is what makes an iPhone self-sufficient: iOS Safari's file picker
    reaches the camera roll, so photos go phone -> panel with no computer in
    between. It works the same from any desktop browser.

    Cropping happens here rather than on the phone because the display daemon
    only ever scales down -- an uncropped 4:3 photo would sit letterboxed.
    """
    if Image is None:
        return render_template("index.html", s=read_state(),
                               photo_count=photo_count(), dash=dashboard(),
                               error="Pillow isn't installed on the Pi, so uploads "
                                     "can't be resized."), 500

    files = request.files.getlist("photos")
    size = panel_size()
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    saved, failed = 0, 0

    for f in files:
        if not f or not f.filename:
            continue
        try:
            with Image.open(f.stream) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                im = ImageOps.fit(im, (size, size), Image.Resampling.LANCZOS)
                # Name by content-independent counter + time: two photos from a
                # phone can share a filename ("IMG_0001.HEIC") across devices.
                name = f"{UPLOAD_PREFIX}{int(time.time() * 1000)}-{saved}.png"
                im.save(os.path.join(PHOTOS_DIR, name), "PNG")
            saved += 1
        except Exception:
            failed += 1

    msg = f"Added {saved} photo{'s' if saved != 1 else ''}."
    if failed:
        msg += f" {failed} could not be read (unsupported format?)."
    return render_template("index.html", s=read_state(),
                           photo_count=photo_count(), dash=dashboard(),
                           notice=msg)


@app.route("/photos/delete", methods=["POST"])
def delete_uploads():
    """Remove photos added through the browser.

    Deliberately only touches up-* files. Photos mirrored from a Mac album or
    an iCloud album are owned by their sync, which would put them straight
    back -- deleting those belongs in the album, on the phone.
    """
    removed = 0
    try:
        for f in os.listdir(PHOTOS_DIR):
            if f.startswith(UPLOAD_PREFIX):
                try:
                    os.remove(os.path.join(PHOTOS_DIR, f))
                    removed += 1
                except OSError:
                    pass
    except FileNotFoundError:
        pass
    return render_template("index.html", s=read_state(),
                           photo_count=photo_count(), dash=dashboard(),
                           notice=f"Removed {removed} uploaded photo(s).")


# Live status endpoint the dashboard polls (also handy for debugging).
@app.route("/status")
def status():
    d = dashboard()
    d["state"] = read_state()
    return jsonify(d)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
