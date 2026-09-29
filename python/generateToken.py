#!/usr/bin/env python3
"""
generateToken.py -- do the one-off Spotify login and save the token.

Adapted from the original spotipi project (ryanwa18/spotipi, develop branch),
with two deliberate differences so that the token it writes is the one this
fork actually reads:

  * The cache file is  .cache-<username>  (the upstream script wrote a bare
    .cache). install_pi.sh asks for the token path, and getSongInfo.py opens
    exactly that file, so the name has to be predictable.
  * The scope is pinned to the same SCOPE constant getSongInfo.py requests.
    spotipy treats a cached token granted for a different scope as unusable,
    so these two must not drift apart.

Usage:
    python3 generateToken.py <spotify_username> [cache_path]

Expects SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET and SPOTIPY_REDIRECT_URI in
the environment -- generate-token.sh prompts for them and exports them.
"""

import os
import sys

from spotipy.oauth2 import SpotifyOAuth

# Must match SCOPE in getSongInfo.py. If you change one, change both.
SCOPE = "user-read-currently-playing"


def main():
    if len(sys.argv) < 2:
        print("usage: generateToken.py <spotify_username> [cache_path]")
        return 1

    username = sys.argv[1]
    cache_path = sys.argv[2] if len(sys.argv) > 2 else f".cache-{username}"

    missing = [v for v in ("SPOTIPY_CLIENT_ID",
                           "SPOTIPY_CLIENT_SECRET",
                           "SPOTIPY_REDIRECT_URI")
               if not os.environ.get(v)]
    if missing:
        print("Missing environment variables: " + ", ".join(missing))
        print("Run generate-token.sh instead -- it prompts for these.")
        return 1

    auth = SpotifyOAuth(
        scope=SCOPE,
        username=username,
        cache_path=cache_path,
        open_browser=False,      # headless Pi: print the URL instead
    )

    # Prompts on the terminal: prints the authorise URL, waits for you to paste
    # back the full redirected URL, then writes the cache file.
    token = auth.get_access_token(as_dict=False)

    if not token:
        print("No token returned -- the login did not complete.")
        return 1

    print()
    print("###### Spotify token created ######")
    print(f"Scope    : {SCOPE}")
    print(f"Filename : {os.path.abspath(cache_path)}")
    print()
    print("Give that full path to install_pi.sh when it asks for the token path.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
