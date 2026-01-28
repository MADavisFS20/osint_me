#!/data/data/com.termux/files/usr/bin/env bash
# Single-command deploy script for Termux OSINT Manager (Original Edition)
# Usage: bash deploy.sh
set -e
echo "[*] Starting full deploy for Termux-OSINT Manager..."
chmod +x install.sh run.sh
bash install.sh
echo "[*] Launching the application..."
bash run.sh