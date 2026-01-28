#!/data/data/com.termux/files/usr/bin/env bash
# Start the FastAPI backend and open the GUI in X browser (Termux:X11).
set -e
if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

echo "[*] Ensuring backend DB & default admin..."
python -c "import backend.main as m; m.ensure_admin()"

echo "[*] Starting backend (uvicorn) on http://127.0.0.1:8000 ..."
# Run backend in background
python backend/main.py &

sleep 1

# Try to open a browser in the X session (Termux:X11)
if command -v x-www-browser >/dev/null 2>&1; then
  x-www-browser "http://127.0.0.1:8000" || true
elif command -v firefox >/dev/null 2>&1; then
  firefox "http://127.0.0.1:8000" & || true
else
  echo "Open a browser in your termux-x11 session and visit: http://127.0.0.1:8000"
fi

echo "[*] Backend started. Visit the UI in the X browser."