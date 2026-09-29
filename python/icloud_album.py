#!/usr/bin/env python3
"""
icloud_album.py -- mirror a public iCloud Shared Album onto the Pi.

This is the route for someone with an iPhone and no Mac. On the phone:
Photos -> new Shared Album -> Public Website ON -> copy the link. Paste that
link into the Spotipi control panel and the Pi polls it. Add a photo to the
album on the phone and it appears on the panel; remove one and it goes.

Nothing here needs an Apple ID, a password, or any credential: a shared album
with the public website enabled is served by iCloud to anyone holding the link,
and that is all we use. Treat the link as semi-secret -- anyone with it can see
the album.

    python3 icloud_album.py --url "https://www.icloud.com/sharedalbum/#B0abc..." --dry-run
    python3 icloud_album.py --url "..." --dest ../photos --size 64

[Unverified] Apple do not document this endpoint. The request/response shapes
below are what the public web viewer itself uses, and match several independent
implementations, but Apple can change them without notice. Everything is
defensive: on any unexpected shape the sync reports an error and leaves the
photos already on the Pi alone, so a broken album never blanks the panel.
"""
import argparse
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request

try:
    from PIL import Image, ImageOps
except ImportError:                                    # pragma: no cover
    Image = None

try:                                                   # iPhone HEIC, if present
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

PREFIX = "icloud-"          # filenames we own; anything else here is left alone
DEFAULT_PARTITION = "p23"
TIMEOUT = 30
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"


class AlbumError(RuntimeError):
    """Anything that stops us reading the album. Always safe to retry later."""


# --------------------------------------------------------------- the API ---
def parse_token(url):
    """Pull the album token out of a shared-album link.

    Accepts the forms Apple hands out:
        https://www.icloud.com/sharedalbum/#B0abc123
        https://www.icloud.com/sharedalbum/?#B0abc123
        B0abc123
    """
    url = (url or "").strip()
    if not url:
        raise AlbumError("No album link set.")
    if "#" in url:
        url = url.split("#", 1)[1]
    url = url.strip().strip("/")
    if not re.fullmatch(r"[A-Za-z0-9]{10,}", url):
        raise AlbumError(
            "That doesn't look like an iCloud shared-album link. It should look "
            "like https://www.icloud.com/sharedalbum/#B0Abc123...")
    return url


def _post(base, path, payload):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "User-Agent": UA},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, dict(r.headers), json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        # 330 is iCloud's "your album lives on another partition" response. It
        # is not really an error, so read the header and let the caller retry.
        headers = dict(e.headers or {})
        body = b""
        try:
            body = e.read()
        except Exception:
            pass
        if e.code == 330 or "X-Apple-MMe-Host" in headers:
            return e.code, headers, {}
        raise AlbumError(f"iCloud returned HTTP {e.code} for {path}.") from e
    except urllib.error.URLError as e:
        raise AlbumError(f"Could not reach iCloud: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise AlbumError("iCloud returned something that wasn't JSON.") from e


def _base_for(host, token):
    return f"https://{host}/{token}/sharedstreams"


def fetch_stream(token, partition=DEFAULT_PARTITION):
    """Return (base_url, photos list). Follows the partition redirect once."""
    base = _base_for(f"{partition}-sharedstreams.icloud.com", token)
    status, headers, data = _post(base, "/webstream", {"streamCtag": None})

    host = headers.get("X-Apple-MMe-Host") or headers.get("x-apple-mme-host")
    if host:
        base = _base_for(host, token)
        status, headers, data = _post(base, "/webstream", {"streamCtag": None})

    photos = data.get("photos")
    if photos is None:
        raise AlbumError(
            "iCloud didn't return any photos. Check the album's Public Website "
            "switch is still on, and that the link is the current one.")
    return base, photos


def asset_urls(base, guids):
    """checksum -> downloadable URL, for the given photo GUIDs."""
    out = {}
    # Apple gets unhappy with very large batches; 25 keeps us well inside.
    for i in range(0, len(guids), 25):
        _, _, data = _post(base, "/webasseturls", {"photoGuids": guids[i:i + 25]})
        for checksum, item in (data.get("items") or {}).items():
            loc, path = item.get("url_location"), item.get("url_path")
            if loc and path:
                out[checksum] = f"https://{loc}{path}"
    return out


def pick_derivative(photo, min_edge):
    """Smallest derivative whose shortest edge still covers the panel.

    The panel is 64 pixels. Downloading a 12-megapixel original to throw
    99.97% of it away would be absurd -- and on a Pi Zero-class board over
    home wi-fi, slow. Apple publish several sizes; take the smallest that is
    still big enough, and only fall back to the largest if none qualify.
    """
    derivatives = (photo.get("derivatives") or {})
    candidates = []
    for d in derivatives.values():
        try:
            w, h = int(d.get("width", 0)), int(d.get("height", 0))
            checksum = d["checksum"]
        except (KeyError, TypeError, ValueError):
            continue
        if w and h and checksum:
            candidates.append((min(w, h), int(d.get("fileSize", 0)), checksum))
    if not candidates:
        return None
    big_enough = [c for c in candidates if c[0] >= min_edge]
    chosen = min(big_enough or candidates, key=lambda c: (c[0], c[1]))
    return chosen[2]


# ------------------------------------------------------------- the sync ---
def _download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r, open(path, "wb") as f:
        f.write(r.read())


def _to_panel(src, dest, size):
    """Centre-crop to a square and resize, same as every other route in."""
    if Image is None:
        raise AlbumError("Pillow is not installed on this Pi.")
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im = ImageOps.fit(im, (size, size), Image.Resampling.LANCZOS)
        im.save(dest, "PNG")


def sync(url, dest, size=64, dry_run=False, log=print):
    """Mirror the album into `dest`. Returns a summary dict.

    Only files named icloud-*.png are considered ours: photos put there by the
    Mac sync or by hand are never touched.
    """
    token = parse_token(url)
    base, photos = fetch_stream(token)

    wanted = {}                              # guid -> checksum
    for p in photos:
        guid = p.get("photoGuid")
        if not guid:
            continue
        checksum = pick_derivative(p, size)
        if checksum:
            wanted[guid] = checksum

    os.makedirs(dest, exist_ok=True)
    have = {f[len(PREFIX):-4] for f in os.listdir(dest)
            if f.startswith(PREFIX) and f.endswith(".png")}

    missing = [g for g in wanted if g not in have]
    stale = sorted(have - set(wanted))

    if dry_run:
        log(f"Album has {len(wanted)} photo(s).")
        log(f"  would download {len(missing)}")
        log(f"  would remove   {len(stale)}")
        return {"total": len(wanted), "added": len(missing),
                "removed": len(stale), "dry_run": True}

    added = 0
    if missing:
        urls = asset_urls(base, missing)
        for guid in missing:
            u = urls.get(wanted[guid])
            if not u:
                log(f"  no URL for {guid[:8]} -- skipped")
                continue
            tmp = None
            try:
                fd, tmp = tempfile.mkstemp(suffix=".bin")
                os.close(fd)
                _download(u, tmp)
                _to_panel(tmp, os.path.join(dest, f"{PREFIX}{guid}.png"), size)
                added += 1
            except Exception as e:                    # one bad photo != failed sync
                log(f"  {guid[:8]} failed: {e}")
            finally:
                if tmp and os.path.exists(tmp):
                    os.remove(tmp)

    removed = 0
    for guid in stale:
        try:
            os.remove(os.path.join(dest, f"{PREFIX}{guid}.png"))
            removed += 1
        except OSError:
            pass

    log(f"Album: {len(wanted)} photo(s); +{added} new, -{removed} removed.")
    return {"total": len(wanted), "added": added, "removed": removed,
            "dry_run": False}


def main():
    ap = argparse.ArgumentParser(
        description="Mirror a public iCloud Shared Album to the panel's photos folder.")
    ap.add_argument("--url", required=True, help="The shared album link, or just its token.")
    ap.add_argument("--dest", default=os.path.join(os.path.dirname(__file__), "..", "photos"),
                    help="Photos folder (default: the project's photos/).")
    ap.add_argument("--size", type=int, default=64, choices=(32, 64),
                    help="Panel size; must match rgb_options.ini (default: 64).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Say what would change without downloading anything.")
    args = ap.parse_args()
    try:
        sync(args.url, os.path.abspath(args.dest), args.size, args.dry_run)
    except AlbumError as e:
        print(f"! {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
