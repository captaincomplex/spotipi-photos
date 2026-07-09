#!/bin/bash
# install_pi.sh -- install the photo + Spotify display on the Raspberry Pi.
#
# Run from inside the spotipi-photos folder on the Pi:
#     cd ~/spotipi-photos
#     sudo bash install_pi.sh
#
# Safe to re-run. Works even on end-of-life Raspbian (Buster), where the apt
# repos are archived -- package steps are best-effort and never abort the run.
set -u   # intentionally NOT 'set -e' -- EOL apt/pip must not kill the install

INSTALL_PATH="$(cd "$(dirname "$0")" && pwd)"

echo "==> System packages (best-effort; ignored on EOL systems)"
sudo apt-get install -y libopenjp2-7 python3-pip python3-pil 2>/dev/null \
  || echo "    (apt unavailable or already present -- continuing)"

echo "==> Python libraries (best-effort)"
if ! python3 -c "import flask, spotipy, PIL, requests" 2>/dev/null; then
  python3 -m pip install spotipy pillow requests 2>/dev/null || true
  if ! python3 -c "import flask" 2>/dev/null; then
    python3 -m pip install flask 2>/dev/null \
      || python3 -m pip install "Flask==2.0.3" "Werkzeug==2.0.3" "Jinja2==3.0.3" \
                                "itsdangerous==2.0.1" "MarkupSafe==2.0.1" 2>/dev/null \
      || echo "    (could not auto-install Flask -- install manually if web UI fails)"
  fi
fi
python3 -c "import flask, spotipy, PIL, requests" 2>/dev/null \
  && echo "    all Python deps present" \
  || echo "    WARNING: some Python deps missing -- see README troubleshooting"

echo
echo "==> rgb-matrix driver"
echo "    If the 'rgbmatrix' python module isn't built yet, run the Adafruit"
echo "    installer once, then re-run this script:"
echo "      curl https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/rgb-matrix.sh >rgb-matrix.sh"
echo "      sudo bash rgb-matrix.sh"
echo

read -p "Spotify username: " SPOTIFY_USERNAME
read -p "Full path to your Spotify token (.cache file): " TOKEN_PATH
read -p "Spotify Client ID: " SPOTIFY_CLIENT_ID
read -p "Spotify Client Secret: " SPOTIFY_CLIENT_SECRET
read -p "Spotify Redirect URI: " SPOTIFY_REDIRECT_URI

mkdir -p "${INSTALL_PATH}/photos"

echo "==> Fixing config permissions (display runs as root and reads these)"
chmod 777 "${INSTALL_PATH}/config" 2>/dev/null || true
chmod 666 "${INSTALL_PATH}/config/state.json" 2>/dev/null || true

echo "==> Creating spotipi display service"
sudo systemctl stop spotipi 2>/dev/null || true
sudo rm -rf /etc/systemd/system/spotipi.service /etc/systemd/system/spotipi.service.d
sudo cp "${INSTALL_PATH}/config/spotipi.service" /etc/systemd/system/
sudo sed -i -e "/\[Service\]/a WorkingDirectory=${INSTALL_PATH}/python" /etc/systemd/system/spotipi.service
sudo sed -i -e "/\[Service\]/a ExecStart=/usr/bin/python3 ${INSTALL_PATH}/python/displaySpotipi.py ${SPOTIFY_USERNAME} ${TOKEN_PATH}" /etc/systemd/system/spotipi.service

sudo mkdir -p /etc/systemd/system/spotipi.service.d
ENVCONF=/etc/systemd/system/spotipi.service.d/spotipi_env.conf
sudo bash -c "cat > ${ENVCONF}" <<EOF
[Service]
Environment="SPOTIPY_CLIENT_ID=${SPOTIFY_CLIENT_ID}"
Environment="SPOTIPY_CLIENT_SECRET=${SPOTIFY_CLIENT_SECRET}"
Environment="SPOTIPY_REDIRECT_URI=${SPOTIFY_REDIRECT_URI}"
EOF

echo "==> Creating spotipi-client web service"
sudo systemctl stop spotipi-client 2>/dev/null || true
sudo rm -f /etc/systemd/system/spotipi-client.service
sudo cp "${INSTALL_PATH}/config/spotipi-client.service" /etc/systemd/system/
sudo sed -i -e "/\[Service\]/a WorkingDirectory=${INSTALL_PATH}/python/client" /etc/systemd/system/spotipi-client.service
sudo sed -i -e "/\[Service\]/a ExecStart=/usr/bin/python3 ${INSTALL_PATH}/python/client/app.py" /etc/systemd/system/spotipi-client.service

echo "==> Enabling services"
sudo systemctl daemon-reload
sudo systemctl enable spotipi spotipi-client
sudo systemctl restart spotipi spotipi-client

echo
echo "Done."
echo "  Display : sudo systemctl status spotipi"
echo "  Web     : http://<pi-ip>  (port 80)"
echo "  Photos  : ${INSTALL_PATH}/photos"
echo
echo "If the panel stays blank, check:  journalctl -u spotipi -n 30"
