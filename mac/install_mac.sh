#!/bin/bash
# install_mac.sh -- set up the Apple Photos -> Pi sync on your Mac.
set -e

echo "Installing Python dependencies (osxphotos, pillow, pillow-heif)..."
python3 -m pip install --upgrade osxphotos pillow pillow-heif

echo
echo "Next steps (manual):"
echo "  1. In Apple Photos, create an album named exactly 'Spotipi'"
echo "     (or pass a different name with --album) and add photos to it."
echo
echo "  2. Set up passwordless SSH to the Pi (needed for rsync):"
echo "       ssh-keygen -t ed25519        # if you don't already have a key"
echo "       ssh-copy-id pi@spotipi.local # authorise it on the Pi"
echo
echo "  3. Test a one-off sync (safe dry run first):"
echo "       python3 sync_album.py --dry-run"
echo "       python3 sync_album.py"
echo
echo "  4. Automate it every 5 minutes with launchd:"
echo "       - Edit com.spotipi.albumsync.plist: set the python3 path, the full"
echo "         path to sync_album.py, and your album/pi-host values."
echo "       cp com.spotipi.albumsync.plist ~/Library/LaunchAgents/"
echo "       launchctl load ~/Library/LaunchAgents/com.spotipi.albumsync.plist"
echo
echo "  Logs: /tmp/spotipi-albumsync.log  and  /tmp/spotipi-albumsync.err"
echo "Done."
