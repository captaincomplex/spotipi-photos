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
NEEDS_REBOOT=0

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
if python3 -c "import rgbmatrix" 2>/dev/null; then
  echo "    rgbmatrix module present."
else
  echo "    The 'rgbmatrix' module isn't built on this Pi yet."
  echo
  echo "    Adafruit have replaced their old rgb-matrix.sh with a Python"
  echo "    installer (the .sh URL that used to be printed here now 404s)."
  echo "    Run this once, then re-run this script:"
  echo
  echo "      sudo apt install -y python3-pip python3-venv git"
  echo "      cd ~"
  echo "      python3 -m venv env --system-site-packages"
  echo "      source env/bin/activate"
  echo "      pip3 install --upgrade setuptools adafruit-python-shell click"
  echo "      git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git"
  echo "      cd Raspberry-Pi-Installer-Scripts"
  echo "      sudo -E env PATH=\$PATH python3 rgb-matrix.py"
  echo
  echo "    Answer: Bonnet (or HAT), then Quality or Convenience -- see"
  echo "    docs/guides/SPOTIPI_BEGINNERS_GUIDE.md for which to pick."
  echo
fi

echo "==> Onboard sound"
# The matrix and the Pi's onboard audio share a timing circuit, so the sound
# has to be off or the panel flickers. Adafruit's installer only handles this
# on its "quality" path; on the convenience path it is left on. This Pi has
# nothing plugged into its audio output, so turning it off costs nothing.
BOOTCFG=/boot/firmware/config.txt
[ -f "$BOOTCFG" ] || BOOTCFG=/boot/config.txt
if [ -f "$BOOTCFG" ]; then
  if grep -q "^dtparam=audio=off" "$BOOTCFG"; then
    echo "    Already off in $BOOTCFG."
  else
    if grep -q "^dtparam=audio=on" "$BOOTCFG"; then
      sudo sed -i 's/^dtparam=audio=on/dtparam=audio=off/' "$BOOTCFG"
    else
      echo "dtparam=audio=off" | sudo tee -a "$BOOTCFG" >/dev/null
    fi
    echo "    Set dtparam=audio=off in $BOOTCFG -- takes effect on next reboot."
    NEEDS_REBOOT=1
  fi
else
  echo "    ! Could not find config.txt -- set dtparam=audio=off by hand."
fi
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

echo "==> Creating spotipi-icloud sync service"
# Optional: only does anything once an album link is set in the control panel.
sudo systemctl stop spotipi-icloud 2>/dev/null || true
sudo rm -f /etc/systemd/system/spotipi-icloud.service
sudo cp "${INSTALL_PATH}/config/spotipi-icloud.service" /etc/systemd/system/
sudo sed -i -e "/\[Service\]/a WorkingDirectory=${INSTALL_PATH}/python" /etc/systemd/system/spotipi-icloud.service
sudo sed -i -e "/\[Service\]/a ExecStart=/usr/bin/python3 ${INSTALL_PATH}/python/icloudSync.py" /etc/systemd/system/spotipi-icloud.service

echo "==> Enabling services"
sudo systemctl daemon-reload
sudo systemctl enable spotipi spotipi-client spotipi-icloud
sudo systemctl restart spotipi spotipi-client spotipi-icloud

echo
echo "Done."
echo "  Display : sudo systemctl status spotipi"
echo "  Web     : http://<pi-ip>  (port 80)"
echo "  Photos  : ${INSTALL_PATH}/photos"
echo "  iCloud  : sudo systemctl status spotipi-icloud"
echo "            (idle until you paste a Shared Album link in the web UI)"
echo
echo "If the panel stays blank, check:  journalctl -u spotipi -n 30"
if [ "${NEEDS_REBOOT:-0}" = "1" ]; then
  echo
  echo "  NOTE: onboard sound was switched off for panel stability."
  echo "        Reboot to apply:  sudo reboot"
fi
