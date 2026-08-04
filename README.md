# Taskly — Advanced To-Do List Manager (Python)

An advanced, GUI-based evolution of the original CLI To-Do List project brief.
It fulfils every original requirement (add / view / complete / delete / JSON
persistence / auto-load / safe exit) and adds the "future enhancements" the
original plan listed as optional: a graphical interface, categories, due
dates, priorities, search, and a matching visual design system.

![status](https://img.shields.io/badge/python-3.9%2B-blue) ![deps](https://img.shields.io/badge/dependencies-standard%20library%20only-brightgreen)

## ✨ Features

| Original requirement            | Status | Where implemented |
|----------------------------------|--------|--------------------|
| Add a new task                   | ✅ | `TaskManager.add_task()` |
| Display all tasks                | ✅ | `TaskManager.list_by_category()` / GUI list |
| Mark a task as completed         | ✅ | `TaskManager.complete_task()` / checkbox in GUI |
| Delete a task                    | ✅ | `TaskManager.delete_task()` |
| Save tasks permanently (JSON)    | ✅ | `TaskManager.save_tasks()` (atomic write) |
| Auto-load tasks on start         | ✅ | `TaskManager.load_tasks()` |
| Exit safely                      | ✅ | window close / all writes flushed immediately |

**Advanced additions:**
- 🖼️ **Full GUI** built with Tkinter (no external libraries — still zero `pip install`s)
- 🗂️ **Categories / lists** (Today, Planned, Personal, Work, Shopping + custom lists)
- 🚩 **Priorities** (Low / Medium / High) with colour-coded indicators
- 📅 **Due dates** with validation, feeding a "Today" and "Planned" smart view
- 🔍 **Live search** across all tasks
- 🧱 **Modular architecture** — `models.py` / `task_manager.py` / `gui.py` are fully decoupled, so the same `TaskManager` could power a CLI, a Flask API, or this GUI unchanged
- 🛡️ **Exception handling** for empty titles, malformed dates, missing/corrupted JSON (auto-backs up a corrupt file instead of crashing), and unknown task ids
- 💾 **Atomic saves** (write-then-replace) so a crash mid-write can't corrupt your data
- 🎨 **Design system** matching the reference mockup (see `design/design_mockup.html`)

## 📁 Project Structure

```
todo_app_advanced/
├── main.py                 # Entry point
├── app/
│   ├── __init__.py
│   ├── models.py            # Task dataclass
│   ├── task_manager.py       # CRUD + persistence + validation (business logic)
│   └── gui.py                # Tkinter GUI (presentation layer)
├── data/
│   └── tasks.json            # Persistent storage (auto-created if missing)
├── design/
│   └── design_mockup.html     # Visual design system / mockup (open in a browser)
├── screenshots/              # Put your own screenshots here for submission
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

```bash
# 1. Clone / unzip the project
cd todo_app_advanced

# 2. (Optional) create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Run — no pip installs needed, Tkinter ships with standard Python
python main.py
```

> Tkinter requires a display. If you're on a headless Linux server, install
> `python3-tk` and run it locally, over a desktop session, or through
> **Anthropic's Claude Code / Claude Desktop**, VS Code, or PyCharm on your
> own machine.

## 🧠 Architecture / Algorithms

**Add Task**
1. Read title, category, priority, due date from the dialog.
2. Validate: title non-empty, due date matches `YYYY-MM-DD` if provided.
3. Construct a `Task`, append to in-memory list, persist to JSON.

**View Tasks**
1. Load tasks (already in memory after start-up).
2. Filter by selected category / search query.
3. Sort: pending before completed → priority (High→Low) → due date.

**Complete / Toggle Task**
1. Look up task by id (raises a clear error if not found).
2. Flip `completed` flag, persist.

**Delete Task**
1. Look up task by id.
2. Remove from list, persist, confirm via dialog before destructive action.

**Persistence**
- Every mutation calls `save_tasks()`, which writes to a temp file and
  atomically replaces `tasks.json` — protects against partial writes.
- On start-up, a missing file is created empty; a corrupted file is backed
  up to `tasks.json.corrupt.bak` and the app starts fresh instead of crashing.

## ✅ Testing Checklist

- [x] Add multiple tasks across different categories
- [x] Complete / un-complete a task
- [x] Delete a task (with confirmation)
- [x] Restart the application → tasks persist from `data/tasks.json`
- [x] Invalid input handled gracefully (empty title, bad date format, corrupt JSON)
- [x] Search filters the visible list live
- [x] Custom category ("+ New list") creation

Run the included logic smoke test any time with:
```bash
python -c "
from app.task_manager import TaskManager
tm = TaskManager(filepath='data/tasks_smoke_test.json')
t = tm.add_task('Test task', category='Work', priority='High', due_date='2026-08-01')
tm.toggle_task(t.id)
tm.delete_task(t.id)
print('OK')
"
```

## 🔮 Future Enhancements (beyond this version)

- Web version with Flask + this same `TaskManager` as the backend
- SQLite/PostgreSQL storage swap-in (interface already isolated in `TaskManager`)
- User accounts / login
- Reminders & notifications
- Drag-and-drop task reordering
- Export to PDF / CSV

## 📄 Resume Description

> Designed and built an advanced Python desktop To-Do List application with a
> custom Tkinter GUI, implementing full CRUD operations, category- and
> priority-based task organization, due-date validation, live search, atomic
> JSON persistence, and robust exception handling — following a modular,
> testable architecture that separates data, business logic, and presentation.

## 📦 Submission Checklist

- [x] Source Code
- [x] README
- [ ] Screenshots *(add your own to `screenshots/` after running the app)*
- [ ] Output images
- [ ] GitHub repository *(push this folder as-is)*
- [ ] Project report
- [ ] Demonstration video *(optional)*
