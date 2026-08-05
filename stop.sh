#!/usr/bin/env bash
# Taskly — stop all background processes

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "  → Stopping Taskly..."

# Kill Flask server
if [ -f "data/server.pid" ]; then
  kill "$(cat data/server.pid)" 2>/dev/null && echo "  ✓ Server stopped"
  rm -f data/server.pid
fi
# Belt-and-suspenders: also kill by port
lsof -ti:5050 | xargs kill -9 2>/dev/null

# Kill reminders daemon
if [ -f "data/reminders.pid" ]; then
  kill "$(cat data/reminders.pid)" 2>/dev/null && echo "  ✓ Reminders daemon stopped"
  rm -f data/reminders.pid
fi

echo "  ✓ Done."
