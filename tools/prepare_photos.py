#!/usr/bin/env python3
"""
prepare_photos.py -- get a folder of pictures ready for the panel, on any OS.

The Apple Photos sync (mac/sync_album.py) is the automatic route, but it needs
a Mac. This is the manual route, and it works on Windows, macOS and Linux: give
it a folder of photos and it centre-crops and resizes each one to the panel's
size, writing them to an output folder you then copy to the Pi.

Why this exists rather than "just copy your photos across": the display daemon
scales images down but never crops them, so a 4000x3000 holiday photo arrives
as 64x48 and sits in a letterboxed band with dead pixels above and below. This
crops to a square first, so it fills the panel.

    python3 prepare_photos.py ~/Pictures/forpanel
    python3 prepare_photos.py C:\\Users\\me\\Pictures\\forpanel --size 32
    python3 prepare_photos.py ~/Pictures/forpanel --push pi@spotipi.local

Needs Pillow:   python3 -m pip install pillow
HEIC support (iPhone photos) also needs:   python3 -m pip install pillow-heif
"""
import argparse
import os
import shutil
import subprocess
import sys

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is not installed.  Run:  python3 -m pip install pillow")

try:                                  # optional: lets us read iPhone .HEIC files
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIC = True
except ImportError:
    HEIC = False

EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
if HEIC:
    EXTS |= {".heic", ".heif"}


def main():
    ap = argparse.ArgumentParser(
        description="Crop and resize photos to square for a Spotipi LED panel.")
    ap.add_argument("source", help="Folder of photos to prepare.")
    ap.add_argument("-o", "--out", default=None,
                    help="Output folder (default: <source>/panel-ready).")
    ap.add_argument("--size", type=int, default=64, choices=(32, 64),
                    help="Panel size in pixels. Must match rows/columns in "
                         "config/rgb_options.ini (default: 64).")
    ap.add_argument("--push", metavar="USER@HOST",
                    help="After preparing, copy to the Pi over SSH, e.g. "
                         "pi@spotipi.local")
    ap.add_argument("--pi-dir", default="/home/pi/spotipi-photos/photos",
                    help="Destination folder on the Pi (used with --push).")
    ap.add_argument("--clean", action="store_true",
                    help="Empty the output folder first.")
    args = ap.parse_args()

    src = os.path.abspath(os.path.expanduser(args.source))
    if not os.path.isdir(src):
        sys.exit(f"Not a folder: {src}")

    out = os.path.abspath(os.path.expanduser(args.out)) if args.out \
        else os.path.join(src, "panel-ready")
    if args.clean and os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)

    names = sorted(f for f in os.listdir(src)
                   if os.path.splitext(f)[1].lower() in EXTS)
    if not names:
        extra = "" if HEIC else \
            "\n(iPhone .HEIC files are skipped -- pip install pillow-heif to include them.)"
        sys.exit(f"No images found in {src}{extra}")

    done = 0
    for n in names:
        try:
            with Image.open(os.path.join(src, n)) as im:
                im = ImageOps.exif_transpose(im)        # honour phone rotation
                im = im.convert("RGB")
                # centre-crop to square, then resize -- same as the Mac sync does
                im = ImageOps.fit(im, (args.size, args.size), Image.Resampling.LANCZOS)
                im.save(os.path.join(out, os.path.splitext(n)[0] + ".png"), "PNG")
            done += 1
        except Exception as e:                          # one bad file shouldn't stop the run
            print(f"  skipped {n}: {e}")

    print(f"Prepared {done} of {len(names)} images at {args.size}x{args.size} -> {out}")

    if not args.push:
        print()
        print("Now copy them to the Pi. From this computer:")
        print(f'  scp "{out}"/*.png pi@spotipi.local:{args.pi_dir}/')
        print()
        print("On Windows, scp ships with Windows 10 and 11 -- run that in")
        print("PowerShell. WinSCP works too if you prefer a window to drag into.")
        return 0

    dest = f"{args.push}:{args.pi_dir}/"
    if shutil.which("rsync"):
        cmd = ["rsync", "-av", "--delete", out + os.sep, dest]
        print(f"\nMirroring with rsync (removes photos on the Pi that aren't here):\n  {' '.join(cmd)}")
    else:
        cmd = ["scp"] + [os.path.join(out, f) for f in os.listdir(out)] + [dest]
        print(f"\nCopying with scp ({len(cmd) - 2} files). Note: scp adds and "
              f"overwrites, but won't remove photos already on the Pi.")
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        sys.exit("Neither rsync nor scp was found on this computer.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"Copy failed ({e.returncode}). Check you can 'ssh {args.push}' first.")
    print("Done. The panel picks up new photos within about ten seconds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
