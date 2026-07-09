"""
Unit tests for the pure display-decision logic (no hardware needed).
Run from the repo root:  python3 -m pytest tests/  -q
or:                      python3 tests/test_logic.py
"""

import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))

from display_logic import (   # noqa: E402
    parse_hhmm, in_quiet_hours, timer_expired, compute_effective,
    sun_times, is_night, effective_brightness,
)


def base(**over):
    s = {
        "mode": "on", "brightness": 60, "slideshow_seconds": 8,
        "timer_enabled": False, "timer_minutes": 30, "timer_started": 0,
        "schedule_enabled": False, "schedule_off": "23:00", "schedule_on": "07:00",
        "dimmer_enabled": False, "dim_brightness": 20,
        "latitude": 51.5074, "longitude": -0.1278,
    }
    s.update(over)
    return s


def test_parse_hhmm():
    assert parse_hhmm("23:00") == (23, 0)
    assert parse_hhmm("07:30") == (7, 30)
    assert parse_hhmm("bad") is None
    assert parse_hhmm("25:00") is None


def test_quiet_hours_crossing_midnight():
    # window 23:00 -> 07:00
    assert in_quiet_hours(datetime(2026, 1, 1, 23, 30), "23:00", "07:00") is True
    assert in_quiet_hours(datetime(2026, 1, 1, 2, 0), "23:00", "07:00") is True
    assert in_quiet_hours(datetime(2026, 1, 1, 12, 0), "23:00", "07:00") is False
    assert in_quiet_hours(datetime(2026, 1, 1, 7, 0), "23:00", "07:00") is False  # boundary = on


def test_quiet_hours_same_day():
    assert in_quiet_hours(datetime(2026, 1, 1, 3, 0), "01:00", "06:00") is True
    assert in_quiet_hours(datetime(2026, 1, 1, 8, 0), "01:00", "06:00") is False


def test_timer():
    now = time.time()
    assert timer_expired(base(timer_enabled=False), now) is False
    # started 40 min ago, limit 30 -> expired
    assert timer_expired(base(timer_enabled=True, timer_minutes=30,
                              timer_started=now - 40 * 60), now) is True
    # started 10 min ago, limit 30 -> not yet
    assert timer_expired(base(timer_enabled=True, timer_minutes=30,
                              timer_started=now - 10 * 60), now) is False
    # enabled but never started
    assert timer_expired(base(timer_enabled=True, timer_started=0), now) is False


def test_compute_effective_modes():
    midday = datetime(2026, 1, 1, 12, 0)
    assert compute_effective(base(mode="off"), False, midday) == "off"
    assert compute_effective(base(mode="photos"), True, midday) == "photos"
    assert compute_effective(base(mode="spotify"), False, midday) == "spotify"
    # auto: depends on playback
    assert compute_effective(base(mode="on"), True, midday) == "spotify"
    assert compute_effective(base(mode="on"), False, midday) == "photos"


def test_compute_effective_off_precedence():
    midnight = datetime(2026, 1, 1, 23, 30)
    now = time.time()
    # schedule forces off even while playing
    s = base(mode="on", schedule_enabled=True)
    assert compute_effective(s, True, midnight, now) == "off"
    # expired timer forces off
    s = base(mode="photos", timer_enabled=True, timer_minutes=10,
             timer_started=now - 20 * 60)
    assert compute_effective(s, False, datetime(2026, 1, 1, 12, 0), now) == "off"


def test_sun_times_london_solstice():
    # London, summer solstice 2026. Expect a very early sunrise (~04-05 local)
    # and a late sunset (~20-21 local). We assert ordering and a plausible
    # long daylight window rather than exact minutes (tz-dependent).
    rise, set_ = sun_times(datetime(2026, 6, 21), 51.5074, -0.1278)
    assert rise is not None and set_ is not None
    assert rise < set_
    daylight_h = (set_ - rise).total_seconds() / 3600.0
    assert 14 < daylight_h < 18   # long summer day


def test_sun_times_polar_night():
    # High Arctic in deep winter: sun never rises -> no crossings.
    rise, set_ = sun_times(datetime(2026, 12, 21), 80.0, 0.0)
    assert rise is None and set_ is None


def test_sun_times_bad_coords():
    assert sun_times(datetime(2026, 1, 1), "abc", 0) == (None, None)


def test_is_night_disabled():
    # Dimmer off -> never "night" regardless of clock.
    assert is_night(base(dimmer_enabled=False), datetime(2026, 1, 1, 3, 0)) is False


def test_effective_brightness_day_vs_night():
    s = base(dimmer_enabled=True, brightness=60, dim_brightness=15)
    # Midday London -> day level.
    assert effective_brightness(s, datetime(2026, 6, 21, 12, 0)) == 60
    # Middle of the night -> dim level.
    assert effective_brightness(s, datetime(2026, 6, 21, 1, 0)) == 15
    # Dimmer off -> always day level.
    assert effective_brightness(base(dimmer_enabled=False, brightness=60),
                                datetime(2026, 6, 21, 1, 0)) == 60


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\nAll {len(fns)} test groups passed.")
