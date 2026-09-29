"""
display_logic.py -- pure decision logic for what the matrix should show.

Kept free of any hardware imports so it can be unit-tested on any machine
(see tests/test_logic.py).
"""

import math
import os
import time
from datetime import datetime, timezone

from state import LOGOS


def parse_hhmm(s):
    """'23:00' -> (23, 0). Returns None on bad input."""
    try:
        h, m = s.split(":")
        h, m = int(h), int(m)
        if 0 <= h < 24 and 0 <= m < 60:
            return h, m
    except Exception:
        pass
    return None


def in_quiet_hours(now, off_str, on_str):
    """True if `now` (a datetime) falls within the off..on window.
    Handles windows that cross midnight (e.g. 23:00 -> 07:00)."""
    off = parse_hhmm(off_str)
    on = parse_hhmm(on_str)
    if not off or not on or off == on:
        return False
    minutes = now.hour * 60 + now.minute
    off_m = off[0] * 60 + off[1]
    on_m = on[0] * 60 + on[1]
    if off_m < on_m:
        # same-day window, e.g. 01:00 -> 06:00
        return off_m <= minutes < on_m
    # crosses midnight, e.g. 23:00 -> 07:00
    return minutes >= off_m or minutes < on_m


def timer_expired(state, now_epoch=None):
    """True if the sleep timer is enabled and has elapsed."""
    if not state.get("timer_enabled"):
        return False
    started = state.get("timer_started", 0) or 0
    if started <= 0:
        return False
    if now_epoch is None:
        now_epoch = time.time()
    minutes = max(0, int(state.get("timer_minutes", 30)))
    return (now_epoch - started) >= minutes * 60


def sun_times(date, lat, lon):
    """Sunrise and sunset for a given calendar date and location.

    Pure, dependency-free implementation of the standard sunrise equation
    (https://en.wikipedia.org/wiki/Sunrise_equation).

    `date` is a datetime (only its Y/M/D are used). `lat`/`lon` are decimal
    degrees (north/east positive). Returns (sunrise, sunset) as naive local
    datetimes, or (None, None) for polar day/night where the sun never
    crosses the horizon on that date.
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return None, None
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return None, None

    # Julian day for the date at 00:00 UTC.
    y, m, d = date.year, date.month, date.day
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    jd = (math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1))
          + d + b - 1524.5)

    # Integer day count since J2000 (jd is at 00:00 UT, so round to the
    # nearest whole day = that date's mean solar noon).
    n = round(jd - 2451545.0 + 0.0008)
    j_star = n - lon / 360.0             # mean solar time
    M = (357.5291 + 0.98560028 * j_star) % 360.0            # solar mean anomaly
    Mr = math.radians(M)
    C = (1.9148 * math.sin(Mr) + 0.0200 * math.sin(2 * Mr)
         + 0.0003 * math.sin(3 * Mr))                       # equation of center
    lam = math.radians((M + C + 180.0 + 102.9372) % 360.0)  # ecliptic longitude
    j_transit = (2451545.0 + j_star + 0.0053 * math.sin(Mr)
                 - 0.0069 * math.sin(2 * lam))               # solar noon (Julian)

    decl = math.asin(math.sin(lam) * math.sin(math.radians(23.44)))
    phi = math.radians(lat)
    cos_omega = ((math.sin(math.radians(-0.833)) - math.sin(phi) * math.sin(decl))
                 / (math.cos(phi) * math.cos(decl)))
    if cos_omega < -1 or cos_omega > 1:
        return None, None                # sun never rises or never sets today
    omega = math.degrees(math.acos(cos_omega))

    j_rise = j_transit - omega / 360.0
    j_set = j_transit + omega / 360.0

    def _to_local(j):
        epoch = (j - 2440587.5) * 86400.0            # Julian date -> unix epoch (UTC)
        return datetime.fromtimestamp(epoch)         # convert to local tz

    return _to_local(j_rise), _to_local(j_set)


def is_night(state, now=None):
    """True if the sunrise/sunset dimmer is on and it is currently night."""
    if not state.get("dimmer_enabled"):
        return False
    if now is None:
        now = datetime.now()
    rise, set_ = sun_times(now, state.get("latitude"), state.get("longitude"))
    if rise is None or set_ is None:
        # Polar day/night (or bad coords): treat "sun up all day" as day,
        # "sun down all day" as night, by checking the sun's declination
        # against latitude is overkill -- default to day (no dimming).
        return False
    return now < rise or now >= set_


def effective_brightness(state, now=None):
    """Brightness the daemon should apply right now (1-100).

    Normally the configured `brightness`; drops to `dim_brightness` at night
    when the sunrise/sunset dimmer is enabled.
    """
    day = int(state.get("brightness", 60))
    if is_night(state, now):
        night = int(state.get("dim_brightness", 20))
        return max(1, min(100, night))
    return max(1, min(100, day))


def compute_effective(state, is_playing, now=None, now_epoch=None):
    """Return what to render: 'off', 'spotify', or 'photos'.

    Precedence:
      1. mode == 'off'           -> off
      2. quiet-hours schedule    -> off
      3. expired sleep timer     -> off
      4. mode == 'spotify'       -> spotify
      5. mode == 'photos'        -> photos
      6. mode == 'on' (auto)     -> spotify if playing else photos
    """
    if now is None:
        now = datetime.now()

    mode = state.get("mode", "on")

    if mode == "off":
        return "off"
    if state.get("schedule_enabled") and in_quiet_hours(
        now, state.get("schedule_off", "23:00"), state.get("schedule_on", "07:00")
    ):
        return "off"
    if timer_expired(state, now_epoch):
        return "off"

    if mode == "spotify":
        return "spotify"
    if mode == "photos":
        return "photos"
    # auto
    return "spotify" if is_playing else "photos"


def logo_image_path(state, panel_px, logos_dir, fallback, logos=LOGOS):
    """The splash to show: <logos_dir>/<logo>-<64|32>.png for the logo picked
    in the web panel, drawn one pixel per LED at the panel's own size.

    An unknown logo name means the first one -- a path is never built from an
    unchecked value. Falls back to `fallback` (the ini's default_image) if the
    file isn't there, e.g. on an install that predates the logo files.
    """
    key = state.get("logo")
    if key not in logos:
        key = logos[0]
    size = 32 if panel_px <= 32 else 64
    path = os.path.join(logos_dir, "%s-%d.png" % (key, size))
    return path if os.path.exists(path) else fallback
