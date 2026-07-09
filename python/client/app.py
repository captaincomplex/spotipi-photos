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
                   read_status, PREVIEW_PATH)

app = Flask(__name__)
app.config["CACHE_TYPE"] = "null"

VALID_MODES = {"on", "off", "photos", "spotify"}


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


# Live status endpoint the dashboard polls (also handy for debugging).
@app.route("/status")
def status():
    d = dashboard()
    d["state"] = read_state()
    return jsonify(d)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
