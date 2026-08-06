#!/usr/bin/env bash
# Taskly — stop all background processes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "  → Stopping Taskly..."

# Kill Flask server
if [ -f "data/server.pid" ]; then
  SERVER_PID=$(cat data/server.pid)
  kill "$SERVER_PID" 2>/dev/null && echo "  ✓ Server stopped (PID $SERVER_PID)"
  rm -f data/server.pid
fi

# Belt-and-suspenders: kill any remaining process on port 5050
if lsof -ti:5050 &>/dev/null; then
  lsof -ti:5050 | xargs kill -9 2>/dev/null || true
  echo "  ✓ Port 5050 freed"
fi

# Kill reminders daemon
if [ -f "data/reminders.pid" ]; then
  REM_PID=$(cat data/reminders.pid)
  kill "$REM_PID" 2>/dev/null && echo "  ✓ Reminders daemon stopped (PID $REM_PID)"
  rm -f data/reminders.pid
fi

echo "  ✓ Taskly stopped successfully."
