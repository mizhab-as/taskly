#!/usr/bin/env bash
# Taskly — run script for macOS/Linux
# Auto-installs dependencies and launches the app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "→ Installing dependencies..."
pip3 install -r requirements.txt -q

echo "→ Launching Taskly..."
python3 main.py "$@"
