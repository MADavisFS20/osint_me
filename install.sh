#/data/data/com.termux/files/usr/bin/env bash
# Install system packages and Python dependencies inside Termux, create venv, and install pip packages.
set -e
echo "[*] Updating Termux packages..."
pkg update -y
pkg upgrade -y 

echo "[*] Installing required system packages..."
pkg install -y python git clang make openssh proot-distro termux-api

echo "[*] (Optional) For GUI use Termux:X11 from F-Droid. Install 'nmap' if you want native scanning tools."
echo "If you want Tor support, run: pkg install tor"

echo "[*] Creating virtualenv..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install virtualenv
if [ ! -d ".venv" ]; then
  python -m virtualenv .venv
fi

# Activate venv for this script
source .venv/bin/activate

echo "[*] Installing Python requirements (this may take a few minutes)..."

# install with fallback: if python import fails, install the pkg
if ! python3 -c "import pywt" >/dev/null 2>&1; then
  pkg install -y python-pywavelets
fi

pip install -r requirements.txt

echo "[*] Preparing directories..."
mkdir -p backend/evidence backend/reports data

echo "[*] Installation complete. You can run: bash run.sh"
