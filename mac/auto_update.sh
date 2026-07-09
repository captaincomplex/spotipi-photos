#!/bin/bash
# auto_update.sh -- keep the Pi's spotipi code in step with the newest release
# zip in Dropbox/AI projects/Spotipi Photos. Runs on the Mac via launchd.
#
# Updates ONLY code (python/ on the Pi, plus the Mac working copy). Never
# touches the Pi's live config, photos, or token. Health-checks the display
# service after pushing and ROLLS BACK if it fails to come up.
set -u

RELEASES="/Users/you/Dropbox/AI projects/Spotipi Photos"
LATEST="$RELEASES/spotipi-photos-latest.zip"
MAC_WORK="$RELEASES/spotipi-photos"
STATE="$HOME/.spotipi_update_state"
LOG="/tmp/spotipi-update.log"
PI="pi@spotipi.local"
PI_DIR="/home/pi/spotipi-photos"
SSH="ssh -o LogLevel=ERROR -o ConnectTimeout=8 -o BatchMode=yes"

exec >>"$LOG" 2>&1
echo "=== $(date) : update check ==="

[ -f "$LATEST" ] || { echo "no latest zip found, skipping"; exit 0; }

SUM=$(shasum -a 256 "$LATEST" | awk '{print $1}')
LAST=$(cat "$STATE" 2>/dev/null || echo "")
if [ "$SUM" = "$LAST" ]; then echo "already up to date ($SUM)"; exit 0; fi
echo "new version detected: $SUM"

TMP=$(mktemp -d) || exit 1
trap 'rm -rf "$TMP"' EXIT
if ! unzip -q "$LATEST" -d "$TMP"; then
  echo "unzip failed (Dropbox still syncing?) -- will retry next run"; exit 0
fi
SRC="$TMP/spotipi-photos"
[ -d "$SRC/python" ] || { echo "unexpected zip layout, aborting"; exit 1; }

rsync -a --delete "$SRC/" "$MAC_WORK/" && echo "Mac working copy updated"

if ! $SSH "$PI" true 2>/dev/null; then
  echo "Pi unreachable -- will retry next run"; exit 0
fi

# Back up + push code only. Exclude __pycache__: the daemon runs as root and
# any *.pyc it wrote are root-owned, so this non-root push can't read/delete
# them (harmless, but it spams the log). Python ignores stale .pyc anyway.
$SSH "$PI" "rm -rf $PI_DIR/python.bak && rsync -a --exclude=__pycache__ $PI_DIR/python/ $PI_DIR/python.bak/"
rsync -az --delete --exclude=__pycache__ -e "ssh -o LogLevel=ERROR" "$SRC/python/" "$PI:$PI_DIR/python/"
echo "Pi code pushed"

$SSH "$PI" "sudo systemctl restart spotipi spotipi-client"
sleep 5
ACTIVE=$($SSH "$PI" "systemctl is-active spotipi spotipi-client" | tr '\n' ' ')
echo "service state after restart: $ACTIVE"

if echo "$ACTIVE" | grep -q "active active"; then
  echo "UPDATE OK -> $SUM"
  $SSH "$PI" "rm -rf $PI_DIR/python.bak"
  echo "$SUM" > "$STATE"
else
  echo "!! services did not come up -- ROLLING BACK"
  $SSH "$PI" "rm -rf $PI_DIR/python && mv $PI_DIR/python.bak $PI_DIR/python && sudo systemctl restart spotipi spotipi-client"
  echo "rolled back (checksum not recorded; will retry when a newer build appears)"
fi
echo "=== done ==="
