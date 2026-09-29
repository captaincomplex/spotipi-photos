#!/usr/bin/env python3
"""
sync_album.py  --  Apple Photos -> Raspberry Pi (spotipi) album sync.

Reads a named album from the local Apple Photos library, converts each photo
to a 64x64 PNG suitable for an LED matrix, and mirrors the result to the Pi
with `rsync --delete`. Because of --delete, any photo removed from the album
is automatically removed from the Pi on the next run.

Runs on your Mac (where Apple Photos lives). Schedule it with launchd
(see com.spotipi.albumsync.plist) or run it by hand.

Requirements (installed by install_mac.sh):
    pip3 install osxphotos pillow pillow-heif
    rsync + ssh (built into macOS)
    An SSH key authorised on the Pi (ssh-copy-id pi@<pi-ip>)
"""

import argparse
import os
import subprocess
import sys
import tempfile
import shutil

try:
    import osxphotos
except ImportError:
    sys.exit("Missing dependency: osxphotos. Run: pip3 install osxphotos")

from PIL import Image, ImageOps

# Register HEIC/HEIF support so iPhone photos open directly.
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass


def build_matrix_png(src_path: str, dst_path: str, size: int) -> bool:
    """Load src image, EXIF-orient, centre-crop to square, resize to size x size,
    save as PNG. Returns True on success."""
    try:
        with Image.open(src_path) as im:
            im = ImageOps.exif_transpose(im)          # honour rotation
            im = im.convert("RGB")
            im = ImageOps.fit(im, (size, size), Image.Resampling.LANCZOS)  # centre-crop + resize
            im.save(dst_path, "PNG")
        return True
    except Exception as e:
        print(f"  ! skip {os.path.basename(src_path)}: {e}")
        return False


def main():
    ap = argparse.ArgumentParser(description="Sync an Apple Photos album to spotipi on a Raspberry Pi.")
    ap.add_argument("--album", default="Spotipi",
                    help="Name of the Apple Photos album to sync (default: 'Spotipi').")
    ap.add_argument("--pi-host", default="pi@spotipi.local",
                    help="user@host for the Pi (default: pi@spotipi.local). "
                         "Use the Pi's IP address instead if .local won't resolve.")
    ap.add_argument("--pi-dir", default="/home/pi/spotipi-photos/photos",
                    help="Destination photos folder on the Pi.")
    ap.add_argument("--size", type=int, default=64,
                    help="Matrix size in pixels: 64 for a 64x64 panel, 32 for a "
                         "32x32 one. Must match rows/columns in rgb_options.ini "
                         "(default: 64).")
    ap.add_argument("--ssh-port", default="22", help="SSH port on the Pi (default: 22).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Build images but show the rsync command instead of running it.")
    args = ap.parse_args()

    print(f"Reading Apple Photos album: {args.album!r}")
    db = osxphotos.PhotosDB()
    photos = [p for p in db.photos(albums=[args.album]) if p.isphoto]

    if not photos:
        print(f"No photos found in album {args.album!r}. "
              f"(Nothing will be sent; on the Pi the folder will be emptied by --delete.)")

    # Build a fresh staging directory that is an exact mirror of the album.
    staging = tempfile.mkdtemp(prefix="spotipi_album_")
    built = 0
    try:
        for p in photos:
            # prefer the edited version if one exists, else the original
            src = p.path_edited if (p.hasadjustments and p.path_edited) else p.path
            if not src or not os.path.exists(src):
                # original may be in iCloud and not downloaded locally
                print(f"  ! not local (download it in Photos first): {p.original_filename}")
                continue
            dst = os.path.join(staging, f"{p.uuid}.png")
            if build_matrix_png(src, dst, args.size):
                built += 1

        print(f"Built {built} image(s) at {args.size}x{args.size}.")

        # Mirror staging -> Pi. Trailing slashes matter: contents of staging
        # are mirrored into pi-dir, and --delete removes anything not in staging.
        rsync_cmd = [
            "rsync", "-av", "--delete",
            "-e", f"ssh -p {args.ssh_port}",
            staging + "/",
            f"{args.pi_host}:{args.pi_dir}/",
        ]

        if args.dry_run:
            print("DRY RUN -- would run:")
            print("  " + " ".join(rsync_cmd))
        else:
            # Make sure the destination exists on the Pi first.
            subprocess.run(
                ["ssh", "-p", args.ssh_port, args.pi_host, f"mkdir -p {args.pi_dir}"],
                check=True,
            )
            result = subprocess.run(rsync_cmd)
            if result.returncode != 0:
                sys.exit(f"rsync failed with code {result.returncode}")
            print("Sync complete.")
    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    main()
