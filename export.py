"""
Taskly — Data Export Utility  (Option 3)
==========================================
Standalone CLI export tool for tasks data.

Usage:
  python3 export.py           # exports JSON + CSV to exports/
  python3 export.py --json    # JSON only
  python3 export.py --csv     # CSV only
  python3 export.py --out /some/path
"""

import json
import csv
import os
import sys
import datetime
import argparse

DATA_FILE   = os.path.join(os.path.dirname(__file__), "data", "tasks.json")
EXPORT_DIR  = os.path.join(os.path.dirname(__file__), "exports")


def load_data() -> dict | None:
    if not os.path.exists(DATA_FILE):
        print(f"[export] No data file found at {DATA_FILE}")
        return None
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # Handle legacy format: old Python app stored a plain list at root
    if isinstance(raw, list):
        raw = {
            "lists": {},
            "tasks": [
                {
                    "id":       t.get("id", i),
                    "list":     t.get("category", "work").lower(),
                    "title":    t.get("title", ""),
                    "priority": t.get("priority", "Medium"),
                    "done":     t.get("completed", False),
                    "due":      t.get("due_date", "") or "",
                }
                for i, t in enumerate(raw)
            ],
            "nextId": len(raw) + 1,
        }
    return raw


def export_json(data: dict, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(out_dir, f"taskly_export_{ts}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filename


def export_csv(data: dict, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    lists    = data.get("lists", {})
    tasks    = data.get("tasks", [])
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(out_dir, f"taskly_export_{ts}.csv")

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "title", "list", "list_name", "priority", "done", "due"],
        )
        writer.writeheader()
        for t in tasks:
            list_meta = lists.get(t.get("list", ""), {})
            writer.writerow({
                "id":        t.get("id", ""),
                "title":     t.get("title", ""),
                "list":      t.get("list", ""),
                "list_name": list_meta.get("name", ""),
                "priority":  t.get("priority", ""),
                "done":      "yes" if t.get("done") else "no",
                "due":       t.get("due", ""),
            })
    return filename


def print_summary(data: dict):
    tasks  = data.get("tasks", [])
    done   = sum(1 for t in tasks if t.get("done"))
    today  = datetime.date.today().isoformat()
    overdue = sum(1 for t in tasks if t.get("due") and t["due"] < today and not t.get("done"))
    print(f"\n  📊 Taskly Data Summary")
    print(f"  ─────────────────────")
    print(f"  Total tasks  : {len(tasks)}")
    print(f"  Completed    : {done}")
    print(f"  Pending      : {len(tasks) - done}")
    print(f"  Overdue      : {overdue}")
    print(f"  Lists        : {len(data.get('lists', {}))}\n")


def main():
    parser = argparse.ArgumentParser(description="Taskly export utility")
    parser.add_argument("--json",  action="store_true", help="Export JSON only")
    parser.add_argument("--csv",   action="store_true", help="Export CSV only")
    parser.add_argument("--out",   default=EXPORT_DIR,  help="Output directory")
    parser.add_argument("--summary", action="store_true", help="Print summary only, no export")
    args = parser.parse_args()

    data = load_data()
    if not data:
        sys.exit(1)

    if args.summary:
        print_summary(data)
        return

    do_json = args.json or (not args.json and not args.csv)
    do_csv  = args.csv  or (not args.json and not args.csv)

    if do_json:
        path = export_json(data, args.out)
        print(f"  ✓ JSON exported → {path}")

    if do_csv:
        path = export_csv(data, args.out)
        print(f"  ✓ CSV  exported → {path}")

    print_summary(data)


if __name__ == "__main__":
    main()
