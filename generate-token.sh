#!/bin/bash
# generate-token.sh -- one-off Spotify login for spotipi-photos.
#
# Run this on the Pi, from inside the spotipi-photos folder, BEFORE
# install_pi.sh -- the installer asks for the path to the file this creates.
#
#     cd ~/spotipi-photos
#     bash generate-token.sh
#
# You need a Spotify developer app first (free). See the "Spotify" part of
# docs/guides/SPOTIPI_BEGINNERS_GUIDE.md for how to create one and where the
# Client ID, Client Secret and Redirect URI come from.
#
# Re-run this whenever album art stops appearing -- Spotify invalidates the
# authorisation roughly every six months. See SPOTIFY_TOKEN_RENEWAL.txt.
set -u

cd "$(dirname "$0")"

if ! python3 -c "import spotipy" 2>/dev/null; then
  echo "==> Installing the spotipy library"
  python3 -m pip install spotipy 2>/dev/null \
    || python3 -m pip install --break-system-packages spotipy 2>/dev/null \
    || { echo "! Could not install spotipy. Install it, then re-run this."; exit 1; }
fi

echo
echo "From your Spotify app at https://developer.spotify.com/dashboard"
echo "(Settings -> Basic Information). Nothing is sent anywhere but Spotify."
echo

read -rp "Spotify Client ID: "     SPOTIPY_CLIENT_ID
read -rp "Spotify Client Secret: " SPOTIPY_CLIENT_SECRET
read -rp "Spotify Redirect URI:  " SPOTIPY_REDIRECT_URI
read -rp "Spotify username:      " SPOTIFY_USERNAME

export SPOTIPY_CLIENT_ID SPOTIPY_CLIENT_SECRET SPOTIPY_REDIRECT_URI

if [ -z "${SPOTIFY_USERNAME}" ]; then
  echo "! A username is required -- the token file is named after it."
  exit 1
fi

echo
echo "==> A long https://accounts.spotify.com/... URL follows."
echo "    1. Open it in a browser on any device and log in / click Agree."
echo "    2. Your browser will jump to your redirect address, which will look"
echo "       like a page that FAILED TO LOAD. That is expected and correct."
echo "    3. Copy that entire address from the address bar and paste it back"
echo "       here, then press Enter."
echo

python3 python/generateToken.py "${SPOTIFY_USERNAME}" ".cache-${SPOTIFY_USERNAME}"
