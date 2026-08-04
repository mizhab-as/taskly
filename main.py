"""
main.py
-------
Entry point for Taskly — Advanced Task Manager.

Run with:
    python main.py
    or
    ./run.sh

Dependencies: customtkinter (pip install customtkinter)
"""

import sys
from app.gui import TasklyApp


def main():
    try:
        app = TasklyApp(user_name="Ender")
        app.mainloop()
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
