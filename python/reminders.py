"""
Taskly — Reminder Daemon  (Option 4)
======================================
Background process that watches for overdue tasks and fires
macOS desktop notifications every 5 minutes.

Run with:  python3 python/reminders.py
Kill with: kill $(cat data/reminders.pid)
"""

import json
import os
import time
import datetime
import subprocess
import sys

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE   = os.path.join(BASE_DIR, "data", "tasks.json")
PID_FILE    = os.path.join(BASE_DIR, "data", "reminders.pid")
CHECK_EVERY = 300   # seconds between checks (5 minutes)

# IDs of tasks we already notified about (avoid repeat spam per session)
_notified: set = set()


def load_tasks() -> list:
    """Read tasks directly from disk (works without the server running)."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("tasks", [])
    except Exception:
        return []


def notify(title: str, message: str):
    """
    Send a macOS desktop notification via osascript.
    Falls back to a terminal bell on non-macOS.
    """
    if sys.platform == "darwin":
        script = (
            f'display notification "{message}" '
            f'with title "{title}" '
            f'sound name "Purr"'
        )
        subprocess.run(["osascript", "-e", script], capture_output=True)
    else:
        # Linux fallback: try libnotify
        try:
            subprocess.run(
                ["notify-send", title, message],
                capture_output=True,
                timeout=3,
            )
        except FileNotFoundError:
            print(f"[Taskly] {title}: {message}")


def check_overdue():
    """Check for overdue tasks and fire notifications for new ones."""
    today  = datetime.date.today().isoformat()
    tasks  = load_tasks()
    overdue = [
        t for t in tasks
        if t.get("due") and t["due"] < today and not t.get("done")
    ]

    new_overdue = [t for t in overdue if t["id"] not in _notified]
    if not new_overdue:
        return

    count = len(new_overdue)
    if count == 1:
        task  = new_overdue[0]
        title = "⏰ Taskly — Task Overdue"
        msg   = f'"{task["title"]}" was due on {task["due"]}'
    else:
        title = f"⏰ Taskly — {count} Tasks Overdue"
        msg   = ", ".join(f'"{t["title"]}"' for t in new_overdue[:3])
        if count > 3:
            msg += f" and {count - 3} more"

    notify(title, msg)
    for t in new_overdue:
        _notified.add(t["id"])

    print(f"[{datetime.datetime.now().strftime('%H:%M')}] Notified: {msg}")


def write_pid():
    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def main():
    write_pid()
    print(f"[Taskly Reminders] Started (PID {os.getpid()}). Checking every {CHECK_EVERY // 60} min.")
    print(f"[Taskly Reminders] Watching: {DATA_FILE}")

    # Check immediately on startup
    check_overdue()

    while True:
        time.sleep(CHECK_EVERY)
        check_overdue()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Taskly Reminders] Stopped.")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
