"""
gui.py
------
Ultra-modern, high-fidelity Tkinter GUI for the Tudy Task Manager.

Features:
    * Standard mobile-inspired resizable viewport (420x720)
    * Custom non-native Modal Dialogs (New List, Task Editor, Confirm Delete, About)
    * Live Search Bar filtering tasks in real time
    * Color-coded Priority Pills (Low, Medium, High)
    * Contextual Quick-Date Selectors (Today, Tomorrow, Next Week)
    * Category Filter Tabs (All, Active, Completed)
    * Fully styled custom buttons, canvas checkboxes, and progress widgets
"""

import tkinter as tk
from datetime import datetime, timedelta

from app.task_manager import TaskManager, TaskManagerError
from app.models import Task, PRIORITIES

# ---- Design System Tokens -----------------------------------------------
YELLOW = "#FFCB3D"
YELLOW_DARK = "#F5A623"
YELLOW_LIGHT = "#FFF8E1"
CREAM = "#FAF9F5"
WHITE = "#FFFFFF"
INK = "#1E1E2D"
GRAY = "#7E7E8F"
GRAY_LIGHT = "#F1F1F5"
LINE = "#E5E5EB"
TEAL = "#14B8A6"
TEAL_HOVER = "#0D9488"
TEAL_LIGHT = "#CCFBF1"
DANGER = "#EF4444"
DANGER_LIGHT = "#FEE2E2"

PRIORITY_CONFIG = {
    "High": {"color": "#EF4444", "bg": "#FEE2E2", "label": "HIGH"},
    "Medium": {"color": "#F97316", "bg": "#FFEDD5", "label": "MED"},
    "Low": {"color": "#10B981", "bg": "#D1FAE5", "label": "LOW"},
}


class CanvasCheckbox(tk.Canvas):
    """Custom canvas-drawn checkbox with teal fill and smooth vector checkmark."""

    def __init__(self, parent, checked=False, command=None, size=22, **kwargs):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=WHITE,
            highlightthickness=0,
            cursor="hand2",
            **kwargs,
        )
        self.size = size
        self.checked = checked
        self.command = command
        self.draw()
        self.bind("<Button-1>", self.on_click)

    def draw(self):
        self.delete("all")
        s = self.size
        if self.checked:
            # Rounded filled teal rectangle
            self.create_rectangle(1, 1, s - 1, s - 1, outline=TEAL, fill=TEAL, width=0)
            # White checkmark vector
            self.create_line(s * 0.28, s * 0.52, s * 0.45, s * 0.68, s * 0.73, s * 0.35, fill=WHITE, width=2.5)
        else:
            # Subtle border with light fill
            self.create_rectangle(1, 1, s - 1, s - 1, outline="#CBD5E1", fill=WHITE, width=1.5)

    def toggle(self):
        self.checked = not self.checked
        self.draw()

    def on_click(self, event):
        self.toggle()
        if self.command:
            self.command(self.checked)


class FAB(tk.Canvas):
    """Floating Action Button matching modern mobile floating teal + element."""

    def __init__(self, parent, command=None, size=52, **kwargs):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=WHITE,
            highlightthickness=0,
            cursor="hand2",
            **kwargs,
        )
        self.command = command
        self.size = size
        self.draw_normal()
        self.bind("<Button-1>", lambda e: self.click())
        self.bind("<Enter>", lambda e: self.draw_hover())
        self.bind("<Leave>", lambda e: self.draw_normal())

    def draw_normal(self):
        self.delete("all")
        s = self.size
        # Circle fill
        self.create_oval(2, 2, s - 2, s - 2, fill=TEAL, outline="")
        self.create_text(s / 2, s / 2 - 1, text="+", font=("Segoe UI", 26, "bold"), fill=WHITE)

    def draw_hover(self):
        self.delete("all")
        s = self.size
        self.create_oval(2, 2, s - 2, s - 2, fill=TEAL_HOVER, outline="")
        self.create_text(s / 2, s / 2 - 1, text="+", font=("Segoe UI", 26, "bold"), fill=WHITE)

    def click(self):
        if self.command:
            self.command()


class BaseModal(tk.Toplevel):
    """Custom themed modal overlay to replace native primitive system dialogs."""

    def __init__(self, parent, title="Dialog", width=360, height=280):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=WHITE)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)

        # Center over parent
        self.transient(parent)
        self.grab_set()

        px = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
        py = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

        # Modal Header Bar
        header = tk.Frame(self, bg=YELLOW, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_lbl = tk.Label(header, text=title, font=("Segoe UI", 12, "bold"), bg=YELLOW, fg=INK)
        title_lbl.pack(side="left", padx=16, pady=12)

        close_btn = tk.Label(header, text="✕", font=("Segoe UI", 11, "bold"), bg=YELLOW, fg=INK, cursor="hand2")
        close_btn.pack(side="right", padx=16, pady=12)
        close_btn.bind("<Button-1>", lambda e: self.destroy())

        # Main Content Frame
        self.body = tk.Frame(self, bg=WHITE, padx=20, pady=16)
        self.body.pack(fill="both", expand=True)

        self.bind("<Escape>", lambda e: self.destroy())


class CustomPromptModal(BaseModal):
    """Custom styled prompt dialog for adding custom lists."""

    def __init__(self, parent, title="Create New List", prompt="Enter list name:", on_submit=None):
        super().__init__(parent, title=title, width=360, height=220)
        self.on_submit = on_submit

        tk.Label(self.body, text=prompt, font=("Segoe UI", 10, "bold"), fg=INK, bg=WHITE).pack(anchor="w", pady=(0, 6))

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            self.body,
            textvariable=self.entry_var,
            font=("Segoe UI", 11),
            bg=CREAM,
            fg=INK,
            bd=0,
            highlightthickness=1.5,
            highlightbackground=LINE,
            highlightcolor=TEAL,
        )
        self.entry.pack(fill="x", ipady=8, pady=(0, 20))
        self.entry.focus_set()

        # Buttons frame
        btn_box = tk.Frame(self.body, bg=WHITE)
        btn_box.pack(fill="x", side="bottom")

        cancel_btn = tk.Button(
            btn_box,
            text="Cancel",
            font=("Segoe UI", 10),
            bg=GRAY_LIGHT,
            fg=INK,
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.destroy,
        )
        cancel_btn.pack(side="left")

        submit_btn = tk.Button(
            btn_box,
            text="Create List",
            font=("Segoe UI", 10, "bold"),
            bg=TEAL,
            fg=WHITE,
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.submit,
        )
        submit_btn.pack(side="right")

        self.entry.bind("<Return>", lambda e: self.submit())

    def submit(self):
        val = self.entry_var.get().strip()
        if val and self.on_submit:
            self.on_submit(val)
        self.destroy()


class CustomConfirmModal(BaseModal):
    """Custom styled confirmation modal for deletion actions."""

    def __init__(self, parent, title="Confirm Delete", message="Are you sure?", on_confirm=None):
        super().__init__(parent, title=title, width=360, height=200)
        self.on_confirm = on_confirm

        msg_lbl = tk.Label(
            self.body,
            text=message,
            font=("Segoe UI", 10),
            fg=INK,
            bg=WHITE,
            wraplength=310,
            justify="left",
        )
        msg_lbl.pack(anchor="w", pady=(0, 20))

        btn_box = tk.Frame(self.body, bg=WHITE)
        btn_box.pack(fill="x", side="bottom")

        cancel_btn = tk.Button(
            btn_box,
            text="Cancel",
            font=("Segoe UI", 10),
            bg=GRAY_LIGHT,
            fg=INK,
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.destroy,
        )
        cancel_btn.pack(side="left")

        confirm_btn = tk.Button(
            btn_box,
            text="Delete",
            font=("Segoe UI", 10, "bold"),
            bg=DANGER,
            fg=WHITE,
            bd=0,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.confirm,
        )
        confirm_btn.pack(side="right")

    def confirm(self):
        if self.on_confirm:
            self.on_confirm()
        self.destroy()


class CustomTaskModal(BaseModal):
    """Custom styled task editor dialog with pill selectors for Priority and Category."""

    def __init__(self, parent, manager: TaskManager, category="Personal", task=None, on_save=None):
        title = "Edit Task" if task else "Create New Task"
        super().__init__(parent, title=title, width=380, height=480)
        self.manager = manager
        self.task = task
        self.on_save = on_save

        # Title
        tk.Label(self.body, text="Task Title", font=("Segoe UI", 9, "bold"), fg=GRAY, bg=WHITE).pack(anchor="w", pady=(0, 4))
        self.title_var = tk.StringVar(value=task.title if task else "")
        self.title_ent = tk.Entry(
            self.body,
            textvariable=self.title_var,
            font=("Segoe UI", 11),
            bg=CREAM,
            fg=INK,
            bd=0,
            highlightthickness=1.5,
            highlightbackground=LINE,
            highlightcolor=TEAL,
        )
        self.title_ent.pack(fill="x", ipady=7, pady=(0, 14))
        self.title_ent.focus_set()

        # Priority Pill Selector
        tk.Label(self.body, text="Priority", font=("Segoe UI", 9, "bold"), fg=GRAY, bg=WHITE).pack(anchor="w", pady=(0, 6))
        prio_frame = tk.Frame(self.body, bg=WHITE)
        prio_frame.pack(fill="x", pady=(0, 14))

        self.selected_prio = tk.StringVar(value=task.priority if task else "Medium")
        self.prio_buttons = {}
        for prio in PRIORITIES:
            btn = tk.Button(
                prio_frame,
                text=f"● {prio}",
                font=("Segoe UI", 9, "bold"),
                bd=0,
                padx=12,
                pady=6,
                cursor="hand2",
                command=lambda p=prio: self.set_priority(p),
            )
            btn.pack(side="left", padx=(0, 8))
            self.prio_buttons[prio] = btn
        self.update_prio_ui()

        # Category Selector
        tk.Label(self.body, text="Category", font=("Segoe UI", 9, "bold"), fg=GRAY, bg=WHITE).pack(anchor="w", pady=(0, 6))
        default_cat = category if category not in ("Today", "Planned") else "Personal"
        self.selected_cat = tk.StringVar(value=task.category if task else default_cat)

        cat_frame = tk.Frame(self.body, bg=WHITE)
        cat_frame.pack(fill="x", pady=(0, 14))

        cat_menu = tk.OptionMenu(self.body, self.selected_cat, *manager.all_categories())
        cat_menu.config(bg=CREAM, fg=INK, bd=0, highlightthickness=1, highlightbackground=LINE, font=("Segoe UI", 10), pady=6)
        cat_menu.pack(fill="x", pady=(0, 14))

        # Due Date Input + Quick Presets
        tk.Label(self.body, text="Due Date", font=("Segoe UI", 9, "bold"), fg=GRAY, bg=WHITE).pack(anchor="w", pady=(0, 4))
        
        default_due = ""
        if not task and category in ("Today", "Planned"):
            default_due = datetime.now().strftime("%Y-%m-%d")
        else:
            default_due = task.due_date if task else ""

        self.due_var = tk.StringVar(value=default_due)
        self.due_ent = tk.Entry(
            self.body,
            textvariable=self.due_var,
            font=("Segoe UI", 10),
            bg=CREAM,
            fg=INK,
            bd=0,
            highlightthickness=1.5,
            highlightbackground=LINE,
            highlightcolor=TEAL,
        )
        self.due_ent.pack(fill="x", ipady=6, pady=(0, 6))

        # Quick Date Presets
        preset_frame = tk.Frame(self.body, bg=WHITE)
        preset_frame.pack(fill="x", pady=(0, 18))

        today_str = datetime.now().strftime("%Y-%m-%d")
        tom_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        tk.Button(preset_frame, text="Today", font=("Segoe UI", 8), bg=GRAY_LIGHT, fg=INK, bd=0, padx=8, pady=3, cursor="hand2",
                  command=lambda: self.due_var.set(today_str)).pack(side="left", padx=(0, 6))
        tk.Button(preset_frame, text="Tomorrow", font=("Segoe UI", 8), bg=GRAY_LIGHT, fg=INK, bd=0, padx=8, pady=3, cursor="hand2",
                  command=lambda: self.due_var.set(tom_str)).pack(side="left", padx=(0, 6))
        tk.Button(preset_frame, text="Clear", font=("Segoe UI", 8), bg=GRAY_LIGHT, fg=GRAY, bd=0, padx=8, pady=3, cursor="hand2",
                  command=lambda: self.due_var.set("")).pack(side="left")

        # Save / Cancel Action Bar
        btn_box = tk.Frame(self.body, bg=WHITE)
        btn_box.pack(fill="x", side="bottom")

        tk.Button(
            btn_box,
            text="Cancel",
            font=("Segoe UI", 10),
            bg=GRAY_LIGHT,
            fg=INK,
            bd=0,
            padx=16,
            pady=8,
            cursor="hand2",
            command=self.destroy,
        ).pack(side="left")

        tk.Button(
            btn_box,
            text="Save Task",
            font=("Segoe UI", 10, "bold"),
            bg=TEAL,
            fg=WHITE,
            bd=0,
            padx=22,
            pady=8,
            cursor="hand2",
            command=self.save,
        ).pack(side="right")

        self.title_ent.bind("<Return>", lambda e: self.save())

    def set_priority(self, prio):
        self.selected_prio.set(prio)
        self.update_prio_ui()

    def update_prio_ui(self):
        curr = self.selected_prio.get()
        for prio, btn in self.prio_buttons.items():
            cfg = PRIORITY_CONFIG[prio]
            if prio == curr:
                btn.config(bg=cfg["bg"], fg=cfg["color"])
            else:
                btn.config(bg=GRAY_LIGHT, fg=GRAY)

    def save(self):
        title = self.title_var.get().strip()
        if not title:
            return

        due_date = self.due_var.get().strip()
        try:
            if self.task:
                self.manager.edit_task(
                    self.task.id,
                    title=title,
                    category=self.selected_cat.get(),
                    priority=self.selected_prio.get(),
                    due_date=due_date,
                )
            else:
                self.manager.add_task(
                    title=title,
                    category=self.selected_cat.get(),
                    priority=self.selected_prio.get(),
                    due_date=due_date,
                )
        except TaskManagerError as e:
            CustomPromptModal(self, title="Error", prompt=str(e))
            return

        if self.on_save:
            self.on_save()
        self.destroy()


class CustomAboutModal(BaseModal):
    """About dialog modal."""

    def __init__(self, parent):
        super().__init__(parent, title="About Tudy", width=350, height=280)

        icon_lbl = tk.Label(self.body, text="🚀", font=("Segoe UI Emoji", 36), bg=WHITE)
        icon_lbl.pack(pady=(0, 6))

        title_lbl = tk.Label(self.body, text="Tudy Mobile Task Manager", font=("Segoe UI", 12, "bold"), fg=INK, bg=WHITE)
        title_lbl.pack()

        ver_lbl = tk.Label(self.body, text="Version 2.5 • Modern Edition", font=("Segoe UI", 9), fg=GRAY, bg=WHITE)
        ver_lbl.pack(pady=(2, 10))

        desc_lbl = tk.Label(
            self.body,
            text="A sleek, mobile-first task manager built with Python standard library. Features custom cards, priority sorting, search, and persistent JSON storage.",
            font=("Segoe UI", 9),
            fg=INK,
            bg=WHITE,
            wraplength=300,
            justify="center",
        )
        desc_lbl.pack(pady=(0, 16))

        btn = tk.Button(
            self.body,
            text="Awesome!",
            font=("Segoe UI", 10, "bold"),
            bg=TEAL,
            fg=WHITE,
            bd=0,
            padx=24,
            pady=6,
            cursor="hand2",
            command=self.destroy,
        )
        btn.pack()


class TodoApp(tk.Tk):
    """Main Application Window."""

    def __init__(self, user_name: str = "Ender"):
        super().__init__()
        self.title("Tudy — Advanced Task Manager")

        # Mobile viewport aspect ratio frame (420x720)
        self.geometry("420x720")
        self.minsize(380, 600)
        self.configure(bg=CREAM)

        self.manager = TaskManager(filepath="data/tasks.json")
        self.user_name = user_name
        self.active_category_data = None
        self.search_query = ""
        self.active_filter = "All"  # "All", "Active", "Completed"

        # Screen routing container
        self.screen_container = tk.Frame(self, bg=CREAM)
        self.screen_container.pack(fill="both", expand=True)

        if not self.manager.onboarded:
            self.show_onboarding()
        else:
            self.show_dashboard()

    def clear_screen(self):
        for w in self.screen_container.winfo_children():
            w.destroy()

    # ------------------------------------------------------------------ #
    # Onboarding View
    # ------------------------------------------------------------------ #
    def show_onboarding(self):
        self.clear_screen()
        onboard = tk.Frame(self.screen_container, bg=WHITE)
        onboard.pack(fill="both", expand=True)

        tk.Frame(onboard, bg=WHITE, height=60).pack()

        blob_canvas = tk.Canvas(onboard, width=160, height=160, bg=WHITE, highlightthickness=0)
        blob_canvas.pack(pady=10)
        blob_canvas.create_oval(5, 5, 155, 155, fill=YELLOW, outline="")
        blob_canvas.create_text(80, 75, text="🛍️📱", font=("Segoe UI Emoji", 44))

        tk.Label(onboard, text="Organize Your Life Beautifully", font=("Segoe UI", 16, "bold"), fg=INK, bg=WHITE).pack(pady=(20, 8))

        desc = (
            "Tudy is a mobile-first task manager crafted to bring focus, clarity, "
            "and elegance to your daily productivity."
        )
        tk.Label(onboard, text=desc, font=("Segoe UI", 10), fg=GRAY, bg=WHITE, wraplength=300, justify="center").pack(padx=20, pady=(0, 30))

        cta = tk.Button(
            onboard,
            text="Get Started →",
            bg=TEAL,
            fg=WHITE,
            font=("Segoe UI", 11, "bold"),
            bd=0,
            activebackground=TEAL_HOVER,
            activeforeground=WHITE,
            cursor="hand2",
            padx=32,
            pady=10,
            command=self.complete_onboarding,
        )
        cta.pack(pady=10)

    def complete_onboarding(self):
        self.manager.mark_onboarded()
        self.show_dashboard()

    # ------------------------------------------------------------------ #
    # Dashboard View
    # ------------------------------------------------------------------ #
    def show_dashboard(self):
        self.clear_screen()
        self.active_category_data = None

        dash = tk.Frame(self.screen_container, bg=CREAM)
        dash.pack(fill="both", expand=True)

        # Dashboard Top Header Banner
        header = tk.Frame(dash, bg=YELLOW, height=140)
        header.pack(fill="x")
        header.pack_propagate(False)

        top_row = tk.Frame(header, bg=YELLOW)
        top_row.pack(fill="x", padx=20, pady=(16, 0))

        menu_btn = tk.Label(top_row, text="☰", font=("Segoe UI", 18, "bold"), bg=YELLOW, fg=INK, cursor="hand2")
        menu_btn.pack(side="left")
        menu_btn.bind("<Button-1>", lambda e: CustomAboutModal(self))

        avatar = tk.Canvas(top_row, width=36, height=36, bg=YELLOW, highlightthickness=0)
        avatar.pack(side="right")
        avatar.create_oval(2, 2, 34, 34, fill=WHITE, outline="")
        avatar.create_text(18, 18, text=self.user_name[:1].upper(), font=("Segoe UI", 13, "bold"), fill=INK)

        greet_box = tk.Frame(header, bg=YELLOW)
        greet_box.pack(fill="x", padx=20, pady=(6, 0))

        tk.Label(greet_box, text=f"Hello, {self.user_name}", font=("Segoe UI", 18, "bold"), bg=YELLOW, fg=INK).pack(anchor="w")

        stats = self.manager.stats()
        today_tasks = stats.get("Today", 0)
        sub_txt = "Nothing due today — enjoy the calm!" if today_tasks == 0 else f"You have {today_tasks} task{'s' if today_tasks > 1 else ''} due today."
        tk.Label(greet_box, text=sub_txt, font=("Segoe UI", 10), bg=YELLOW, fg="#6B5A12").pack(anchor="w")

        # Search Bar Box
        search_box = tk.Frame(dash, bg=WHITE, bd=0, highlightthickness=1, highlightbackground=LINE)
        search_box.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(search_box, text="🔍", font=("Segoe UI Emoji", 11), bg=WHITE, fg=GRAY).pack(side="left", padx=(10, 4), pady=6)
        
        self.search_var = tk.StringVar(value=self.search_query)
        search_ent = tk.Entry(
            search_box,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg=WHITE,
            fg=INK,
            bd=0,
        )
        search_ent.pack(side="left", fill="x", expand=True, ipady=4)
        search_ent.bind("<KeyRelease>", self.on_search_change)

        if self.search_query:
            clear_lbl = tk.Label(search_box, text="✕", font=("Segoe UI", 9, "bold"), bg=WHITE, fg=GRAY, cursor="hand2")
            clear_lbl.pack(side="right", padx=10)
            clear_lbl.bind("<Button-1>", lambda e: self.clear_search())

        # Categories Scroll Area
        scroll_container = tk.Frame(dash, bg=CREAM)
        scroll_container.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        canvas = tk.Canvas(scroll_container, bg=CREAM, highlightthickness=0)
        vsb = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        cards_frame = tk.Frame(canvas, bg=CREAM)

        cards_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=cards_frame, anchor="nw", width=388)
        canvas.configure(yscrollcommand=vsb.set)

        canvas.pack(side="left", fill="both", expand=True)
        cards_frame.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Render list of Category Cards or Search Results
        if self.search_query.strip():
            self._build_search_results_cards(cards_frame)
        else:
            categories = self.manager.get_categories()
            for cat in categories:
                self._build_category_card(cards_frame, cat, stats)

            # Modern "+ Create New List" Card Button
            self._build_add_list_card(cards_frame)

    def on_search_change(self, event):
        self.search_query = self.search_var.get()
        self.show_dashboard()

    def clear_search(self):
        self.search_query = ""
        self.show_dashboard()

    def _build_search_results_cards(self, parent):
        matching_tasks = self.manager.search_tasks(self.search_query)
        tk.Label(parent, text=f"Search results ({len(matching_tasks)})", font=("Segoe UI", 10, "bold"), fg=GRAY, bg=CREAM).pack(anchor="w", pady=(4, 8))

        if not matching_tasks:
            tk.Label(parent, text="No matching tasks found.", font=("Segoe UI", 10), fg=GRAY, bg=CREAM).pack(pady=20)
            return

        for t in matching_tasks:
            self._build_task_card(parent, t)

    def _build_category_card(self, parent, cat, stats):
        card = tk.Frame(parent, bg=WHITE, bd=0, highlightthickness=1, highlightbackground=LINE, height=66)
        card.pack(fill="x", pady=4)
        card.pack_propagate(False)

        # Hover highlighting
        def on_enter(e): card.config(bg="#FAFAFC")
        def on_leave(e): card.config(bg=WHITE)
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        card.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        # Icon Chip Box
        chip = tk.Frame(card, bg=cat["bg"], width=42, height=42)
        chip.pack(side="left", padx=(12, 12), pady=12)
        chip.pack_propagate(False)
        chip.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        icon_lbl = tk.Label(chip, text=cat["icon"], font=("Segoe UI Emoji", 15), bg=cat["bg"], fg=cat["color"])
        icon_lbl.pack(fill="both", expand=True)
        icon_lbl.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        # Text Info
        txt_box = tk.Frame(card, bg=WHITE)
        txt_box.pack(side="left", fill="y", pady=12)
        txt_box.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        label_lbl = tk.Label(txt_box, text=cat["label"], font=("Segoe UI", 12, "bold"), fg=INK, bg=WHITE)
        label_lbl.pack(anchor="w")
        label_lbl.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        count = stats.get(cat["label"], 0)
        count_lbl = tk.Label(txt_box, text=f"{count} Task{'s' if count != 1 else ''}", font=("Segoe UI", 9), fg=GRAY, bg=WHITE)
        count_lbl.pack(anchor="w")
        count_lbl.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        # Custom Category Delete Action
        if "smart" not in cat and cat["label"] not in ("Personal", "Work", "Shopping"):
            del_lbl = tk.Label(card, text="✕", font=("Segoe UI", 11, "bold"), fg="#CBD5E1", bg=WHITE, cursor="hand2")
            del_lbl.pack(side="right", padx=16)
            del_lbl.bind("<Button-1>", lambda e, c=cat: self.prompt_delete_category(c))
            del_lbl.bind("<Enter>", lambda e: del_lbl.config(fg=DANGER))
            del_lbl.bind("<Leave>", lambda e: del_lbl.config(fg="#CBD5E1"))

    def _build_add_list_card(self, parent):
        """Custom styled button card for creating a new category list."""
        card = tk.Frame(parent, bg=WHITE, bd=0, highlightthickness=1, highlightbackground=LINE, height=54)
        card.pack(fill="x", pady=6)
        card.pack_propagate(False)

        btn = tk.Button(
            card,
            text="+ Create New List",
            font=("Segoe UI", 10, "bold"),
            bg=WHITE,
            fg=TEAL,
            activebackground=TEAL_LIGHT,
            activeforeground=TEAL_HOVER,
            bd=0,
            cursor="hand2",
            command=self.open_new_list_dialog,
        )
        btn.pack(fill="both", expand=True)

    def open_new_list_dialog(self):
        CustomPromptModal(
            self,
            title="Create New List",
            prompt="Enter a name for your custom list:",
            on_submit=self.create_category,
        )

    def create_category(self, name):
        try:
            self.manager.add_category(name)
            self.show_dashboard()
        except TaskManagerError as e:
            CustomPromptModal(self, title="Error", prompt=str(e))

    def prompt_delete_category(self, cat):
        CustomConfirmModal(
            self,
            title="Delete List",
            message=f"Delete '{cat['label']}' list and all tasks inside it?",
            on_confirm=lambda: (self.manager.delete_category(cat["label"]), self.show_dashboard()),
        )

    # ------------------------------------------------------------------ #
    # Category Detail Screen View
    # ------------------------------------------------------------------ #
    def show_category_detail(self, cat):
        self.clear_screen()
        self.active_category_data = cat

        detail = tk.Frame(self.screen_container, bg=WHITE)
        detail.pack(fill="both", expand=True)

        # Header Panel
        header = tk.Frame(detail, bg=YELLOW, height=125)
        header.pack(fill="x")
        header.pack_propagate(False)

        top_row = tk.Frame(header, bg=YELLOW)
        top_row.pack(fill="x", padx=16, pady=(14, 0))

        back_btn = tk.Label(top_row, text="← Back", font=("Segoe UI", 11, "bold"), bg=YELLOW, fg=INK, cursor="hand2")
        back_btn.pack(side="left")
        back_btn.bind("<Button-1>", lambda e: self.show_dashboard())

        # Category Identity Row
        who = tk.Frame(header, bg=YELLOW)
        who.pack(fill="x", padx=16, pady=(8, 0))

        chip = tk.Frame(who, bg="#FCECB5", width=36, height=36)
        chip.pack(side="left", padx=(0, 10))
        chip.pack_propagate(False)

        icon_lbl = tk.Label(chip, text=cat["icon"], font=("Segoe UI Emoji", 14), bg="#FCECB5", fg=cat["color"])
        icon_lbl.pack(fill="both", expand=True)

        info_box = tk.Frame(who, bg=YELLOW)
        info_box.pack(side="left")

        tasks = self.manager.list_by_category(cat["label"])
        open_count = sum(1 for t in tasks if not t.completed)

        tk.Label(info_box, text=cat["label"], font=("Segoe UI", 17, "bold"), bg=YELLOW, fg=INK).pack(anchor="w")
        tk.Label(info_box, text=f"{open_count} Task{'s' if open_count != 1 else ''} pending", font=("Segoe UI", 9, "bold"), bg=YELLOW, fg="#6B5A12").pack(anchor="w")

        # Filter Tabs Row
        tabs_bar = tk.Frame(detail, bg=GRAY_LIGHT, height=36)
        tabs_bar.pack(fill="x")

        for f_name in ("All", "Active", "Completed"):
            is_active = (self.active_filter == f_name)
            fg_col = TEAL if is_active else GRAY
            bg_col = WHITE if is_active else GRAY_LIGHT
            btn = tk.Button(
                tabs_bar,
                text=f_name,
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                bg=bg_col,
                fg=fg_col,
                bd=0,
                padx=16,
                cursor="hand2",
                command=lambda fn=f_name: self.set_filter(fn),
            )
            btn.pack(side="left", fill="y")

        # Scrollable Task Checklist
        list_container = tk.Frame(detail, bg=WHITE)
        list_container.pack(fill="both", expand=True, padx=16, pady=(8, 10))

        canvas = tk.Canvas(list_container, bg=WHITE, highlightthickness=0)
        vsb = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        task_rows_frame = tk.Frame(canvas, bg=WHITE)

        task_rows_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=task_rows_frame, anchor="nw", width=388)
        canvas.configure(yscrollcommand=vsb.set)

        canvas.pack(side="left", fill="both", expand=True)
        task_rows_frame.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Apply Tab Filter
        filtered_tasks = tasks
        if self.active_filter == "Active":
            filtered_tasks = [t for t in tasks if not t.completed]
        elif self.active_filter == "Completed":
            filtered_tasks = [t for t in tasks if t.completed]

        if not filtered_tasks:
            empty_msg = f"No {self.active_filter.lower()} tasks in this list.\nTap '+' to add one."
            tk.Label(task_rows_frame, text=empty_msg, font=("Segoe UI", 10), fg=GRAY, bg=WHITE, justify="center").pack(pady=50, fill="x")
        else:
            order = {"High": 0, "Medium": 1, "Low": 2}
            filtered_tasks.sort(key=lambda t: (t.completed, order.get(t.priority, 1), t.due_date or "9999-99-99"))

            for t in filtered_tasks:
                self._build_task_card(task_rows_frame, t)

        # FAB (Floating Action Button)
        fab = FAB(detail, command=self.open_task_dialog)
        fab.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")

    def set_filter(self, filter_name):
        self.active_filter = filter_name
        if self.active_category_data:
            self.show_category_detail(self.active_category_data)

    def _build_task_card(self, parent, task):
        """Builds a rich, interactive card for an individual task item."""
        card = tk.Frame(parent, bg=WHITE, bd=0, highlightthickness=1, highlightbackground=LINE)
        card.pack(fill="x", pady=4)

        # Checkbox
        chk = CanvasCheckbox(card, checked=task.completed, command=lambda val, t_id=task.id: self.toggle_task(t_id))
        chk.pack(side="left", padx=(10, 8), pady=12)

        # Content Box
        content = tk.Frame(card, bg=WHITE)
        content.pack(side="left", fill="both", expand=True, pady=8)

        font = ("Segoe UI", 10, "overstrike") if task.completed else ("Segoe UI", 10, "bold")
        color = GRAY if task.completed else INK

        title_lbl = tk.Label(content, text=task.title, font=font, fg=color, bg=WHITE, anchor="w", cursor="hand2")
        title_lbl.pack(fill="x")
        title_lbl.bind("<Double-Button-1>", lambda e, t=task: self.open_task_dialog(task=t))

        # Meta tags (Priority Pill + Category Tag + Due Date)
        meta_box = tk.Frame(content, bg=WHITE)
        meta_box.pack(fill="x", pady=(2, 0))

        p_cfg = PRIORITY_CONFIG.get(task.priority, PRIORITY_CONFIG["Medium"])
        prio_lbl = tk.Label(
            meta_box,
            text=p_cfg["label"],
            font=("Segoe UI", 7, "bold"),
            fg=p_cfg["color"],
            bg=p_cfg["bg"],
            padx=5,
            pady=1,
        )
        prio_lbl.pack(side="left", padx=(0, 6))

        if task.category:
            cat_lbl = tk.Label(
                meta_box,
                text=task.category,
                font=("Segoe UI", 8),
                fg=GRAY,
                bg=GRAY_LIGHT,
                padx=5,
                pady=1,
            )
            cat_lbl.pack(side="left", padx=(0, 6))

        if task.due_date:
            due_fg = DANGER if (task.due_date < datetime.now().strftime("%Y-%m-%d") and not task.completed) else GRAY
            due_lbl = tk.Label(meta_box, text=f"📅 {task.due_date}", font=("Segoe UI", 8), fg=due_fg, bg=WHITE)
            due_lbl.pack(side="left")

        # Action Buttons (Edit + Delete)
        actions = tk.Frame(card, bg=WHITE)
        actions.pack(side="right", padx=8)

        edit_btn = tk.Label(actions, text="✏", font=("Segoe UI Emoji", 11), fg=GRAY, bg=WHITE, cursor="hand2")
        edit_btn.pack(side="left", padx=4)
        edit_btn.bind("<Button-1>", lambda e, t=task: self.open_task_dialog(task=t))

        del_btn = tk.Label(actions, text="✕", font=("Segoe UI", 11, "bold"), fg="#CBD5E1", bg=WHITE, cursor="hand2")
        del_btn.pack(side="left", padx=4)
        del_btn.bind("<Button-1>", lambda e, t_id=task.id: self.prompt_delete_task(t_id))
        del_btn.bind("<Enter>", lambda e: del_btn.config(fg=DANGER))
        del_btn.bind("<Leave>", lambda e: del_btn.config(fg="#CBD5E1"))

    def toggle_task(self, task_id):
        try:
            self.manager.toggle_task(task_id)
            if self.active_category_data:
                self.show_category_detail(self.active_category_data)
            else:
                self.show_dashboard()
        except TaskManagerError as e:
            CustomPromptModal(self, title="Error", prompt=str(e))

    def prompt_delete_task(self, task_id):
        CustomConfirmModal(
            self,
            title="Delete Task",
            message="Are you sure you want to delete this task?",
            on_confirm=lambda: self.delete_task(task_id),
        )

    def delete_task(self, task_id):
        try:
            self.manager.delete_task(task_id)
            if self.active_category_data:
                self.show_category_detail(self.active_category_data)
            else:
                self.show_dashboard()
        except TaskManagerError as e:
            CustomPromptModal(self, title="Error", prompt=str(e))

    def open_task_dialog(self, task=None):
        cat = self.active_category_data["label"] if self.active_category_data else "Personal"
        CustomTaskModal(self, self.manager, category=cat, task=task, on_save=self.refresh_current_view)

    def refresh_current_view(self):
        if self.active_category_data:
            self.show_category_detail(self.active_category_data)
        else:
            self.show_dashboard()


if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
