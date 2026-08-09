"""
Taskly — Python Flask API Server
=================================
Option 1 : REST API   — CRUD for tasks & lists stored in data/tasks.json
Option 2 : File server — serves frontend/ as a static web app at localhost:5050
Option 3 : Export     — /api/export/json and /api/export/csv endpoints

Run with:  python3 server.py
"""

import json
import os
import csv
import io
import datetime
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS

# ── Config ────────────────────────────────────────────────────────────────────
PORT      = int(os.environ.get("PORT", 5050))
DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "tasks.json")
FRONTEND  = os.path.join(os.path.dirname(__file__), "frontend")

app = Flask(__name__, static_folder=FRONTEND, static_url_path="")
CORS(app)  # allow requests from file:// and any localhost port


# ── Data helpers ──────────────────────────────────────────────────────────────
def load_data():
    """Load persisted data from disk. Returns None if no file exists yet."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_data(data: dict):
    """Atomically write data to disk."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


# ── Static: serve the frontend ────────────────────────────────────────────────
@app.route("/")
def index():
    """Option 2 — Python serves the web app."""
    return send_from_directory(FRONTEND, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND, filename)


# ── API: health check ─────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "mode": "server",
        "port": PORT,
        "timestamp": datetime.datetime.now().isoformat(),
    })


# ── API: full data blob (mirrors localStorage shape) ─────────────────────────
@app.route("/api/data", methods=["GET"])
def get_data():
    """Return all task data. 204 if no data saved yet (frontend uses defaults)."""
    data = load_data()
    if data is None:
        return "", 204
    return jsonify(data)


@app.route("/api/data", methods=["POST"])
def post_data():
    """Save the full data blob sent by the frontend."""
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No data provided"}), 400
    save_data(data)
    return jsonify({"ok": True, "saved": datetime.datetime.now().isoformat()})


# ── API: export endpoints (Option 3) ─────────────────────────────────────────
@app.route("/api/export/json")
def export_json():
    """Download a timestamped JSON backup of all tasks."""
    data = load_data()
    if not data:
        return jsonify({"error": "No data to export"}), 404
    ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"taskly_export_{ts}.json"
    content  = json.dumps(data, ensure_ascii=False, indent=2)
    return Response(
        content,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.route("/api/export/csv")
def export_csv():
    """Download tasks as a CSV file."""
    data = load_data()
    if not data:
        return jsonify({"error": "No data to export"}), 404

    lists = data.get("lists", {})
    tasks = data.get("tasks", [])
    ts    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
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

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=taskly_export_{ts}.csv"},
    )


# ── API: overdue tasks (used by reminders.py) ────────────────────────────────
@app.route("/api/overdue")
def overdue():
    """Return tasks that are overdue and not yet done."""
    data = load_data()
    if not data:
        return jsonify([])
    today  = datetime.date.today().isoformat()
    result = [
        t for t in data.get("tasks", [])
        if t.get("due") and t["due"] < today and not t.get("done")
    ]
    return jsonify(result)


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"  ╭─────────────────────────────────────────╮")
    print(f"  │  Taskly API + File Server                │")
    print(f"  │  http://localhost:{PORT}                    │")
    print(f"  │  Press Ctrl+C to stop                    │")
    print(f"  ╰─────────────────────────────────────────╯")
    app.run(host="0.0.0.0", port=PORT, debug=False)
