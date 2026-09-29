"""
state.py -- shared, atomic read/write of the live display state.

Both the display daemon and the web app read and write config/state.json.
The daemon polls it every loop, so changes from the web UI take effect
immediately with no service restart.
"""

import json
import os
import tempfile
import time

DIR = os.path.dirname(__file__)
STATE_PATH = os.path.abspath(os.path.join(DIR, "..", "config", "state.json"))

# Runtime status: written by the display daemon, read by the web dashboard.
# Separate from state.json (which is user config) so the two never clash.
STATUS_PATH = os.path.abspath(os.path.join(DIR, "..", "config", "status.json"))
# A tiny PNG of what is currently on the panel (also written by the daemon).
PREVIEW_PATH = os.path.abspath(os.path.join(DIR, "..", "config", "current.png"))

DEFAULT_STATE = {
    # mode: "on" (auto: Spotify when playing, else photos),
    #       "off", "photos" (photos only), "spotify" (Spotify only)
    "mode": "on",
    "brightness": 60,               # 1-100, applied live (this is the daytime level)
    "slideshow_seconds": 8,         # seconds per photo

    # Manual "next photo" nonce. The web UI bumps this; the display daemon
    # notices the change and jumps to the next photo immediately.
    "photo_advance": 0,

    # Sunrise/sunset dimmer: when enabled, the display drops to
    # dim_brightness between sunset and sunrise (computed from lat/lon),
    # and uses the normal "brightness" level during the day.
    "dimmer_enabled": False,
    "dim_brightness": 20,           # 1-100, night level
    "latitude": 51.5074,            # default: London; set to your location
    "longitude": -0.1278,

    # Sleep timer: when enabled, the display turns OFF this many minutes
    # after timer_started. Toggling a mode button resets timer_started.
    "timer_enabled": False,
    "timer_minutes": 30,
    "timer_started": 0,             # epoch seconds; 0 = not started

    # Optional recurring daily "quiet hours" -- display off in this window.
    "schedule_enabled": False,
    "schedule_off": "23:00",        # HH:MM 24h
    "schedule_on": "07:00",

    # iCloud Shared Album sync (the iPhone-only route in). The album's public
    # link, polled by the spotipi-icloud daemon. Empty = feature off.
    "icloud_url": "",
    "icloud_minutes": 15,           # how often to poll
    "icloud_sync_now": 0,           # nonce: bump from the web UI to sync at once

    # Which logo the panel shows when there is nothing else to show, and the
    # web panel uses as its icon. Files: config/logos/<logo>-64.png / -32.png.
    "logo": "sunset",
}

# The logos on offer (image/build_logo_assets.py makes them). First = default.
#   sunset -- orange sunset, the sun setting behind the ridges
#   dusk   -- pink dusk, the whole sun just clear of the ridges
LOGOS = ("sunset", "dusk")


def read_state():
    """Return the current state dict, filling in any missing defaults."""
    try:
        with open(STATE_PATH, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError):
        data = {}
    merged = dict(DEFAULT_STATE)
    merged.update(data or {})
    return merged


def write_state(state):
    """Atomically write the full state dict."""
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(STATE_PATH), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, STATE_PATH)   # atomic on POSIX
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def update_state(**changes):
    """Read, apply changes, write. Returns the new state."""
    state = read_state()
    state.update(changes)
    write_state(state)
    return state


def reset_timer(state):
    """Mark the sleep timer as starting now."""
    state["timer_started"] = int(time.time())
    return state


# Written by the iCloud daemon, read by the web dashboard. Kept apart from
# status.json so the display daemon and the sync daemon never fight over a file.
ICLOUD_STATUS_PATH = os.path.abspath(
    os.path.join(DIR, "..", "config", "icloud_status.json"))


def write_icloud_status(status):
    """Atomically write the iCloud sync daemon's last-run status."""
    os.makedirs(os.path.dirname(ICLOUD_STATUS_PATH), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(ICLOUD_STATUS_PATH), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(status, f)
        os.replace(tmp, ICLOUD_STATUS_PATH)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def read_icloud_status():
    """Last iCloud sync result, or {} if it has never run."""
    try:
        with open(ICLOUD_STATUS_PATH, "r") as f:
            return json.load(f) or {}
    except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError):
        return {}


def write_status(status):
    """Atomically write the daemon's runtime status dict (config/status.json)."""
    os.makedirs(os.path.dirname(STATUS_PATH), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(STATUS_PATH), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(status, f)
        os.replace(tmp, STATUS_PATH)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def read_status():
    """Return the daemon's runtime status dict, or {} if unavailable.

    Adds "age_s" = seconds since the file was last written, so the dashboard
    can tell whether the display daemon is alive.
    """
    try:
        with open(STATUS_PATH, "r") as f:
            data = json.load(f) or {}
        data["age_s"] = max(0, int(time.time() - os.path.getmtime(STATUS_PATH)))
        return data
    except (FileNotFoundError, json.JSONDecodeError, PermissionError, OSError):
        return {}
