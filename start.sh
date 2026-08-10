#!/usr/bin/env bash
# Taskly — Single Startup Launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  ┌─────────────────────────────────────────────┐"
echo "  │              Taskly Launcher                 │"
echo "  └─────────────────────────────────────────────┘"
echo ""

# 1. Install python dependencies if virtualenv or system python
echo "  → Installing Python dependencies..."
python3 -m pip install -q -r requirements.txt 2>/dev/null || true

# 2. Free port 5050 if occupied
echo "  → Freeing port 5050..."
if lsof -ti:5050 &>/dev/null; then
  lsof -ti:5050 | xargs kill -9 2>/dev/null || true
  sleep 1
fi

# 3. Start Python API server (background)
echo "  → Starting Python API server (http://localhost:5050)..."
python3 python/server.py &
SERVER_PID=$!
mkdir -p data
echo "$SERVER_PID" > data/server.pid
sleep 1

# Check server is up
if ! lsof -ti:5050 &>/dev/null; then
  echo "  ❌ Failed to start server."
  exit 1
fi
echo "  ✓ Server ready (PID $SERVER_PID)"

# 4. Start Reminders Daemon (background)
echo "  → Starting reminder daemon..."
python3 python/reminders.py &>/dev/null &
REM_PID=$!
echo "$REM_PID" > data/reminders.pid

# 5. Open browser on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo "  → Opening Taskly at http://localhost:5050"
  open "http://localhost:5050"
elif command -v xdg-open &>/dev/null; then
  xdg-open "http://localhost:5050"
fi

echo ""
echo "  ✨ Taskly is running!"
echo "  ─────────────────────────────────────────────"
echo "  Web App  → http://localhost:5050"
echo "  API      → http://localhost:5050/api/health"
echo "  Export   → python3 python/export.py"
echo "  ─────────────────────────────────────────────"
echo ""
