"""
task_manager.py
---------------
Core business logic for the Taskly (To-Do) application.

Responsibilities:
    * Load / save tasks from a JSON file (persistent storage)
    * Load / save custom categories and onboarding configurations
    * Add, edit, complete, delete tasks (CRUD)
    * Search & filter tasks
    * Provide per-category statistics used by the UI

All exceptions related to file I/O or malformed data are handled here so
that the GUI layer never has to worry about corrupt JSON, missing files,
or permission errors.
"""

import json
import os
import shutil
import uuid
from datetime import datetime

from app.models import Task

DEFAULT_CATEGORIES_DATA = [
    {"id": "Today", "label": "Today", "icon": "☀", "color": "#F59E0B", "bg": "#FFF1D6", "smart": "today"},
    {"id": "Planned", "label": "Planned", "icon": "🗓", "color": "#4C6FFF", "bg": "#E8EDFF", "smart": "planned"},
    {"id": "Personal", "label": "Personal", "icon": "🙂", "color": "#8B5CF6", "bg": "#F1EAFE"},
    {"id": "Work", "label": "Work", "icon": "💼", "color": "#0F172A", "bg": "#E7E9EE"},
    {"id": "Shopping", "label": "Shopping", "icon": "🛍", "color": "#16A34A", "bg": "#E3F9E5"},
]

ROTATING_PALETTE = [
    {"icon": "🛒", "color": "#EC4899", "bg": "#FCE7F3"},  # Pink
    {"icon": "🌟", "color": "#F59E0B", "bg": "#FFF1D6"},  # Amber
    {"icon": "❤️", "color": "#EF4444", "bg": "#FEE2E2"},  # Red
    {"icon": "🎯", "color": "#10B981", "bg": "#D1FAE5"},  # Emerald
    {"icon": "🏷️", "color": "#3B82F6", "bg": "#DBEAFE"},  # Blue
    {"icon": "🏃", "color": "#EC4899", "bg": "#FCE7F3"},  # Pink
]


class TaskManagerError(Exception):
    """Raised for recoverable task-manager errors (bad input, bad id, etc.)."""


class TaskManager:
    def __init__(self, filepath: str = "data/tasks.json"):
        self.filepath = filepath
        self.cat_filepath = "data/categories.json"
        self.config_filepath = "data/config.json"
        
        self.tasks: list[Task] = []
        self.custom_categories: list[dict] = []
        self.onboarded: bool = False
        
        self.load_tasks()
        self.load_categories()
        self.load_config()

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def load_tasks(self):
        """Load tasks from disk. Creates an empty store if none exists yet
        and recovers gracefully from a corrupted JSON file by backing it
        up rather than crashing the app."""
        if not os.path.exists(self.filepath):
            os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
            self.tasks = []
            self.save_tasks()
            return

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.tasks = [Task.from_dict(item) for item in raw]
        except (json.JSONDecodeError, ValueError):
            # Corrupted file: back it up so no data is silently destroyed,
            # then start fresh instead of crashing the whole application.
            backup_path = self.filepath + ".corrupt.bak"
            shutil.copy(self.filepath, backup_path)
            self.tasks = []
            self.save_tasks()
        except OSError as e:
            raise TaskManagerError(f"Could not read tasks file: {e}") from e

    def save_tasks(self):
        """Persist the current in-memory task list to disk atomically
        (write to a temp file, then replace) to avoid corrupting the
        JSON file if the app is closed mid-write."""
        try:
            os.makedirs(os.path.dirname(self.filepath) or ".", exist_ok=True)
            tmp_path = self.filepath + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump([t.to_dict() for t in self.tasks], f, indent=2)
            os.replace(tmp_path, self.filepath)
        except OSError as e:
            raise TaskManagerError(f"Could not save tasks file: {e}") from e

    def load_categories(self):
        """Load custom categories from disk."""
        if not os.path.exists(self.cat_filepath):
            self.custom_categories = []
            return
        try:
            with open(self.cat_filepath, "r", encoding="utf-8") as f:
                self.custom_categories = json.load(f)
        except Exception:
            self.custom_categories = []

    def save_categories(self):
        """Persist custom categories to disk."""
        try:
            os.makedirs(os.path.dirname(self.cat_filepath) or ".", exist_ok=True)
            with open(self.cat_filepath, "w", encoding="utf-8") as f:
                json.dump(self.custom_categories, f, indent=2)
        except OSError as e:
            raise TaskManagerError(f"Could not save categories: {e}") from e

    def load_config(self):
        """Load configuration settings."""
        if not os.path.exists(self.config_filepath):
            self.onboarded = False
            return
        try:
            with open(self.config_filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.onboarded = data.get("onboarded", False)
        except Exception:
            self.onboarded = False

    def save_config(self):
        """Persist configuration settings."""
        try:
            os.makedirs(os.path.dirname(self.config_filepath) or ".", exist_ok=True)
            with open(self.config_filepath, "w", encoding="utf-8") as f:
                json.dump({"onboarded": self.onboarded}, f)
        except Exception:
            pass

    def mark_onboarded(self):
        """Mark onboarding as complete."""
        self.onboarded = True
        self.save_config()

    # ------------------------------------------------------------------ #
    # Category Management
    # ------------------------------------------------------------------ #
    def add_category(self, label: str) -> dict:
        """Create a new custom category with rotating design properties."""
        label = (label or "").strip()
        if not label:
            raise TaskManagerError("Category label cannot be empty.")
        
        # Check for duplicates (case insensitive)
        all_labels = [c["label"].lower() for c in self.get_categories()]
        if label.lower() in all_labels:
            raise TaskManagerError(f"Category '{label}' already exists.")

        index = len(self.custom_categories) % len(ROTATING_PALETTE)
        palette = ROTATING_PALETTE[index]

        new_cat = {
            "id": label,  # Use label as ID to map category references easily
            "label": label,
            "icon": palette["icon"],
            "color": palette["color"],
            "bg": palette["bg"]
        }
        self.custom_categories.append(new_cat)
        self.save_categories()
        return new_cat

    def delete_category(self, label: str):
        """Delete a custom category and cascade delete all its tasks."""
        # Filter category out
        self.custom_categories = [c for c in self.custom_categories if c["label"] != label]
        self.save_categories()

        # Cascade: delete all tasks matching this category
        self.tasks = [t for t in self.tasks if t.category != label]
        self.save_tasks()

    def get_categories(self) -> list[dict]:
        """Returns standard and custom categories combined."""
        return DEFAULT_CATEGORIES_DATA + self.custom_categories

    def all_categories(self) -> list[str]:
        """Returns category labels for standard and custom categories (non-smart)."""
        categories = self.get_categories()
        # Exclude smart lists from task category picker
        return [c["label"] for c in categories if "smart" not in c]

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #
    def add_task(self, title: str, category: str = "Personal",
                 priority: str = "Medium", due_date: str = "") -> Task:
        title = (title or "").strip()
        if not title:
            raise TaskManagerError("Task title cannot be empty.")
        if due_date:
            self._validate_date(due_date)

        task = Task(title=title, category=category, priority=priority, due_date=due_date)
        self.tasks.append(task)
        self.save_tasks()
        return task

    def edit_task(self, task_id: str, **fields) -> Task:
        task = self.get_task(task_id)
        if "due_date" in fields and fields["due_date"]:
            self._validate_date(fields["due_date"])
        for key, value in fields.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)
        self.save_tasks()
        return task

    def complete_task(self, task_id: str) -> Task:
        task = self.get_task(task_id)
        task.completed = True
        self.save_tasks()
        return task

    def toggle_task(self, task_id: str) -> Task:
        task = self.get_task(task_id)
        task.toggle()
        self.save_tasks()
        return task

    def delete_task(self, task_id: str):
        task = self.get_task(task_id)
        self.tasks.remove(task)
        self.save_tasks()

    def get_task(self, task_id: str) -> Task:
        for t in self.tasks:
            if t.id == task_id:
                return t
        raise TaskManagerError(f"No task found with id '{task_id}'.")

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    def list_by_category(self, category: str) -> list[Task]:
        """Returns tasks filtered by category. Shows all matching tasks (completed or not)."""
        if category == "Today":
            today = datetime.now().strftime("%Y-%m-%d")
            return [t for t in self.tasks if t.due_date == today]
        if category == "Planned":
            return [t for t in self.tasks if t.due_date and t.due_date != ""]
        return [t for t in self.tasks if t.category == category]

    def search(self, query: str) -> list[Task]:
        query = query.lower().strip()
        if not query:
            return list(self.tasks)
        return [t for t in self.tasks if query in t.title.lower()]

    def stats(self) -> dict:
        """Returns {category: pending_task_count} used by the categories list."""
        counts = {}
        for c in self.get_categories():
            counts[c["label"]] = 0
            
        for t in self.tasks:
            if t.completed:
                continue
            if t.category in counts:
                counts[t.category] += 1
                
        # Smart list count calculation (uncompleted only)
        today = datetime.now().strftime("%Y-%m-%d")
        counts["Today"] = sum(1 for t in self.tasks if not t.completed and t.due_date == today)
        counts["Planned"] = sum(1 for t in self.tasks if not t.completed and t.due_date)
        return counts

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _validate_date(date_str: str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as e:
            raise TaskManagerError("Due date must be in YYYY-MM-DD format.") from e
