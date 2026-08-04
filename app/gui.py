"""
gui.py
------
Taskly — Professional dark-mode task manager built with CustomTkinter.

Stack: CustomTkinter 6.x (rounded widgets, HiDPI, system dark-mode aware)
Backend: TaskManager / models (pure standard library, unchanged)
"""

import tkinter as tk
import customtkinter as ctk
from datetime import datetime, timedelta
import os

from app.task_manager import TaskManager, TaskManagerError
from app.models import PRIORITIES

# Module-level root reference — set once TasklyApp.__init__ runs
_ROOT = None

# ─── Global appearance ────────────────────────────────────────────────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─── Design tokens ────────────────────────────────────────────────────────────
BG          = "#0D0D1A"
SURFACE     = "#161625"
SURFACE2    = "#1E1E35"
SURFACE3    = "#252540"
BORDER      = "#2E2E50"

ACCENT      = "#7C6FFF"   # Vivid violet
ACCENT_H    = "#9B8FFF"   # Hover
TEAL        = "#00D4AA"   # Secondary teal
TEAL_H      = "#33DDBB"
GOLD        = "#FFD166"
ROSE        = "#FF6B9D"
GREEN       = "#06D6A0"

TEXT        = "#EEEEff"
TEXT_M      = "#9090B0"
TEXT_D      = "#555578"

PRIO = {
    "High":   {"color": "#FF6B9D", "bg": "#2D1A25"},
    "Medium": {"color": "#FFD166", "bg": "#2D2710"},
    "Low":    {"color": "#06D6A0", "bg": "#0D2520"},
}

CAT_META = {
    "Today":    ("☀️", "#FFD166", "#2D2710"),
    "Planned":  ("🗓️", "#7C6FFF", "#1A1830"),
    "Personal": ("🙂", "#00D4AA", "#0D2520"),
    "Work":     ("💼", "#9B8FFF", "#1A1830"),
    "Shopping": ("🛍️", "#FF6B9D", "#2D1A25"),
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def cat_icon(label):
    m = CAT_META.get(label)
    return m[0] if m else "📋"

def cat_color(label):
    m = CAT_META.get(label)
    return (m[0], m[1], m[2]) if m else ("📋", ACCENT, SURFACE2)


# ─── Reusable Widgets ─────────────────────────────────────────────────────────

class PillButton(ctk.CTkButton):
    """Small pill-shaped toggle-style button used for priority and filter selection."""
    def __init__(self, master, text, is_active=False,
                 active_fg=TEXT, active_bg=ACCENT,
                 inactive_fg=TEXT_M, inactive_bg=SURFACE3,
                 command=None, **kwargs):
        self.active_fg   = active_fg
        self.active_bg   = active_bg
        self.inactive_fg = inactive_fg
        self.inactive_bg = inactive_bg
        super().__init__(
            master, text=text, corner_radius=20,
            fg_color=active_bg if is_active else inactive_bg,
            hover_color=ACCENT_H if is_active else SURFACE2,
            text_color=active_fg if is_active else inactive_fg,
            border_width=0, height=30,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=command, **kwargs
        )
        self._active = is_active

    def set_active(self, active):
        self._active = active
        self.configure(
            fg_color=self.active_bg if active else self.inactive_bg,
            hover_color=ACCENT_H if active else SURFACE2,
            text_color=self.active_fg if active else self.inactive_fg,
        )


class SectionLabel(ctk.CTkLabel):
    def __init__(self, master, text, **kwargs):
        super().__init__(master, text=text.upper(),
                         font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                         text_color=TEXT_D, **kwargs)


class TaskCard(ctk.CTkFrame):
    """A single task row card with checkbox, labels, priority pill, and actions."""

    def __init__(self, master, task, on_toggle, on_edit, on_delete,
                 show_category=False, **kwargs):
        super().__init__(master, corner_radius=12, fg_color=SURFACE,
                         border_width=1, border_color=BORDER, **kwargs)
        self.task = task

        p_cfg = PRIO.get(task.priority, PRIO["Medium"])

        # Left accent strip (priority colour)
        strip = ctk.CTkFrame(self, width=4, corner_radius=0,
                             fg_color=p_cfg["color"])
        strip.pack(side="left", fill="y")

        # Checkbox
        self._var = ctk.BooleanVar(value=task.completed)
        chk = ctk.CTkCheckBox(
            self, variable=self._var,
            text="",
            width=24, height=24,
            checkbox_width=22, checkbox_height=22,
            corner_radius=6,
            fg_color=TEAL, hover_color=TEAL_H,
            border_color=BORDER,
            command=lambda: on_toggle(task.id),
        )
        chk.pack(side="left", padx=(10, 8), pady=14)

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, pady=10)

        title_font = ctk.CTkFont(family="Segoe UI", size=13,
                                  weight="bold" if not task.completed else "normal",
                                  overstrike=task.completed)
        title_color = TEXT_M if task.completed else TEXT
        ctk.CTkLabel(content, text=task.title, font=title_font,
                     text_color=title_color, anchor="w").pack(fill="x")

        # Meta row
        meta = ctk.CTkFrame(content, fg_color="transparent")
        meta.pack(fill="x", pady=(3, 0))

        # Priority pill
        ctk.CTkLabel(meta, text=f" {task.priority} ",
                     font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color=p_cfg["color"],
                     fg_color=p_cfg["bg"],
                     corner_radius=6, width=0).pack(side="left", padx=(0, 6))

        # Category chip (in search results)
        if show_category and task.category:
            ctk.CTkLabel(meta, text=f" {task.category} ",
                         font=ctk.CTkFont(family="Segoe UI", size=9),
                         text_color=TEXT_M, fg_color=SURFACE3,
                         corner_radius=6, width=0).pack(side="left", padx=(0, 6))

        # Due date
        if task.due_date:
            today = datetime.now().strftime("%Y-%m-%d")
            overdue = task.due_date < today and not task.completed
            due_color = ROSE if overdue else TEXT_M
            ctk.CTkLabel(meta, text=f"📅 {task.due_date}",
                         font=ctk.CTkFont(family="Segoe UI", size=9),
                         text_color=due_color,
                         fg_color="transparent").pack(side="left")

        # Right action buttons
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(side="right", padx=10)

        edit_btn = ctk.CTkButton(
            actions, text="✏", width=30, height=30,
            corner_radius=8, font=ctk.CTkFont(size=13),
            fg_color="transparent", hover_color=SURFACE3,
            text_color=TEXT_M, border_width=0,
            command=lambda: on_edit(task),
        )
        edit_btn.pack(side="left", padx=2)

        del_btn = ctk.CTkButton(
            actions, text="✕", width=30, height=30,
            corner_radius=8, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="transparent", hover_color="#2D1A25",
            text_color=TEXT_D, border_width=0,
            command=lambda: on_delete(task.id),
        )
        del_btn.pack(side="left", padx=2)


class CategoryCard(ctk.CTkFrame):
    """Dashboard category row card."""

    def __init__(self, master, cat, count, on_click, on_delete=None, **kwargs):
        super().__init__(master, corner_radius=14, fg_color=SURFACE,
                         border_width=1, border_color=BORDER,
                         cursor="hand2", **kwargs)
        self.bind("<Button-1>", lambda e: on_click(cat))

        icon_txt, icon_color, icon_bg = cat_color(cat["label"])
        icon_txt = cat.get("icon", cat_icon(cat["label"]))

        # Icon chip
        chip = ctk.CTkFrame(self, width=48, height=48, corner_radius=12,
                            fg_color=cat.get("bg", icon_bg))
        chip.pack(side="left", padx=(14, 12), pady=14)
        chip.pack_propagate(False)
        chip.bind("<Button-1>", lambda e: on_click(cat))

        icon_lbl = ctk.CTkLabel(chip, text=icon_txt,
                                font=ctk.CTkFont(family="Segoe UI Emoji", size=20),
                                fg_color="transparent", text_color=cat.get("color", ACCENT))
        icon_lbl.pack(expand=True)
        icon_lbl.bind("<Button-1>", lambda e: on_click(cat))

        # Text
        txt = ctk.CTkFrame(self, fg_color="transparent")
        txt.pack(side="left", fill="y", pady=14)
        txt.bind("<Button-1>", lambda e: on_click(cat))

        name_lbl = ctk.CTkLabel(txt, text=cat["label"],
                                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                                text_color=TEXT, anchor="w")
        name_lbl.pack(anchor="w")
        name_lbl.bind("<Button-1>", lambda e: on_click(cat))

        count_lbl = ctk.CTkLabel(txt, text=f"{count} task{'s' if count != 1 else ''}",
                                 font=ctk.CTkFont(family="Segoe UI", size=10),
                                 text_color=TEXT_M, anchor="w")
        count_lbl.pack(anchor="w")
        count_lbl.bind("<Button-1>", lambda e: on_click(cat))

        # Right side: badge + optional delete
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", padx=12)

        if count > 0:
            badge = ctk.CTkLabel(right, text=str(count), width=28, height=28,
                                 corner_radius=14, fg_color=ACCENT,
                                 font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                                 text_color="white")
            badge.pack(side="left", padx=(0, 8))

        if on_delete:
            del_lbl = ctk.CTkButton(right, text="✕", width=28, height=28,
                                    corner_radius=8,
                                    fg_color="transparent", hover_color="#2D1A25",
                                    text_color=TEXT_D, border_width=0,
                                    font=ctk.CTkFont(size=12, weight="bold"),
                                    command=lambda: on_delete(cat))
            del_lbl.pack(side="left")


# ─── Modal Dialogs ────────────────────────────────────────────────────────────

class BaseModal(ctk.CTkToplevel):
    def __init__(self, parent, title="", width=400, height=320):
        super().__init__(parent)
        self.title(title)
        self.configure(fg_color=SURFACE)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center over parent
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - width)  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

        # Header
        hdr = ctk.CTkFrame(self, fg_color=SURFACE2, corner_radius=0, height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text=title,
                     font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                     text_color=TEXT).pack(side="left", padx=20, pady=14)

        ctk.CTkButton(hdr, text="✕", width=32, height=32, corner_radius=8,
                      fg_color="transparent", hover_color="#2D1A25",
                      text_color=TEXT_M, border_width=0,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.destroy).pack(side="right", padx=16, pady=11)

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x")

        # Body
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=22, pady=18)

        self.bind("<Escape>", lambda e: self.destroy())

    def _field_label(self, text):
        ctk.CTkLabel(self.body, text=text.upper(),
                     font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color=TEXT_D, anchor="w").pack(fill="x", pady=(10, 4))

    def _entry(self, var=None, placeholder=""):
        ent = ctk.CTkEntry(
            self.body, textvariable=var or tk.StringVar(master=_ROOT),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=SURFACE3, border_color=BORDER,
            text_color=TEXT, placeholder_text=placeholder,
            placeholder_text_color=TEXT_D,
            corner_radius=8, border_width=1, height=40,
        )
        ent.pack(fill="x")
        return ent

    def _btn_row(self, cancel_text="Cancel", ok_text="Save",
                 ok_color=ACCENT, on_ok=None):
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", pady=(18, 0), side="bottom")

        ctk.CTkButton(row, text=cancel_text, corner_radius=10,
                      fg_color=SURFACE3, hover_color=SURFACE2,
                      text_color=TEXT_M, border_width=0,
                      font=ctk.CTkFont(family="Segoe UI", size=11),
                      width=100, height=38,
                      command=self.destroy).pack(side="left")

        ctk.CTkButton(row, text=ok_text, corner_radius=10,
                      fg_color=ok_color, hover_color=ACCENT_H,
                      text_color="white", border_width=0,
                      font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                      width=140, height=38,
                      command=on_ok or (lambda: None)).pack(side="right")


class NewListModal(BaseModal):
    def __init__(self, parent, on_submit):
        super().__init__(parent, title="✦  Create New List", width=380, height=220)
        self.on_submit = on_submit
        self._field_label("List Name")
        self.var = tk.StringVar(master=_ROOT)
        ent = self._entry(self.var, placeholder="e.g. Health, Finance…")
        ent.focus()
        ent.bind("<Return>", lambda e: self._submit())
        self._btn_row(ok_text="Create List", on_ok=self._submit)

    def _submit(self):
        v = self.var.get().strip()
        if v:
            self.on_submit(v)
        self.destroy()


class ConfirmModal(BaseModal):
    def __init__(self, parent, message, on_confirm):
        super().__init__(parent, title="⚠  Confirm", width=380, height=190)
        self._on_confirm = on_confirm
        ctk.CTkLabel(self.body, text=message, wraplength=330,
                     font=ctk.CTkFont(family="Segoe UI", size=11),
                     text_color=TEXT, justify="left", anchor="w").pack(fill="x")
        self._btn_row(ok_text="Delete", ok_color=ROSE,
                      on_ok=self._confirm)

    def _confirm(self):
        if self._on_confirm:
            self._on_confirm()
        self.destroy()


class TaskModal(BaseModal):
    def __init__(self, parent, manager, category="Personal", task=None, on_save=None):
        title = "✏  Edit Task" if task else "✦  New Task"
        super().__init__(parent, title=title, width=410, height=500)
        self.manager = manager
        self.task = task
        self.on_save = on_save
        self._selected_prio = task.priority if task else "Medium"

        # Title
        self._field_label("Task Title")
        self.title_var = tk.StringVar(master=_ROOT, value=task.title if task else "")
        title_ent = self._entry(self.title_var, placeholder="What needs to be done?")
        title_ent.focus()

        # Priority pills
        self._field_label("Priority")
        prow = ctk.CTkFrame(self.body, fg_color="transparent")
        prow.pack(fill="x", pady=(0, 4))
        self._prio_btns = {}
        for p in ["Low", "Medium", "High"]:
            cfg = PRIO[p]
            b = PillButton(prow, text=f"● {p}",
                           is_active=(p == self._selected_prio),
                           active_fg="white", active_bg=cfg["color"],
                           inactive_fg=cfg["color"], inactive_bg=cfg["bg"],
                           width=90,
                           command=lambda pv=p: self._pick_prio(pv))
            b.pack(side="left", padx=(0, 8))
            self._prio_btns[p] = b

        # Category
        self._field_label("Category")
        default = category if category not in ("Today", "Planned") else "Personal"
        self.cat_var = tk.StringVar(master=_ROOT, value=task.category if task else default)
        cat_dd = ctk.CTkOptionMenu(
            self.body, variable=self.cat_var,
            values=manager.all_categories(),
            fg_color=SURFACE3, button_color=SURFACE2,
            button_hover_color=BORDER,
            text_color=TEXT, dropdown_fg_color=SURFACE2,
            dropdown_hover_color=SURFACE3,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            corner_radius=8, height=40,
        )
        cat_dd.pack(fill="x")

        # Due date
        self._field_label("Due Date")
        default_due = ""
        if not task and category in ("Today", "Planned"):
            default_due = datetime.now().strftime("%Y-%m-%d")
        elif task:
            default_due = task.due_date or ""
        self.due_var = tk.StringVar(master=_ROOT, value=default_due)
        self._entry(self.due_var, placeholder="YYYY-MM-DD (optional)")

        # Date presets
        preset_row = ctk.CTkFrame(self.body, fg_color="transparent")
        preset_row.pack(fill="x", pady=(6, 0))
        today_s = datetime.now().strftime("%Y-%m-%d")
        tom_s   = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        for lbl, val in [("Today", today_s), ("Tomorrow", tom_s), ("Clear", "")]:
            ctk.CTkButton(preset_row, text=lbl, width=80, height=26,
                          corner_radius=8,
                          fg_color=SURFACE3, hover_color=SURFACE2,
                          text_color=TEXT_M, border_width=0,
                          font=ctk.CTkFont(size=10),
                          command=lambda v=val: self.due_var.set(v)).pack(side="left", padx=(0, 6))

        self._btn_row(ok_text="Save Task", ok_color=TEAL, on_ok=self._save)
        title_ent.bind("<Return>", lambda e: self._save())

    def _pick_prio(self, p):
        self._selected_prio = p
        for pv, btn in self._prio_btns.items():
            btn.set_active(pv == p)

    def _save(self):
        t = self.title_var.get().strip()
        if not t:
            return
        try:
            if self.task:
                self.manager.edit_task(self.task.id, title=t,
                                       category=self.cat_var.get(),
                                       priority=self._selected_prio,
                                       due_date=self.due_var.get().strip())
            else:
                self.manager.add_task(title=t, category=self.cat_var.get(),
                                      priority=self._selected_prio,
                                      due_date=self.due_var.get().strip())
        except TaskManagerError:
            return
        if self.on_save:
            self.on_save()
        self.destroy()


class AboutModal(BaseModal):
    def __init__(self, parent):
        super().__init__(parent, title="✦  About Taskly", width=360, height=280)
        ctk.CTkLabel(self.body, text="🚀", font=ctk.CTkFont(size=44),
                     fg_color="transparent").pack(pady=(0, 8))
        ctk.CTkLabel(self.body, text="Taskly — Advanced Task Manager",
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=TEXT).pack()
        ctk.CTkLabel(self.body, text="v3.0  ·  CustomTkinter Edition",
                     font=ctk.CTkFont(family="Segoe UI", size=10),
                     text_color=TEXT_M).pack(pady=(4, 14))
        ctk.CTkLabel(self.body,
                     text="A beautiful, professional desktop task manager.\n"
                          "Categories · Priorities · Live Search · JSON Persistence.",
                     font=ctk.CTkFont(family="Segoe UI", size=10),
                     text_color=TEXT_D, justify="center").pack()
        ctk.CTkButton(self.body, text="Awesome ✓", width=120, height=36,
                      corner_radius=10, fg_color=ACCENT, hover_color=ACCENT_H,
                      text_color="white",
                      font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                      command=self.destroy).pack(pady=16)


# ─── Main App Window ──────────────────────────────────────────────────────────

class TasklyApp(ctk.CTk):

    def __init__(self, user_name="Ender"):
        super().__init__()
        self.title("Taskly — Advanced Task Manager")
        self.geometry("460x780")
        self.minsize(420, 620)
        self.configure(fg_color=BG)

        # Set module-level root for StringVar master
        global _ROOT
        _ROOT = self

        self.manager     = TaskManager(filepath="data/tasks.json")
        self.user_name   = user_name
        self.active_cat  = None
        self.filter_tab  = "All"
        self.search_q    = ""

        self._frame = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self._frame.pack(fill="both", expand=True)

        if not self.manager.onboarded:
            self._show_onboarding()
        else:
            self._show_dashboard()

    # ─── helpers ─────────────────────────────────────────────────────────
    def _clear(self):
        for w in self._frame.winfo_children():
            w.destroy()

    def _scrollable(self, parent, corner_radius=0):
        sf = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                    corner_radius=corner_radius,
                                    scrollbar_button_color=SURFACE3,
                                    scrollbar_button_hover_color=BORDER)
        sf.pack(fill="both", expand=True, padx=14, pady=(6, 14))
        return sf

    # ─── ONBOARDING ───────────────────────────────────────────────────────
    def _show_onboarding(self):
        self._clear()
        root = ctk.CTkFrame(self._frame, fg_color=BG, corner_radius=0)
        root.pack(fill="both", expand=True)

        ctk.CTkFrame(root, fg_color="transparent", height=70).pack()

        # Icon circle
        circle = ctk.CTkFrame(root, width=160, height=160, corner_radius=80,
                              fg_color=SURFACE2, border_width=2, border_color=ACCENT)
        circle.pack(pady=10)
        circle.pack_propagate(False)
        ctk.CTkLabel(circle, text="🗂️",
                     font=ctk.CTkFont(family="Segoe UI Emoji", size=60),
                     fg_color="transparent").pack(expand=True)

        ctk.CTkLabel(root, text="Stay Organized.\nStay Focused.",
                     font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                     text_color=TEXT, justify="center").pack(pady=(28, 10))

        ctk.CTkLabel(root,
                     text="Taskly is your personal productivity hub.\n"
                          "Tasks, priorities, smart lists — all in one place.",
                     font=ctk.CTkFont(family="Segoe UI", size=12),
                     text_color=TEXT_M, justify="center").pack(padx=40, pady=(0, 40))

        ctk.CTkButton(root, text="Get Started →", corner_radius=24,
                      fg_color=ACCENT, hover_color=ACCENT_H,
                      text_color="white", border_width=0,
                      font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                      width=200, height=50,
                      command=self._complete_onboarding).pack()

    def _complete_onboarding(self):
        self.manager.mark_onboarded()
        self._show_dashboard()

    # ─── DASHBOARD ────────────────────────────────────────────────────────
    def _show_dashboard(self):
        self._clear()
        self.active_cat = None

        root = ctk.CTkFrame(self._frame, fg_color=BG, corner_radius=0)
        root.pack(fill="both", expand=True)

        # ── Header bar ──
        hdr = ctk.CTkFrame(root, fg_color=SURFACE2, corner_radius=0, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        top = ctk.CTkFrame(hdr, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=12)

        menu_btn = ctk.CTkButton(top, text="☰", width=36, height=36,
                                 corner_radius=10,
                                 fg_color="transparent", hover_color=SURFACE3,
                                 text_color=TEXT_M, border_width=0,
                                 font=ctk.CTkFont(size=18, weight="bold"),
                                 command=lambda: AboutModal(self))
        menu_btn.pack(side="left")

        ctk.CTkLabel(top, text="Taskly",
                     font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                     text_color=TEXT).pack(side="left", padx=10)

        # Avatar pill
        av_frame = ctk.CTkFrame(top, width=36, height=36, corner_radius=18,
                                fg_color=ACCENT)
        av_frame.pack(side="right")
        av_frame.pack_propagate(False)
        ctk.CTkLabel(av_frame,
                     text=self.user_name[:1].upper(),
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color="white").pack(expand=True)

        # ── Greeting ──
        stats = self.manager.stats()
        today_ct = stats.get("Today", 0)
        all_tasks = self.manager.tasks
        total = len(all_tasks)
        done  = sum(1 for t in all_tasks if t.completed)

        greet_panel = ctk.CTkFrame(root, fg_color="transparent")
        greet_panel.pack(fill="x", padx=20, pady=(18, 4))

        hour = datetime.now().hour
        greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
        ctk.CTkLabel(greet_panel, text=f"{greet}, {self.user_name} 👋",
                     font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
                     text_color=TEXT, anchor="w").pack(fill="x")

        sub = (f"You have {today_ct} task{'s' if today_ct != 1 else ''} due today."
               if today_ct else "Nothing due today — enjoy the calm! 🎉")
        ctk.CTkLabel(greet_panel, text=sub,
                     font=ctk.CTkFont(family="Segoe UI", size=11),
                     text_color=TEXT_M, anchor="w").pack(fill="x", pady=(2, 0))

        # ── Stats strip ──
        stats_row = ctk.CTkFrame(root, fg_color=SURFACE, corner_radius=14)
        stats_row.pack(fill="x", padx=14, pady=(12, 0))

        for label, val, color in [
            (str(total), "Total Tasks", TEXT),
            (str(done),  "Completed",   GREEN),
            (str(total-done), "Pending", GOLD),
        ]:
            col = ctk.CTkFrame(stats_row, fg_color="transparent")
            col.pack(side="left", expand=True, padx=10, pady=12)
            ctk.CTkLabel(col, text=label,
                         font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                         text_color=color).pack()
            ctk.CTkLabel(col, text=val,
                         font=ctk.CTkFont(family="Segoe UI", size=9),
                         text_color=TEXT_D).pack()

        # Progress bar under stats
        pct = int((done / total) * 100) if total else 0
        _pb = ctk.CTkProgressBar(root, progress_color=TEAL, fg_color=SURFACE3,
                                 corner_radius=4, height=6)
        _pb.pack(fill="x", padx=14, pady=(2, 0))
        _pb.set(pct / 100)

        # ── Search bar ──
        self._search_var = tk.StringVar(master=_ROOT, value=self.search_q)
        search_ent = ctk.CTkEntry(
            root, textvariable=self._search_var,
            placeholder_text="🔍  Search tasks…",
            placeholder_text_color=TEXT_D,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color=SURFACE3, border_color=BORDER,
            text_color=TEXT, corner_radius=10, height=40, border_width=1,
        )
        search_ent.pack(fill="x", padx=14, pady=(12, 4))
        search_ent.bind("<KeyRelease>", self._on_search)

        # ── Scrollable category list ──
        sf = self._scrollable(root)

        SectionLabel(sf, "My Lists").pack(anchor="w", pady=(4, 8))

        if self.search_q.strip():
            self._build_search_results(sf)
        else:
            for cat in self.manager.get_categories():
                count = stats.get(cat["label"], 0)
                is_custom = "smart" not in cat and cat["label"] not in ("Personal","Work","Shopping")
                CategoryCard(
                    sf, cat=cat, count=count,
                    on_click=self._show_cat_detail,
                    on_delete=self._confirm_del_cat if is_custom else None,
                ).pack(fill="x", pady=4)

            # Add list button
            add_btn = ctk.CTkButton(sf, text="+ Create New List",
                                    corner_radius=12,
                                    fg_color=SURFACE, hover_color=SURFACE2,
                                    border_color=BORDER, border_width=1,
                                    text_color=TEAL, height=50,
                                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                    command=self._open_new_list)
            add_btn.pack(fill="x", pady=(8, 4))

    def _on_search(self, e):
        self.search_q = self._search_var.get()
        self._show_dashboard()

    def _build_search_results(self, parent):
        results = self.manager.search(self.search_q)
        ctk.CTkLabel(parent,
                     text=f"Search results · {len(results)} found",
                     font=ctk.CTkFont(family="Segoe UI", size=10),
                     text_color=TEXT_M).pack(anchor="w", pady=(0, 8))
        if not results:
            ctk.CTkLabel(parent, text="No tasks match that search.",
                         font=ctk.CTkFont(size=11), text_color=TEXT_D).pack(pady=30)
            return
        for t in results:
            TaskCard(parent, t,
                     on_toggle=self._toggle_task,
                     on_edit=self._open_task_modal,
                     on_delete=self._confirm_del_task,
                     show_category=True).pack(fill="x", pady=4)

    def _open_new_list(self):
        NewListModal(self, on_submit=self._create_cat)

    def _create_cat(self, name):
        try:
            self.manager.add_category(name)
            self._show_dashboard()
        except TaskManagerError:
            pass

    def _confirm_del_cat(self, cat):
        ConfirmModal(self,
                     message=f"Delete '{cat['label']}' and all its tasks?",
                     on_confirm=lambda: (
                         self.manager.delete_category(cat["label"]),
                         self._show_dashboard()
                     ))

    # ─── CATEGORY DETAIL ────────────────────────────────────────────────────
    def _show_cat_detail(self, cat):
        self._clear()
        self.active_cat = cat

        root = ctk.CTkFrame(self._frame, fg_color=BG, corner_radius=0)
        root.pack(fill="both", expand=True)

        # Header
        accent_fg, accent_bg = cat.get("color", ACCENT), cat.get("bg", SURFACE2)

        hdr = ctk.CTkFrame(root, fg_color=SURFACE2, corner_radius=0, height=120)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        top = ctk.CTkFrame(hdr, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 0))

        back = ctk.CTkButton(top, text="← Back", width=80, height=32,
                             corner_radius=8,
                             fg_color="transparent", hover_color=SURFACE3,
                             text_color=TEXT_M, border_width=0,
                             font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                             command=self._show_dashboard)
        back.pack(side="left")

        dots = ctk.CTkButton(top, text="⋮", width=32, height=32,
                             corner_radius=8,
                             fg_color="transparent", hover_color=SURFACE3,
                             text_color=TEXT_M, border_width=0,
                             font=ctk.CTkFont(size=18, weight="bold"),
                             command=lambda: self._cat_menu())
        dots.pack(side="right")

        # Category identity
        id_row = ctk.CTkFrame(hdr, fg_color="transparent")
        id_row.pack(fill="x", padx=16, pady=(8, 0))

        chip = ctk.CTkFrame(id_row, width=44, height=44, corner_radius=12,
                            fg_color=cat.get("bg", SURFACE3))
        chip.pack(side="left", padx=(0, 12))
        chip.pack_propagate(False)
        ctk.CTkLabel(chip, text=cat.get("icon", "📋"),
                     font=ctk.CTkFont(family="Segoe UI Emoji", size=20),
                     text_color=cat.get("color", ACCENT),
                     fg_color="transparent").pack(expand=True)

        info = ctk.CTkFrame(id_row, fg_color="transparent")
        info.pack(side="left")

        tasks = self.manager.list_by_category(cat["label"])
        pending = sum(1 for t in tasks if not t.completed)
        ctk.CTkLabel(info, text=cat["label"],
                     font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
                     text_color=TEXT, anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text=f"{pending} pending · {len(tasks)} total",
                     font=ctk.CTkFont(family="Segoe UI", size=10),
                     text_color=TEXT_M, anchor="w").pack(anchor="w")

        # Filter tab bar
        tab_row = ctk.CTkFrame(root, fg_color=SURFACE2, corner_radius=0, height=44)
        tab_row.pack(fill="x")
        tab_row.pack_propagate(False)

        inner_tab = ctk.CTkFrame(tab_row, fg_color="transparent")
        inner_tab.pack(side="left", padx=14, pady=7)

        self._tab_btns = {}
        for tab in ("All", "Active", "Completed"):
            is_a = (self.filter_tab == tab)
            b = PillButton(inner_tab, text=tab, is_active=is_a,
                           width=85, command=lambda t=tab: self._set_filter(t))
            b.pack(side="left", padx=(0, 6))
            self._tab_btns[tab] = b

        ctk.CTkFrame(root, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x")

        # Task list
        sf = self._scrollable(root)

        filtered = tasks
        if self.filter_tab == "Active":
            filtered = [t for t in tasks if not t.completed]
        elif self.filter_tab == "Completed":
            filtered = [t for t in tasks if t.completed]

        if not filtered:
            ctk.CTkLabel(sf,
                         text=f"No {self.filter_tab.lower()} tasks.\nTap '+' to add one.",
                         font=ctk.CTkFont(family="Segoe UI", size=11),
                         text_color=TEXT_D, justify="center").pack(pady=60)
        else:
            order = {"High": 0, "Medium": 1, "Low": 2}
            filtered.sort(key=lambda t: (
                t.completed,
                order.get(t.priority, 1),
                t.due_date or "9999-99-99",
            ))
            for t in filtered:
                TaskCard(sf, t,
                         on_toggle=self._toggle_task,
                         on_edit=self._open_task_modal,
                         on_delete=self._confirm_del_task).pack(fill="x", pady=4)

        # FAB
        fab = ctk.CTkButton(root, text="+", width=58, height=58,
                            corner_radius=29,
                            fg_color=TEAL, hover_color=TEAL_H,
                            text_color="white", border_width=0,
                            font=ctk.CTkFont(size=28, weight="bold"),
                            command=self._open_task_modal)
        fab.place(relx=1.0, rely=1.0, x=-22, y=-22, anchor="se")

    def _set_filter(self, f):
        self.filter_tab = f
        if self.active_cat:
            self._show_cat_detail(self.active_cat)

    def _cat_menu(self):
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0,
                       bg=SURFACE2, fg=TEXT,
                       activebackground=ACCENT, activeforeground="white",
                       font=("Segoe UI", 10))
        menu.add_command(label="Clear Completed", command=self._clear_completed)
        x = self.winfo_rootx() + self.winfo_width() - 160
        y = self.winfo_rooty() + 120
        menu.post(x, y)

    def _clear_completed(self):
        if not self.active_cat:
            return
        tasks = self.manager.list_by_category(self.active_cat["label"])
        for t in [t for t in tasks if t.completed]:
            self.manager.delete_task(t.id)
        self._show_cat_detail(self.active_cat)

    # ─── Task CRUD ───────────────────────────────────────────────────────────
    def _toggle_task(self, task_id):
        try:
            self.manager.toggle_task(task_id)
            self._refresh()
        except TaskManagerError:
            pass

    def _confirm_del_task(self, task_id):
        ConfirmModal(self, message="Delete this task? This cannot be undone.",
                     on_confirm=lambda: self._delete_task(task_id))

    def _delete_task(self, task_id):
        try:
            self.manager.delete_task(task_id)
            self._refresh()
        except TaskManagerError:
            pass

    def _open_task_modal(self, task=None):
        cat = self.active_cat["label"] if self.active_cat else "Personal"
        TaskModal(self, self.manager, category=cat, task=task, on_save=self._refresh)

    def _refresh(self):
        if self.active_cat:
            self._show_cat_detail(self.active_cat)
        else:
            self._show_dashboard()
