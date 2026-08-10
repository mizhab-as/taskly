#!/usr/bin/env bash
# Taskly Startup Script Alias
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR/run.sh" "$SCRIPT_DIR/stop.sh"
exec "$SCRIPT_DIR/run.sh" "$@"
