"""
models.py
---------
Defines the Task data model used across the To-Do application.
Keeping the model in its own module makes the codebase modular and
testable, and mirrors how larger real-world Python apps are structured.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
import itertools
import uuid


PRIORITIES = ("Low", "Medium", "High")
CATEGORIES = ("Today", "Planned", "Personal", "Work", "Shopping")


@dataclass
class Task:
    title: str
    category: str = "Personal"
    priority: str = "Medium"
    due_date: str = ""          # stored as "YYYY-MM-DD" or ""
    completed: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def toggle(self):
        self.completed = not self.completed

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Task":
        # Defensive construction: ignores unknown keys, fills sensible
        # defaults for missing ones so older/edited JSON files still load.
        return Task(
            title=data.get("title", "Untitled task"),
            category=data.get("category", "Personal"),
            priority=data.get("priority", "Medium"),
            due_date=data.get("due_date", ""),
            completed=bool(data.get("completed", False)),
            id=data.get("id", uuid.uuid4().hex[:8]),
            created_at=data.get("created_at", datetime.now().isoformat(timespec="seconds")),
        )
