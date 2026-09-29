#!/usr/bin/env python3
"""
icloudSync.py -- background daemon that keeps a public iCloud Shared Album
mirrored into photos/.

Follows the same design rule as the rest of this project: the web UI only ever
writes config/state.json, and daemons read it. So the album link and the poll
interval are set from the control panel, and this process picks them up on its
next tick with nothing to restart.

    python3 icloudSync.py           # run forever (this is what systemd starts)
    python3 icloudSync.py --once    # one pass, then exit -- handy for testing
"""
import argparse
import configparser
import os
import sys
import time
import logging

sys.dont_write_bytecode = True

from state import read_state, write_icloud_status          # noqa: E402
import icloud_album                                        # noqa: E402

DIR = os.path.dirname(os.path.abspath(__file__))
PHOTOS_DIR = os.path.abspath(os.path.join(DIR, "..", "photos"))
CONFIG_PATH = os.path.abspath(os.path.join(DIR, "..", "config", "rgb_options.ini"))

TICK = 20.0                    # how often to look at state.json
MIN_MINUTES = 1

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
log = logging.getLogger("spotipi-icloud")


def panel_size():
    """Match the panel: a 32x32 shouldn't be fed 64px images."""
    try:
        cfg = configparser.ConfigParser()
        cfg.read(CONFIG_PATH)
        return max(int(cfg["DEFAULT"]["rows"]), int(cfg["DEFAULT"]["columns"]))
    except Exception:
        return 64


def run_once(url, size):
    """One sync. Never raises: the result goes into icloud_status.json."""
    started = time.time()
    try:
        result = icloud_album.sync(url, PHOTOS_DIR, size=size, log=log.info)
        write_icloud_status({
            "ok": True, "at": int(started), "error": None,
            "total": result["total"], "added": result["added"],
            "removed": result["removed"],
        })
        return True
    except icloud_album.AlbumError as e:
        log.warning("sync failed: %s", e)
        write_icloud_status({"ok": False, "at": int(started), "error": str(e)})
    except Exception as e:                       # never let the daemon die
        log.exception("unexpected sync error")
        write_icloud_status({"ok": False, "at": int(started),
                             "error": f"Unexpected: {e}"})
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="Sync once and exit.")
    args = ap.parse_args()

    last_sync = 0.0
    last_url = None
    last_nonce = None
    idle_logged = False

    while True:
        state = read_state()
        url = (state.get("icloud_url") or "").strip()
        minutes = max(MIN_MINUTES, int(state.get("icloud_minutes") or 15))
        nonce = state.get("icloud_sync_now", 0)

        if not url:
            if not idle_logged:
                log.info("No album link set; idle. Set one in the control panel.")
                idle_logged = True
            if args.once:
                return 0
            time.sleep(TICK)
            continue
        idle_logged = False

        now = time.time()
        due = (now - last_sync) >= minutes * 60
        changed = url != last_url                    # new link: sync immediately
        asked = last_nonce is not None and nonce != last_nonce

        if last_nonce is None:
            last_nonce = nonce

        if due or changed or asked or args.once:
            if changed:
                log.info("Album link changed -- syncing now.")
            if asked:
                log.info("Sync requested from the control panel.")
            run_once(url, panel_size())
            last_sync = time.time()
            last_url = url
            last_nonce = nonce

        if args.once:
            return 0
        time.sleep(TICK)


if __name__ == "__main__":
    sys.exit(main())
