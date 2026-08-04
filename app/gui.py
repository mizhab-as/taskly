"""
gui.py
------
Premium dark-mode Tkinter GUI for Taskly — Advanced Task Manager.

Design language:
    * Deep navy/charcoal dark mode with vivid accent colors
    * Glassmorphism-style cards with layered depth
    * Smooth canvas-drawn custom widgets (checkboxes, pills, progress bars)
    * Zero native system dialogs — all custom-drawn modal sheets
    * Mobile-inspired vertical layout with full-width card rows
    * Animated hover states and interactive affordances
"""

import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime, timedelta

from app.task_manager import TaskManager, TaskManagerError
from app.models import Task, PRIORITIES

# ─────────────────────────────────────────────────────────────
#  DESIGN SYSTEM — Dark-mode premium palette
# ─────────────────────────────────────────────────────────────
BG          = "#0F0F1A"   # Deep navy background
SURFACE     = "#1A1A2E"   # Card surface
SURFACE2    = "#16213E"   # Slightly elevated surface
SURFACE3    = "#0D1B2A"   # Sunken / input background
BORDER      = "#2A2A45"   # Subtle border
BORDER2     = "#3A3A5C"   # Highlighted border

ACCENT      = "#6C63FF"   # Primary vivid violet
ACCENT_DIM  = "#4A45B0"   # Pressed / dimmed violet
ACCENT_GLOW = "#8B85FF"   # Hover glow violet

TEAL        = "#00D4AA"   # Secondary teal
TEAL_DIM    = "#00A882"   # Pressed teal
TEAL_GLOW   = "#33DDBB"   # Hover teal

GOLD        = "#FFD166"   # Warning / due-date highlight
ROSE        = "#FF6B9D"   # Danger / overdue
GREEN       = "#06D6A0"   # Completed / success

TEXT        = "#E8E8F8"   # Primary text
TEXT_MUTED  = "#8888AA"   # Secondary / muted text
TEXT_DIM    = "#555578"   # Disabled / placeholder text

# Priority config
PRIORITY_CONFIG = {
    "High":   {"color": "#FF6B9D", "bg": "#2D1A25", "pill_bg": "#FF6B9D22", "dot": "#FF6B9D"},
    "Medium": {"color": "#FFD166", "bg": "#2D2710", "pill_bg": "#FFD16622", "dot": "#FFD166"},
    "Low":    {"color": "#06D6A0", "bg": "#0D2520", "pill_bg": "#06D6A022", "dot": "#06D6A0"},
}

# Category icon + palette map for built-in categories
CAT_PALETTE = {
    "Today":    {"icon": "☀", "color": "#FFD166", "bg": "#2D2710"},
    "Planned":  {"icon": "🗓", "color": "#6C63FF", "bg": "#1A1830"},
    "Personal": {"icon": "🙂", "color": "#00D4AA", "bg": "#0D2520"},
    "Work":     {"icon": "💼", "color": "#8B85FF", "bg": "#1A1830"},
    "Shopping": {"icon": "🛍", "color": "#FF6B9D", "bg": "#2D1A25"},
}


def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def blend(c1, c2, t=0.5):
    """Linear interpolate between two hex colors."""
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ─────────────────────────────────────────────────────────────
#  ATOMIC WIDGETS
# ─────────────────────────────────────────────────────────────

class GlowButton(tk.Canvas):
    """Rounded-rectangle button with solid fill and hover glow."""

    def __init__(self, parent, text="", bg_color=ACCENT, fg_color=TEXT,
                 hover_color=None, command=None, width=120, height=36,
                 radius=10, font_size=10, bold=True, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=SURFACE, highlightthickness=0, cursor="hand2", **kwargs)
        self.text = text
        self.bg_normal = bg_color
        self.bg_hover = hover_color or blend(bg_color, "#ffffff", 0.15)
        self.fg = fg_color
        self.command = command
        self.radius = radius
        self.w = width
        self.h = height
        self.font_size = font_size
        self.bold = bold
        self.hovered = False

        self.draw(self.bg_normal)
        self.bind("<Enter>",    self._on_enter)
        self.bind("<Leave>",    self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [
            x1+r, y1,  x2-r, y1,
            x2,   y1,  x2,   y1+r,
            x2,   y1+r, x2,  y2-r,
            x2,   y2,   x2-r, y2,
            x2-r, y2,   x1+r, y2,
            x1,   y2,   x1,   y2-r,
            x1,   y2-r, x1,   y1+r,
            x1,   y1,   x1+r, y1,
        ]
        return self.create_polygon(pts, smooth=True, **kw)

    def draw(self, fill):
        self.delete("all")
        # Background fill
        self._rounded_rect(2, 2, self.w-2, self.h-2, self.radius,
                           fill=fill, outline="")
        # Label
        wt = "bold" if self.bold else "normal"
        self.create_text(self.w//2, self.h//2, text=self.text,
                         font=("Segoe UI", self.font_size, wt), fill=self.fg)

    def _on_enter(self, e):
        self.draw(self.bg_hover)

    def _on_leave(self, e):
        self.draw(self.bg_normal)

    def _on_click(self, e):
        self.draw(self.bg_normal)
        if self.command:
            self.command()


class RoundedFrame(tk.Canvas):
    """A canvas-drawn rounded rectangle that acts as a styled card container."""

    def __init__(self, parent, width, height, bg_fill=SURFACE, border_color=BORDER,
                 radius=14, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=BG, highlightthickness=0, **kwargs)
        self.fill = bg_fill
        self.border_color = border_color
        self.radius = radius
        self._draw()

    def _draw(self):
        w = int(self["width"])
        h = int(self["height"])
        r = self.radius
        pts = [r,0, w-r,0, w,0, w,r, w,r, w,h-r, w,h, w-r,h, w-r,h, r,h, 0,h, 0,h-r, 0,h-r, 0,r, 0,0, r,0]
        self.create_polygon(pts, smooth=True, fill=self.fill, outline=self.border_color, width=1)


class PremiumCheckbox(tk.Canvas):
    """Animated custom checkbox with gradient-fill and check glyph."""

    def __init__(self, parent, checked=False, command=None, size=24, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=SURFACE, highlightthickness=0, cursor="hand2", **kwargs)
        self.size = size
        self.checked = checked
        self.command = command
        self._draw()
        self.bind("<Button-1>", self._on_click)

    def _draw(self):
        self.delete("all")
        s = self.size
        pad = 2
        if self.checked:
            self.create_oval(pad, pad, s-pad, s-pad, fill=TEAL, outline=TEAL_DIM, width=1.5)
            # Checkmark
            cx, cy = s/2, s/2
            self.create_line(cx-5, cy, cx-1, cy+4, cx+6, cy-5,
                             fill="white", width=2.5, capstyle="round", joinstyle="round")
        else:
            self.create_oval(pad, pad, s-pad, s-pad,
                             fill=SURFACE3, outline=BORDER2, width=1.5)

    def toggle(self):
        self.checked = not self.checked
        self._draw()

    def _on_click(self, e):
        self.toggle()
        if self.command:
            self.command(self.checked)

    def set_bg(self, color):
        self.config(bg=color)
        self._draw()


class FAB(tk.Canvas):
    """Premium floating action button with glow ring."""

    def __init__(self, parent, command=None, size=56, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=BG, highlightthickness=0, cursor="hand2", **kwargs)
        self.command = command
        self.size = size
        self._draw(False)
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>",    lambda e: self._draw(True))
        self.bind("<Leave>",    lambda e: self._draw(False))

    def _draw(self, hovered):
        self.delete("all")
        s = self.size
        pad = 4
        # Outer glow ring when hovered
        if hovered:
            self.create_oval(0, 0, s, s, fill="", outline=TEAL_GLOW, width=2)
        # Main fill
        self.create_oval(pad, pad, s-pad, s-pad, fill=TEAL, outline="")
        self.create_text(s//2, s//2-1, text="+",
                         font=("Segoe UI", 28, "bold"), fill="white")

    def _click(self, e):
        if self.command:
            self.command()


# ─────────────────────────────────────────────────────────────
#  MODAL LAYER — Custom dark themed dialogs
# ─────────────────────────────────────────────────────────────

class DarkModal(tk.Toplevel):
    """Base dark-mode modal with rounded header and escape-to-close."""

    def __init__(self, parent, title="", width=380, height=300):
        super().__init__(parent)
        self.parent = parent
        self.configure(bg=SURFACE)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Center over parent
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - width)  // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

        # Header bar
        hdr = tk.Frame(self, bg=SURFACE2, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text=title, font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=SURFACE2).pack(side="left", padx=18, pady=14)

        close = tk.Label(hdr, text="✕", font=("Segoe UI", 11),
                         fg=TEXT_MUTED, bg=SURFACE2, cursor="hand2")
        close.pack(side="right", padx=18, pady=14)
        close.bind("<Button-1>", lambda e: self.destroy())
        close.bind("<Enter>",    lambda e: close.config(fg=ROSE))
        close.bind("<Leave>",    lambda e: close.config(fg=TEXT_MUTED))

        # Divider
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Body frame
        self.body = tk.Frame(self, bg=SURFACE, padx=20, pady=18)
        self.body.pack(fill="both", expand=True)

        self.bind("<Escape>", lambda e: self.destroy())

    def _input(self, parent, placeholder="", var=None):
        """Returns a styled dark-mode Entry widget."""
        f = tk.Frame(parent, bg=SURFACE3, highlightthickness=1,
                     highlightbackground=BORDER, highlightcolor=ACCENT)
        ent = tk.Entry(f, textvariable=var or tk.StringVar(),
                       font=("Segoe UI", 11), bg=SURFACE3, fg=TEXT,
                       insertbackground=ACCENT, bd=0,
                       disabledbackground=SURFACE3)
        ent.pack(fill="x", padx=10, ipady=8)
        ent.bind("<FocusIn>",  lambda e: f.config(highlightbackground=ACCENT))
        ent.bind("<FocusOut>", lambda e: f.config(highlightbackground=BORDER))
        return f, ent

    def _label(self, parent, text):
        tk.Label(parent, text=text, font=("Segoe UI", 9, "bold"),
                 fg=TEXT_MUTED, bg=SURFACE).pack(anchor="w", pady=(10, 4))

    def _btn_row(self, parent, cancel_text="Cancel", ok_text="Save",
                 ok_color=ACCENT, on_ok=None):
        row = tk.Frame(parent, bg=SURFACE)
        row.pack(fill="x", pady=(16, 0), side="bottom")

        cancel = GlowButton(row, text=cancel_text, bg_color=SURFACE2,
                            hover_color=SURFACE3, fg_color=TEXT_MUTED,
                            width=100, height=36, command=self.destroy)
        cancel.pack(side="left")

        ok = GlowButton(row, text=ok_text, bg_color=ok_color,
                        width=140, height=36, command=on_ok or (lambda: None))
        ok.pack(side="right")
        return ok


class NewListModal(DarkModal):
    def __init__(self, parent, on_submit):
        super().__init__(parent, title="✦  Create New List", width=380, height=230)
        self.on_submit = on_submit

        self._label(self.body, "LIST NAME")
        self.name_var = tk.StringVar()
        frame, self.ent = self._input(self.body, var=self.name_var)
        frame.pack(fill="x")
        self.ent.focus_set()

        self._btn_row(self.body, ok_text="Create List",
                      ok_color=ACCENT, on_ok=self.submit)
        self.ent.bind("<Return>", lambda e: self.submit())

    def submit(self):
        val = self.name_var.get().strip()
        if val:
            self.on_submit(val)
        self.destroy()


class ConfirmModal(DarkModal):
    def __init__(self, parent, message, on_confirm, danger=True):
        super().__init__(parent, title="⚠  Confirm Action", width=380, height=200)
        self.on_confirm = on_confirm

        tk.Label(self.body, text=message, font=("Segoe UI", 10),
                 fg=TEXT, bg=SURFACE, wraplength=330,
                 justify="left").pack(anchor="w", pady=(0, 10))

        self._btn_row(self.body, ok_text="Delete",
                      ok_color=ROSE if danger else ACCENT,
                      on_ok=self._confirm)

    def _confirm(self):
        if self.on_confirm:
            self.on_confirm()
        self.destroy()


class TaskModal(DarkModal):
    """Full-featured task editor modal with pill priority selector."""

    def __init__(self, parent, manager: TaskManager, category="Personal",
                 task=None, on_save=None):
        title = "✏  Edit Task" if task else "✦  New Task"
        super().__init__(parent, title=title, width=400, height=490)
        self.manager = manager
        self.task = task
        self.on_save = on_save

        # Title
        self._label(self.body, "TASK TITLE")
        self.title_var = tk.StringVar(value=task.title if task else "")
        title_frame, self.title_ent = self._input(self.body, var=self.title_var)
        title_frame.pack(fill="x")
        self.title_ent.focus_set()

        # Priority Pills
        self._label(self.body, "PRIORITY")
        prio_row = tk.Frame(self.body, bg=SURFACE)
        prio_row.pack(fill="x", pady=(0, 4))

        self.selected_prio = task.priority if task else "Medium"
        self.prio_btns = {}
        for p in ["Low", "Medium", "High"]:
            cfg = PRIORITY_CONFIG[p]
            btn = tk.Label(prio_row, text=f"● {p}",
                           font=("Segoe UI", 9, "bold"),
                           fg=cfg["color"], padx=12, pady=5,
                           cursor="hand2")
            btn.pack(side="left", padx=(0, 6))
            btn.bind("<Button-1>", lambda e, pv=p: self._set_prio(pv))
            self.prio_btns[p] = btn
        self._refresh_prio_ui()

        # Category Dropdown
        self._label(self.body, "CATEGORY")
        self.cat_var = tk.StringVar()
        cats = manager.all_categories()
        default = category if category not in ("Today", "Planned") else "Personal"
        self.cat_var.set(task.category if task else default)

        cat_frame = tk.Frame(self.body, bg=SURFACE3, highlightthickness=1,
                             highlightbackground=BORDER)
        cat_frame.pack(fill="x")
        cat_menu = tk.OptionMenu(cat_frame, self.cat_var, *cats)
        cat_menu.config(bg=SURFACE3, fg=TEXT, activebackground=SURFACE2,
                        activeforeground=ACCENT, bd=0, highlightthickness=0,
                        font=("Segoe UI", 10))
        cat_menu["menu"].config(bg=SURFACE2, fg=TEXT,
                                activebackground=ACCENT, activeforeground="white",
                                font=("Segoe UI", 10))
        cat_menu.pack(fill="x", padx=2, ipady=5)

        # Due Date
        self._label(self.body, "DUE DATE")
        default_due = ""
        if not task and category in ("Today", "Planned"):
            default_due = datetime.now().strftime("%Y-%m-%d")
        elif task:
            default_due = task.due_date or ""
        self.due_var = tk.StringVar(value=default_due)
        due_frame, _ = self._input(self.body, var=self.due_var)
        due_frame.pack(fill="x")

        # Quick date preset chips
        preset_row = tk.Frame(self.body, bg=SURFACE)
        preset_row.pack(fill="x", pady=(6, 0))
        today_s = datetime.now().strftime("%Y-%m-%d")
        tom_s   = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        for label, val in [("Today", today_s), ("Tomorrow", tom_s), ("Clear", "")]:
            color = TEXT_DIM if label == "Clear" else TEXT_MUTED
            chip = tk.Label(preset_row, text=label, font=("Segoe UI", 8),
                            fg=color, bg=SURFACE2, padx=8, pady=3, cursor="hand2")
            chip.pack(side="left", padx=(0, 6))
            chip.bind("<Enter>", lambda e, c=chip: c.config(fg=ACCENT))
            chip.bind("<Leave>", lambda e, c=chip, col=color: c.config(fg=col))
            chip.bind("<Button-1>", lambda e, v=val: self.due_var.set(v))

        self._btn_row(self.body, ok_text="Save Task",
                      ok_color=TEAL, on_ok=self.save)
        self.title_ent.bind("<Return>", lambda e: self.save())

    def _set_prio(self, prio):
        self.selected_prio = prio
        self._refresh_prio_ui()

    def _refresh_prio_ui(self):
        for p, btn in self.prio_btns.items():
            cfg = PRIORITY_CONFIG[p]
            if p == self.selected_prio:
                btn.config(bg=cfg["bg"], relief="flat",
                           highlightthickness=1)
            else:
                btn.config(bg=SURFACE, relief="flat",
                           highlightthickness=0)

    def save(self):
        t = self.title_var.get().strip()
        if not t:
            return
        due = self.due_var.get().strip()
        try:
            if self.task:
                self.manager.edit_task(self.task.id, title=t,
                                       category=self.cat_var.get(),
                                       priority=self.selected_prio,
                                       due_date=due)
            else:
                self.manager.add_task(title=t, category=self.cat_var.get(),
                                      priority=self.selected_prio, due_date=due)
        except TaskManagerError:
            return
        if self.on_save:
            self.on_save()
        self.destroy()


class AboutModal(DarkModal):
    def __init__(self, parent):
        super().__init__(parent, title="✦  About Taskly", width=360, height=280)
        tk.Label(self.body, text="🚀", font=("Segoe UI Emoji", 38),
                 bg=SURFACE).pack(pady=(0, 8))
        tk.Label(self.body, text="Taskly  ·  Advanced Task Manager",
                 font=("Segoe UI", 13, "bold"), fg=TEXT, bg=SURFACE).pack()
        tk.Label(self.body, text="v3.0  Dark Edition  —  Python Standard Library",
                 font=("Segoe UI", 9), fg=TEXT_MUTED, bg=SURFACE).pack(pady=(4, 14))
        tk.Label(self.body,
                 text="Beautiful, native dark-mode task management. "
                      "Categories, priorities, live search, "
                      "custom lists, and persistent JSON storage.",
                 font=("Segoe UI", 9), fg=TEXT_DIM, bg=SURFACE,
                 wraplength=300, justify="center").pack()
        GlowButton(self.body, text="Awesome!", bg_color=ACCENT,
                   width=120, height=36, command=self.destroy).pack(pady=16)


# ─────────────────────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────────────────────

class TodoApp(tk.Tk):

    def __init__(self, user_name: str = "Ender"):
        super().__init__()
        self.title("Taskly  —  Task Manager")
        self.geometry("430x750")
        self.minsize(390, 600)
        self.configure(bg=BG)

        self.manager     = TaskManager(filepath="data/tasks.json")
        self.user_name   = user_name
        self.active_cat  = None   # current category dict
        self.filter_tab  = "All"  # "All" | "Active" | "Completed"
        self.search_q    = ""

        self._container = tk.Frame(self, bg=BG)
        self._container.pack(fill="both", expand=True)

        if not self.manager.onboarded:
            self._show_onboarding()
        else:
            self._show_dashboard()

    # ─── helpers ────────────────────────────────────────────────
    def _clear(self):
        for w in self._container.winfo_children():
            w.destroy()

    def _section_label(self, parent, text):
        tk.Label(parent, text=text.upper(),
                 font=("Segoe UI", 8, "bold"),
                 fg=TEXT_DIM, bg=BG).pack(anchor="w", padx=20, pady=(14, 4))

    def _scrollable(self, parent, bg=BG, width=None):
        """Returns (outer_frame, inner_frame) for a scrollable region."""
        outer = tk.Frame(parent, bg=bg)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
        inner  = tk.Frame(canvas, bg=bg)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        # Dynamically resize inner width
        def _resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", _resize)

        canvas.pack(side="left", fill="both", expand=True)

        # Mouse wheel
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(
                            int(-1 * (e.delta / 120)), "units"))

        return outer, inner, canvas

    # ─── ONBOARDING ──────────────────────────────────────────────
    def _show_onboarding(self):
        self._clear()
        root = tk.Frame(self._container, bg=BG)
        root.pack(fill="both", expand=True)

        tk.Frame(root, bg=BG, height=80).pack()

        # Big glowing circle icon
        blob = tk.Canvas(root, width=180, height=180, bg=BG, highlightthickness=0)
        blob.pack(pady=10)
        # Outer glow ring
        blob.create_oval(4, 4, 176, 176, fill="", outline=ACCENT, width=1.5)
        # Main circle
        blob.create_oval(16, 16, 164, 164, fill=SURFACE2, outline="")
        blob.create_text(90, 85, text="🗂", font=("Segoe UI Emoji", 52))

        tk.Label(root, text="Stay Organized.\nStay Focused.",
                 font=("Segoe UI", 19, "bold"), fg=TEXT, bg=BG,
                 justify="center").pack(pady=(24, 8))

        tk.Label(root,
                 text="Taskly is your personal productivity hub.\n"
                      "Tasks, priorities, smart lists — all in one place.",
                 font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG,
                 justify="center", wraplength=300).pack(padx=30, pady=(0, 36))

        GlowButton(root, text="Get Started →", bg_color=ACCENT,
                   hover_color=ACCENT_GLOW, width=180, height=46,
                   font_size=11, command=self._complete_onboarding).pack()

    def _complete_onboarding(self):
        self.manager.mark_onboarded()
        self._show_dashboard()

    # ─── DASHBOARD ────────────────────────────────────────────────
    def _show_dashboard(self):
        self._clear()
        self.active_cat = None

        root = tk.Frame(self._container, bg=BG)
        root.pack(fill="both", expand=True)

        # ── TOP HEADER BAR ──
        header = tk.Frame(root, bg=SURFACE2, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        top = tk.Frame(header, bg=SURFACE2)
        top.pack(fill="x", padx=20, pady=14)

        # Menu icon
        menu = tk.Label(top, text="☰", font=("Segoe UI", 17, "bold"),
                        fg=TEXT_MUTED, bg=SURFACE2, cursor="hand2")
        menu.pack(side="left")
        menu.bind("<Button-1>", lambda e: AboutModal(self))
        menu.bind("<Enter>", lambda e: menu.config(fg=ACCENT_GLOW))
        menu.bind("<Leave>", lambda e: menu.config(fg=TEXT_MUTED))

        # App name
        tk.Label(top, text="Taskly", font=("Segoe UI", 14, "bold"),
                 fg=TEXT, bg=SURFACE2).pack(side="left", padx=12)

        # Avatar pill
        av = tk.Canvas(top, width=36, height=36, bg=SURFACE2, highlightthickness=0)
        av.pack(side="right")
        av.create_oval(2, 2, 34, 34, fill=ACCENT_DIM, outline=ACCENT_GLOW, width=1.5)
        av.create_text(18, 18, text=self.user_name[:1].upper(),
                       font=("Segoe UI", 12, "bold"), fill="white")

        # ── GREETING BANNER ──
        stats    = self.manager.stats()
        pending  = sum(v for v in stats.values())
        today_ct = stats.get("Today", 0)

        banner = tk.Frame(root, bg=BG)
        banner.pack(fill="x", padx=20, pady=(18, 4))

        greeting = datetime.now().hour
        time_txt = "Good morning" if greeting < 12 else ("Good afternoon" if greeting < 17 else "Good evening")
        tk.Label(banner, text=f"{time_txt}, {self.user_name} 👋",
                 font=("Segoe UI", 16, "bold"), fg=TEXT, bg=BG).pack(anchor="w")
        sub = (f"You have {today_ct} task{'s' if today_ct != 1 else ''} due today."
               if today_ct else "Nothing due today — enjoy the calm! 🎉")
        tk.Label(banner, text=sub, font=("Segoe UI", 10),
                 fg=TEXT_MUTED, bg=BG).pack(anchor="w", pady=(2, 0))

        # ── SEARCH BAR ──
        s_frame = tk.Frame(root, bg=SURFACE3, highlightthickness=1,
                           highlightbackground=BORDER)
        s_frame.pack(fill="x", padx=16, pady=(12, 4))

        tk.Label(s_frame, text="🔍", font=("Segoe UI Emoji", 11),
                 bg=SURFACE3, fg=TEXT_MUTED).pack(side="left", padx=(10, 4), pady=6)

        self._search_var = tk.StringVar(value=self.search_q)
        s_ent = tk.Entry(s_frame, textvariable=self._search_var,
                         font=("Segoe UI", 10), bg=SURFACE3, fg=TEXT,
                         insertbackground=ACCENT, bd=0,)
        s_ent.pack(side="left", fill="x", expand=True, ipady=6)
        s_ent.bind("<KeyRelease>", self._on_search)
        s_ent.bind("<FocusIn>",  lambda e: s_frame.config(highlightbackground=ACCENT))
        s_ent.bind("<FocusOut>", lambda e: s_frame.config(highlightbackground=BORDER))

        if self.search_q:
            clr = tk.Label(s_frame, text="✕", font=("Segoe UI", 9, "bold"),
                           fg=TEXT_MUTED, bg=SURFACE3, cursor="hand2", padx=10)
            clr.pack(side="right")
            clr.bind("<Button-1>", lambda e: self._clear_search())

        # ── CATEGORIES SCROLL AREA ──
        _, scroll_inner, _ = self._scrollable(root)
        scroll_inner.config(padx=16, pady=8)

        if self.search_q.strip():
            self._build_search_results(scroll_inner)
        else:
            self._section_label(scroll_inner, "My Lists")
            for cat in self.manager.get_categories():
                self._build_cat_card(scroll_inner, cat, stats)

            # Progress Summary Card
            if pending > 0:
                self._build_summary_card(scroll_inner, stats)

            # Add List Button
            self._build_add_list_button(scroll_inner)

    def _on_search(self, event):
        self.search_q = self._search_var.get()
        self._show_dashboard()

    def _clear_search(self):
        self.search_q = ""
        self._show_dashboard()

    def _build_summary_card(self, parent, stats):
        """Compact summary stats card."""
        self._section_label(parent, "Overview")
        card = tk.Frame(parent, bg=SURFACE, highlightthickness=1,
                        highlightbackground=BORDER, padx=14, pady=12)
        card.pack(fill="x", pady=(0, 6))

        all_tasks = self.manager.tasks
        total = len(all_tasks)
        done  = sum(1 for t in all_tasks if t.completed)
        pct   = int((done / total) * 100) if total else 0

        row = tk.Frame(card, bg=SURFACE)
        row.pack(fill="x")

        # Stats
        for label, val, color in [
            (f"{total}", "Total", TEXT),
            (f"{done}", "Done", GREEN),
            (f"{total - done}", "Pending", GOLD),
        ]:
            col = tk.Frame(row, bg=SURFACE)
            col.pack(side="left", expand=True)
            tk.Label(col, text=label, font=("Segoe UI", 18, "bold"),
                     fg=color, bg=SURFACE).pack()
            tk.Label(col, text=val,   font=("Segoe UI", 9),
                     fg=TEXT_MUTED, bg=SURFACE).pack()

        # Progress bar
        pb_bg = tk.Frame(card, bg=SURFACE3, height=6)
        pb_bg.pack(fill="x", pady=(12, 0))

        if pct > 0:
            pb_fill = tk.Frame(card, bg=TEAL, height=6)
            pb_fill.place(in_=pb_bg, relwidth=pct / 100, relheight=1)

        tk.Label(card, text=f"{pct}% complete",
                 font=("Segoe UI", 8), fg=TEXT_DIM, bg=SURFACE).pack(anchor="e", pady=(2, 0))

    def _build_cat_card(self, parent, cat, stats):
        card = tk.Frame(parent, bg=SURFACE, highlightthickness=1,
                        highlightbackground=BORDER, height=70)
        card.pack(fill="x", pady=5)
        card.pack_propagate(False)

        # Hover highlight
        def _enter(e): card.config(highlightbackground=ACCENT)
        def _leave(e): card.config(highlightbackground=BORDER)
        card.bind("<Enter>", _enter)
        card.bind("<Leave>", _leave)
        card.bind("<Button-1>", lambda e, c=cat: self._show_cat_detail(c))

        # Colored icon pill
        pill_color = cat.get("bg", SURFACE2)
        pill = tk.Frame(card, bg=pill_color, width=46, height=46)
        pill.pack(side="left", padx=(14, 12), pady=12)
        pill.pack_propagate(False)
        pill.bind("<Button-1>", lambda e, c=cat: self._show_cat_detail(c))

        icon = tk.Label(pill, text=cat["icon"],
                        font=("Segoe UI Emoji", 16),
                        bg=pill_color, fg=cat.get("color", ACCENT))
        icon.pack(fill="both", expand=True)
        icon.bind("<Button-1>", lambda e, c=cat: self._show_cat_detail(c))

        # Text info
        txt = tk.Frame(card, bg=SURFACE)
        txt.pack(side="left", fill="y", pady=12)
        txt.bind("<Button-1>", lambda e, c=cat: self._show_cat_detail(c))

        name = tk.Label(txt, text=cat["label"],
                        font=("Segoe UI", 12, "bold"), fg=TEXT, bg=SURFACE)
        name.pack(anchor="w")
        name.bind("<Button-1>", lambda e, c=cat: self._show_cat_detail(c))

        count = stats.get(cat["label"], 0)
        count_lbl = tk.Label(txt, text=f"{count} task{'s' if count != 1 else ''}",
                             font=("Segoe UI", 9), fg=TEXT_MUTED, bg=SURFACE)
        count_lbl.pack(anchor="w")
        count_lbl.bind("<Button-1>", lambda e, c=cat: self._show_cat_detail(c))

        # Delete badge for custom lists
        if "smart" not in cat and cat["label"] not in ("Personal", "Work", "Shopping"):
            x_lbl = tk.Label(card, text="✕", font=("Segoe UI", 11, "bold"),
                             fg=TEXT_DIM, bg=SURFACE, cursor="hand2")
            x_lbl.pack(side="right", padx=16)
            x_lbl.bind("<Enter>", lambda e: x_lbl.config(fg=ROSE))
            x_lbl.bind("<Leave>", lambda e: x_lbl.config(fg=TEXT_DIM))
            x_lbl.bind("<Button-1>", lambda e, c=cat: self._confirm_delete_cat(c))

        # Task count badge on right
        if count > 0:
            badge = tk.Canvas(card, width=26, height=26, bg=SURFACE, highlightthickness=0)
            badge.pack(side="right", padx=(0, 14))
            badge.create_oval(2, 2, 24, 24, fill=ACCENT_DIM, outline="")
            badge.create_text(13, 13, text=str(count),
                              font=("Segoe UI", 8, "bold"), fill="white")

    def _build_search_results(self, parent):
        results = self.manager.search(self.search_q)
        tk.Label(parent, text=f"Search  ·  {len(results)} result{'s' if len(results) != 1 else ''}",
                 font=("Segoe UI", 10, "bold"), fg=TEXT_MUTED, bg=BG).pack(anchor="w", pady=(4, 10))
        if not results:
            tk.Label(parent, text="No tasks match that search.",
                     font=("Segoe UI", 10), fg=TEXT_DIM, bg=BG).pack(pady=30)
            return
        for t in results:
            self._build_task_card(parent, t)

    def _build_add_list_button(self, parent):
        frame = tk.Frame(parent, bg=SURFACE, highlightthickness=1,
                         highlightbackground=BORDER, height=52)
        frame.pack(fill="x", pady=6)
        frame.pack_propagate(False)

        btn = tk.Label(frame, text="+ Create New List",
                       font=("Segoe UI", 10, "bold"), fg=TEAL, bg=SURFACE,
                       cursor="hand2")
        btn.pack(fill="both", expand=True)
        btn.bind("<Enter>", lambda e: btn.config(bg=SURFACE2, fg=TEAL_GLOW))
        btn.bind("<Leave>", lambda e: btn.config(bg=SURFACE, fg=TEAL))
        btn.bind("<Button-1>", lambda e: self._open_new_list_dialog())

    def _open_new_list_dialog(self):
        NewListModal(self, on_submit=self._create_category)

    def _create_category(self, name):
        try:
            self.manager.add_category(name)
            self._show_dashboard()
        except TaskManagerError:
            pass

    def _confirm_delete_cat(self, cat):
        ConfirmModal(self,
                     message=f"Delete the '{cat['label']}' list and all its tasks?",
                     on_confirm=lambda: (self.manager.delete_category(cat["label"]),
                                        self._show_dashboard()))

    # ─── CATEGORY DETAIL ────────────────────────────────────────────────
    def _show_cat_detail(self, cat):
        self._clear()
        self.active_cat = cat

        root = tk.Frame(self._container, bg=BG)
        root.pack(fill="both", expand=True)

        # ── HEADER ──
        p = CAT_PALETTE.get(cat["label"], {})
        hdr_bg = p.get("bg", SURFACE2) if p else SURFACE2

        header = tk.Frame(root, bg=hdr_bg, height=120)
        header.pack(fill="x")
        header.pack_propagate(False)

        top_row = tk.Frame(header, bg=hdr_bg)
        top_row.pack(fill="x", padx=16, pady=(14, 0))

        back = tk.Label(top_row, text="← Back",
                        font=("Segoe UI", 11, "bold"),
                        fg=TEXT_MUTED, bg=hdr_bg, cursor="hand2")
        back.pack(side="left")
        back.bind("<Button-1>", lambda e: self._show_dashboard())
        back.bind("<Enter>", lambda e: back.config(fg=TEXT))
        back.bind("<Leave>", lambda e: back.config(fg=TEXT_MUTED))

        # Menu dots
        dots = tk.Label(top_row, text="⋮", font=("Segoe UI", 16, "bold"),
                        fg=TEXT_MUTED, bg=hdr_bg, cursor="hand2")
        dots.pack(side="right")
        dots.bind("<Button-1>", lambda e: self._open_cat_menu(dots))

        # Category identity row
        id_row = tk.Frame(header, bg=hdr_bg)
        id_row.pack(fill="x", padx=16, pady=(8, 0))

        icon_chip = tk.Frame(id_row, bg=cat.get("bg", SURFACE2), width=40, height=40)
        icon_chip.pack(side="left", padx=(0, 10))
        icon_chip.pack_propagate(False)
        tk.Label(icon_chip, text=cat["icon"],
                 font=("Segoe UI Emoji", 15),
                 bg=cat.get("bg", SURFACE2),
                 fg=cat.get("color", ACCENT)).pack(fill="both", expand=True)

        info_col = tk.Frame(id_row, bg=hdr_bg)
        info_col.pack(side="left")

        tasks = self.manager.list_by_category(cat["label"])
        open_ct = sum(1 for t in tasks if not t.completed)

        tk.Label(info_col, text=cat["label"],
                 font=("Segoe UI", 17, "bold"), fg=TEXT, bg=hdr_bg).pack(anchor="w")
        tk.Label(info_col, text=f"{open_ct} pending",
                 font=("Segoe UI", 9), fg=TEXT_MUTED, bg=hdr_bg).pack(anchor="w")

        # ── FILTER TABS ──
        tabs = tk.Frame(root, bg=SURFACE2)
        tabs.pack(fill="x")
        for tab in ("All", "Active", "Completed"):
            active = (self.filter_tab == tab)
            tb = tk.Label(tabs, text=tab,
                          font=("Segoe UI", 9, "bold" if active else "normal"),
                          fg=TEAL if active else TEXT_MUTED,
                          bg=SURFACE2 if not active else SURFACE,
                          padx=18, pady=9, cursor="hand2")
            tb.pack(side="left")
            tb.bind("<Button-1>", lambda e, t=tab: self._set_filter(t))

        tk.Frame(root, bg=BORDER, height=1).pack(fill="x")

        # ── TASK LIST ──
        _, inner, _ = self._scrollable(root)
        inner.config(padx=14, pady=8)

        filtered = tasks
        if self.filter_tab == "Active":
            filtered = [t for t in tasks if not t.completed]
        elif self.filter_tab == "Completed":
            filtered = [t for t in tasks if t.completed]

        if not filtered:
            tk.Label(inner, text=f"No {self.filter_tab.lower()} tasks here.\nTap '+' to add one.",
                     font=("Segoe UI", 10), fg=TEXT_DIM, bg=BG,
                     justify="center").pack(pady=60)
        else:
            order = {"High": 0, "Medium": 1, "Low": 2}
            filtered.sort(key=lambda t: (
                t.completed,
                order.get(t.priority, 1),
                t.due_date or "9999-99-99",
            ))
            for t in filtered:
                self._build_task_card(inner, t)

        # FAB
        fab = FAB(root, command=self._open_task_dialog)
        fab.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")

    def _set_filter(self, f):
        self.filter_tab = f
        if self.active_cat:
            self._show_cat_detail(self.active_cat)

    def _open_cat_menu(self, anchor):
        menu = tk.Menu(self, tearoff=0,
                       bg=SURFACE2, fg=TEXT,
                       activebackground=ACCENT, activeforeground="white",
                       font=("Segoe UI", 10))
        menu.add_command(label="Clear Completed", command=self._clear_completed)
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height()
        menu.post(x, y)

    def _clear_completed(self):
        if not self.active_cat:
            return
        tasks = self.manager.list_by_category(self.active_cat["label"])
        for t in tasks:
            if t.completed:
                self.manager.delete_task(t.id)
        self._show_cat_detail(self.active_cat)

    # ─── TASK CARD ──────────────────────────────────────────────────────
    def _build_task_card(self, parent, task):
        card = tk.Frame(parent, bg=SURFACE, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", pady=4)

        # Left priority indicator strip
        p_cfg  = PRIORITY_CONFIG.get(task.priority, PRIORITY_CONFIG["Medium"])
        strip  = tk.Frame(card, bg=p_cfg["color"], width=3)
        strip.pack(side="left", fill="y")

        # Checkbox
        chk = PremiumCheckbox(card, checked=task.completed,
                              command=lambda v, tid=task.id: self._toggle_task(tid))
        chk.pack(side="left", padx=(10, 8), pady=12)

        # Main content area
        content = tk.Frame(card, bg=SURFACE)
        content.pack(side="left", fill="both", expand=True, pady=10)

        tfont  = ("Segoe UI", 10, "overstrike") if task.completed else ("Segoe UI", 10, "bold")
        tcolor = TEXT_MUTED if task.completed else TEXT

        t_lbl = tk.Label(content, text=task.title, font=tfont,
                         fg=tcolor, bg=SURFACE, anchor="w", cursor="hand2")
        t_lbl.pack(fill="x")
        t_lbl.bind("<Double-Button-1>", lambda e, t=task: self._open_task_dialog(task=t))

        # Meta row — priority pill + due date
        meta = tk.Frame(content, bg=SURFACE)
        meta.pack(fill="x", pady=(3, 0))

        # Priority pill
        pill = tk.Label(meta, text=p_cfg["color"] and task.priority,
                        font=("Segoe UI", 7, "bold"),
                        fg=p_cfg["color"], bg=p_cfg["bg"],
                        padx=6, pady=2)
        pill.pack(side="left", padx=(0, 6))

        # Category chip (shown in search results only — when active_cat is None)
        if not self.active_cat and task.category:
            cat_chip = tk.Label(meta, text=task.category,
                                font=("Segoe UI", 7),
                                fg=TEXT_DIM, bg=SURFACE3,
                                padx=5, pady=2)
            cat_chip.pack(side="left", padx=(0, 6))

        # Due date chip
        if task.due_date:
            today = datetime.now().strftime("%Y-%m-%d")
            overdue = (task.due_date < today and not task.completed)
            due_fg = ROSE if overdue else TEXT_MUTED
            due_bg = "#2D1A25" if overdue else SURFACE3
            due = tk.Label(meta, text=f"📅 {task.due_date}",
                           font=("Segoe UI", 8),
                           fg=due_fg, bg=due_bg, padx=6, pady=2)
            due.pack(side="left")

        # Right side action bar
        actions = tk.Frame(card, bg=SURFACE)
        actions.pack(side="right", padx=8)

        edit_lbl = tk.Label(actions, text="✏", font=("Segoe UI Emoji", 11),
                            fg=TEXT_DIM, bg=SURFACE, cursor="hand2")
        edit_lbl.pack(side="left", padx=4)
        edit_lbl.bind("<Enter>", lambda e: edit_lbl.config(fg=ACCENT_GLOW))
        edit_lbl.bind("<Leave>", lambda e: edit_lbl.config(fg=TEXT_DIM))
        edit_lbl.bind("<Button-1>", lambda e, t=task: self._open_task_dialog(task=t))

        del_lbl = tk.Label(actions, text="✕", font=("Segoe UI", 11, "bold"),
                           fg=TEXT_DIM, bg=SURFACE, cursor="hand2")
        del_lbl.pack(side="left", padx=4)
        del_lbl.bind("<Enter>", lambda e: del_lbl.config(fg=ROSE))
        del_lbl.bind("<Leave>", lambda e: del_lbl.config(fg=TEXT_DIM))
        del_lbl.bind("<Button-1>", lambda e, tid=task.id: self._confirm_delete_task(tid))

    # ─── TASK ACTIONS ─────────────────────────────────────────────────
    def _toggle_task(self, task_id):
        try:
            self.manager.toggle_task(task_id)
            self._refresh()
        except TaskManagerError:
            pass

    def _confirm_delete_task(self, task_id):
        ConfirmModal(self,
                     message="Are you sure you want to delete this task?",
                     on_confirm=lambda: self._delete_task(task_id))

    def _delete_task(self, task_id):
        try:
            self.manager.delete_task(task_id)
            self._refresh()
        except TaskManagerError:
            pass

    def _open_task_dialog(self, task=None):
        cat = self.active_cat["label"] if self.active_cat else "Personal"
        TaskModal(self, self.manager, category=cat, task=task,
                  on_save=self._refresh)

    def _refresh(self):
        if self.active_cat:
            self._show_cat_detail(self.active_cat)
        else:
            self._show_dashboard()


if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
