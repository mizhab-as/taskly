#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  Taskly — macOS / Linux launcher
#  Starts 4 Python-powered layers, then opens the web app.
#
#  Option 1 : Flask REST API    (localhost:5050/api/*)
#  Option 2 : Python file server (Flask serves frontend/)
#  Option 3 : export.py available — run: python3 export.py
#  Option 4 : reminders.py runs in background
# ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  ┌─────────────────────────────────────────────┐"
echo "  │              Taskly Launcher                 │"
echo "  └─────────────────────────────────────────────┘"
echo ""

# ── 1. Install Python dependencies ───────────────────────────
echo "  → Installing Python dependencies..."
pip3 install -r requirements.txt -q

# ── 2. Kill any stale Taskly server processes ────────────────
if lsof -ti:5050 &>/dev/null; then
  echo "  → Killing stale server on port 5050..."
  kill "$(lsof -ti:5050)" 2>/dev/null
  sleep 0.5
fi

if [ -f "data/reminders.pid" ]; then
  OLD_PID=$(cat data/reminders.pid)
  kill "$OLD_PID" 2>/dev/null
  rm -f data/reminders.pid
fi

# ── 3. Start Flask API + file server (Option 1 & 2) ─────────
echo "  → Starting Python API server (localhost:5050)..."
python3 server.py > data/server.log 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > data/server.pid

# Wait briefly for server to be ready
sleep 1.2

# ── 4. Start reminders daemon (Option 4) ─────────────────────
echo "  → Starting reminder daemon..."
python3 reminders.py > data/reminders.log 2>&1 &
# PID is written by reminders.py itself

# ── 5. Open browser (served by Python — Option 2) ────────────
echo "  → Opening Taskly at http://localhost:5050"
sleep 0.3

if command -v open &>/dev/null; then
  open "http://localhost:5050"
elif command -v xdg-open &>/dev/null; then
  xdg-open "http://localhost:5050"
fi

echo ""
echo "  ✓ Taskly is running!"
echo ""
echo "  Web app  → http://localhost:5050"
echo "  API      → http://localhost:5050/api/health"
echo "  Export   → python3 export.py"
echo "  Stop     → ./stop.sh"
echo ""
