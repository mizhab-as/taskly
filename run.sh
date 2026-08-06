#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  Taskly — macOS / Linux Launcher
#  Starts Flask REST API + File Server + Reminder Daemon
# ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure data directory exists
mkdir -p data

echo ""
echo "  ┌─────────────────────────────────────────────┐"
echo "  │              Taskly Launcher                 │"
echo "  └─────────────────────────────────────────────┘"
echo ""

# Find python binary
if command -v python3 &>/dev/null; then
  PYTHON_BIN="python3"
elif command -v python &>/dev/null; then
  PYTHON_BIN="python"
else
  echo "  ❌ Error: Python 3 is required but not installed."
  exit 1
fi

# ── 1. Install Python dependencies ───────────────────────────
echo "  → Installing Python dependencies..."
$PYTHON_BIN -m pip install -r requirements.txt -q

# ── 2. Clean up stale Taskly processes ───────────────────────
if lsof -ti:5050 &>/dev/null; then
  echo "  → Freeing port 5050..."
  lsof -ti:5050 | xargs kill 2>/dev/null || true
  sleep 0.5
  if lsof -ti:5050 &>/dev/null; then
    lsof -ti:5050 | xargs kill -9 2>/dev/null || true
  fi
fi

if [ -f "data/reminders.pid" ]; then
  OLD_PID=$(cat data/reminders.pid)
  kill "$OLD_PID" 2>/dev/null || true
  rm -f data/reminders.pid
fi

# ── 3. Start Flask API + file server ─────────────────────────
echo "  → Starting Python API server (http://localhost:5050)..."
$PYTHON_BIN server.py > data/server.log 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > data/server.pid

# Wait up to 5 seconds for health endpoint
READY=0
for i in {1..10}; do
  if curl -s http://localhost:5050/api/health | grep -q '"status":"ok"' &>/dev/null; then
    READY=1
    break
  fi
  sleep 0.3
done

if [ $READY -eq 1 ]; then
  echo "  ✓ Server ready (PID $SERVER_PID)"
else
  echo "  ⚠️ Server started (PID $SERVER_PID)"
fi

# ── 4. Start reminders daemon ────────────────────────────────
echo "  → Starting reminder daemon..."
$PYTHON_BIN reminders.py > data/reminders.log 2>&1 &

# ── 5. Open web app ──────────────────────────────────────────
echo "  → Opening Taskly at http://localhost:5050"
sleep 0.3

if command -v open &>/dev/null; then
  open "http://localhost:5050"
elif command -v xdg-open &>/dev/null; then
  xdg-open "http://localhost:5050"
fi

echo ""
echo "  ✨ Taskly is running!"
echo "  ─────────────────────────────────────────────"
echo "  Web App  → http://localhost:5050"
echo "  API      → http://localhost:5050/api/health"
echo "  Export   → $PYTHON_BIN export.py"
echo "  Stop     → ./stop.sh"
echo "  ─────────────────────────────────────────────"
echo ""
