"""
main.py
-------
Entry point for the Advanced To-Do List Application.

Run with:
    python main.py

Only uses the Python standard library (json, tkinter, dataclasses, uuid) —
no pip installs required, exactly as specified in the project requirements.
"""

import sys
import tkinter as tk
from tkinter import messagebox

from app.gui import TodoApp


def main():
    try:
        app = TodoApp(user_name="Ender")
        app.mainloop()
    except tk.TclError as e:
        # Happens if no display server is available (e.g. a headless
        # server/container). Fail with a clear, actionable message
        # instead of a raw traceback.
        print("Could not start the GUI. A display is required to run this app.")
        print(f"Details: {e}")
        sys.exit(1)
    except Exception as e:  # last-resort safety net
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
