"""
Tests for the logo choice: which splash the daemon shows, and the web panel's
Logo card. Run from the repo root:  python3 -m pytest tests/ -q
"""
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "python"))
sys.path.insert(0, os.path.join(ROOT, "python", "client"))

import state                                   # noqa: E402
from display_logic import logo_image_path       # noqa: E402

LOGOS_DIR = os.path.join(ROOT, "config", "logos")
FALLBACK = os.path.join(ROOT, "config", "default.png")


def pick(logo, px=64):
    return os.path.basename(logo_image_path({"logo": logo}, px, LOGOS_DIR, FALLBACK))


def test_default_is_sunset():
    assert state.DEFAULT_STATE["logo"] == "sunset" == state.LOGOS[0]
    assert pick(None) == "sunset-64.png"


def test_dusk_and_panel_size():
    assert pick("dusk") == "dusk-64.png"
    assert pick("dusk", 32) == "dusk-32.png"
    assert pick("sunset", 32) == "sunset-32.png"


def test_bad_names_never_reach_the_filesystem():
    for bad in ("../../etc/passwd", "", "Sunset", 7):
        assert pick(bad) == "sunset-64.png"


def test_missing_file_falls_back():
    with tempfile.TemporaryDirectory() as empty:
        assert logo_image_path({"logo": "dusk"}, 64, empty, FALLBACK) == FALLBACK


def test_every_logo_has_its_files():
    for key in state.LOGOS:
        for n in (64, 32):
            assert os.path.exists(os.path.join(LOGOS_DIR, f"{key}-{n}.png"))
        for f in ("favicon.ico", "icon-128.png", "icon-256.png"):
            assert os.path.exists(os.path.join(ROOT, "image", "logos", key, f))


def test_web_logo_card(monkeypatch, tmp_path):
    monkeypatch.setattr(state, "STATE_PATH", str(tmp_path / "state.json"))
    import app as webapp
    monkeypatch.setattr(webapp, "read_state", state.read_state)
    monkeypatch.setattr(webapp, "write_state", state.write_state)
    c = webapp.app.test_client()
    page = c.get("/").get_data(as_text=True)
    assert 'value="sunset"' in page and 'value="dusk"' in page
    assert c.post("/logo", data={"logo": "dusk"}).status_code == 302
    assert state.read_state()["logo"] == "dusk"
    c.post("/logo", data={"logo": "../../x"})
    assert state.read_state()["logo"] == "sunset"
    assert c.get("/favicon.ico").status_code == 200
    assert c.get("/logo/dusk.png").status_code == 200
    assert c.get("/logo/nope.png").status_code == 404
    assert c.get("/apple-touch-icon.png").status_code == 200
    assert c.get("/logo/sunset/small.png").status_code == 200
