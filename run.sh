#!/usr/bin/env bash
# Launcher script for Tudy To-Do List Application

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 &>/dev/null; then
    python3 main.py "$@"
elif command -v python &>/dev/null; then
    python main.py "$@"
else
    echo "Error: Python was not found on your system."
    echo "Please install Python 3.9 or higher."
    exit 1
fi
