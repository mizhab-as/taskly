"""
gui.py
------
Tkinter front-end for the Tudy mobile-first To-Do List application.

Visual language is modeled exactly on the supplied "Tudy" mobile app design:
    * Standard mobile device viewport (375x667 size constraint)
    * Multi-screen route framework (Onboarding -> Dashboard -> CategoryDetail)
    * Custom canvas-drawn check buttons with teal checks for completed tasks
    * Priority-coded indicators and dynamic state counters
    * Elegant rotating styling palette for user-created custom lists
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime

from app.task_manager import TaskManager, TaskManagerError
from app.models import Task, PRIORITIES

# ---- Design tokens (mirrors the reference mockup) -----------------------
YELLOW = "#FFCB3D"
YELLOW_DARK = "#F5B400"
CREAM = "#FFF7E0"
WHITE = "#FFFFFF"
INK = "#2B2B3C"
GRAY = "#8B8B96"
TEAL = "#17C3B2"
LINE = "#EFEFF3"

PRIORITY_COLORS = {"High": "#FF5D5D", "Medium": "#FFA53D", "Low": "#3DBE6C"}


class CanvasCheckbox(tk.Canvas):
    """Custom canvas-drawn checkbox that renders a flat rounded rectangle
    with a checkmark when selected, matching the high fidelity mockup."""
    def __init__(self, parent, checked=False, command=None, **kwargs):
        super().__init__(parent, width=20, height=20, bg=WHITE, highlightthickness=0, cursor="hand2", **kwargs)
        self.checked = checked
        self.command = command
        self.draw()
        self.bind("<Button-1>", self.on_click)

    def draw(self):
        self.delete("all")
        if self.checked:
            # Rounded checkbox filled in teal
            self.create_rectangle(1, 1, 19, 19, outline=TEAL, fill=TEAL, width=0)
            # White checkmark vector
            self.create_line(6, 10, 9, 13, 14, 7, fill=WHITE, width=2)
        else:
            # Unchecked checkbox with border
            self.create_rectangle(1, 1, 19, 19, outline="#C9C9D2", fill=WHITE, width=1.5)

    def toggle(self):
        self.checked = not self.checked
        self.draw()

    def on_click(self, event):
        self.toggle()
        if self.command:
            self.command(self.checked)


class FAB(tk.Canvas):
    """Floating Action Button matching the teal circular + element in the mockup."""
    def __init__(self, parent, command=None, **kwargs):
        super().__init__(parent, width=48, height=48, bg=WHITE, highlightthickness=0, cursor="hand2", **kwargs)
        self.command = command
        self.bind("<Button-1>", lambda e: self.click())
        self.create_oval(2, 2, 46, 46, fill=TEAL, outline="")
        self.create_text(24, 23, text="+", font=("Segoe UI", 24, "bold"), fill=WHITE)

    def click(self):
        if self.command:
            self.command()


class TodoApp(tk.Tk):
    def __init__(self, user_name: str = "Ender"):
        super().__init__()
        self.title("Tudy — Mobile Task Manager")
        
        # Constrain dimensions to a mobile viewport aspect ratio
        self.geometry("375x667")
        self.resizable(False, False)
        self.configure(bg=WHITE)

        self.manager = TaskManager(filepath="data/tasks.json")
        self.user_name = user_name
        self.active_category_data = None  # Stores dictionary of currently viewed category

        # Screen routing container
        self.screen_container = tk.Frame(self, bg=WHITE)
        self.screen_container.pack(fill="both", expand=True)

        # Route dynamically depending on onboarding state
        if not self.manager.onboarded:
            self.show_onboarding()
        else:
            self.show_dashboard()

    def clear_screen(self):
        for w in self.screen_container.winfo_children():
            w.destroy()

    # ------------------------------------------------------------------ #
    # Onboarding Screen View
    # ------------------------------------------------------------------ #
    def show_onboarding(self):
        self.clear_screen()
        
        # Outer Frame
        onboard = tk.Frame(self.screen_container, bg=WHITE)
        onboard.pack(fill="both", expand=True)

        # Spacing
        spacer = tk.Frame(onboard, bg=WHITE, height=70)
        spacer.pack()

        # Canvas for the giant yellow blob and emojis
        blob_canvas = tk.Canvas(onboard, width=180, height=180, bg=WHITE, highlightthickness=0)
        blob_canvas.pack(pady=20)
        blob_canvas.create_oval(5, 5, 175, 175, fill=YELLOW, outline="")
        blob_canvas.create_text(90, 85, text="🛍️📱", font=("Segoe UI Emoji", 48))

        # Title
        title_lbl = tk.Label(onboard, text="Get Organized Your Life", font=("Segoe UI", 18, "bold"), fg=INK, bg=WHITE)
        title_lbl.pack(pady=(20, 10))

        # Description
        desc_lbl = tk.Label(
            onboard,
            text="Tudy is a simple and effective to-do list and task manager app which helps you manage your time.",
            font=("Segoe UI", 10),
            fg=GRAY,
            bg=WHITE,
            wraplength=280,
            justify="center"
        )
        desc_lbl.pack(padx=30, pady=(0, 35))

        # CTA Button
        cta_btn = tk.Button(
            onboard,
            text="Get Started",
            bg=TEAL,
            fg=WHITE,
            font=("Segoe UI", 11, "bold"),
            bd=0,
            activebackground=TEAL,
            activeforeground=WHITE,
            cursor="hand2",
            padx=32,
            pady=8,
            command=self.complete_onboarding
        )
        cta_btn.pack(pady=10)
        cta_btn.bind("<Enter>", lambda e: cta_btn.config(bg="#12A794"))
        cta_btn.bind("<Leave>", lambda e: cta_btn.config(bg=TEAL))

    def complete_onboarding(self):
        self.manager.mark_onboarded()
        self.show_dashboard()

    # ------------------------------------------------------------------ #
    # Dashboard / Home Screen View
    # ------------------------------------------------------------------ #
    def show_dashboard(self):
        self.clear_screen()
        self.active_category_data = None

        # Outer Frame
        dash = tk.Frame(self.screen_container, bg=CREAM)
        dash.pack(fill="both", expand=True)

        # Header Panel
        header = tk.Frame(dash, bg=YELLOW, height=130)
        header.pack(fill="x")
        header.pack_propagate(False)

        top_row = tk.Frame(header, bg=YELLOW)
        top_row.pack(fill="x", padx=18, pady=(20, 0))

        # Decorative Menu Button
        menu_btn = tk.Label(top_row, text="☰", font=("Segoe UI", 16), bg=YELLOW, fg=INK, cursor="hand2")
        menu_btn.pack(side="left")
        menu_btn.bind("<Button-1>", lambda e: messagebox.showinfo("About Tudy", "Tudy v2.0 — An Advanced Mobile-First To-Do App."))

        # Greeting block
        greet_box = tk.Frame(header, bg=YELLOW)
        greet_box.pack(side="left", padx=18, pady=(10, 0))
        
        tk.Label(greet_box, text=f"Hello {self.user_name}", font=("Segoe UI", 17, "bold"), bg=YELLOW, fg=INK).pack(anchor="w")
        
        stats = self.manager.stats()
        today_tasks = stats.get("Today", 0)
        today_text = "Nothing due today — enjoy the calm." if today_tasks == 0 else f"Today you have {today_tasks} tasks"
        tk.Label(greet_box, text=today_text, font=("Segoe UI", 10), bg=YELLOW, fg="#6B5A12").pack(anchor="w")

        # Avatar Initial
        avatar = tk.Canvas(top_row, width=34, height=34, bg=YELLOW, highlightthickness=0)
        avatar.pack(side="right")
        avatar.create_oval(2, 2, 32, 32, fill=WHITE, outline="")
        avatar.create_text(17, 17, text=self.user_name[:1].upper(), font=("Segoe UI", 12, "bold"), fill=INK)

        # Categories Scrollable Area
        scroll_container = tk.Frame(dash, bg=CREAM)
        scroll_container.pack(fill="both", expand=True, padx=16, pady=(10, 16))

        # Canvas with scrollable content
        canvas = tk.Canvas(scroll_container, bg=CREAM, highlightthickness=0)
        vsb = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        cards_frame = tk.Frame(canvas, bg=CREAM)
        
        cards_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=cards_frame, anchor="nw", width=343) # Match width of canvas minus scrollbar margins
        canvas.configure(yscrollcommand=vsb.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        # Scrollbar is hidden for maximum visual clean style, but scroll binds still function
        cards_frame.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Render list of Category Cards
        categories = self.manager.get_categories()
        for cat in categories:
            self._build_category_card(cards_frame, cat, stats)

        # "+ Add list" Button Card at the bottom of the list
        add_cat_row = tk.Frame(cards_frame, bg=CREAM, height=52)
        add_cat_row.pack(fill="x", pady=6)
        add_cat_row.pack_propagate(False)

        add_cat_btn = tk.Button(
            add_cat_row,
            text="+ Add list",
            font=("Segoe UI", 11, "bold"),
            bg="#FFFFFF",
            fg=GRAY,
            activebackground=CREAM,
            activeforeground=TEAL,
            bd=0,
            cursor="hand2",
            command=self.open_new_list_dialog
        )
        add_cat_btn.pack(fill="both", expand=True)
        add_cat_btn.bind("<Enter>", lambda e: add_cat_btn.config(fg=TEAL))
        add_cat_btn.bind("<Leave>", lambda e: add_cat_btn.config(fg=GRAY))

    def _build_category_card(self, parent, cat, stats):
        card = tk.Frame(parent, bg=WHITE, bd=0, highlightthickness=0, height=64)
        card.pack(fill="x", pady=5)
        card.pack_propagate(False)

        # Trigger list view on click
        card.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        # Icon Chip
        chip = tk.Frame(card, bg=cat["bg"], width=38, height=38)
        chip.pack(side="left", padx=(14, 12), pady=13)
        chip.pack_propagate(False)
        chip.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        icon_lbl = tk.Label(chip, text=cat["icon"], font=("Segoe UI Emoji", 14), bg=cat["bg"], fg=cat["color"])
        icon_lbl.pack(fill="both", expand=True)
        icon_lbl.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        # Card Labels
        txt_box = tk.Frame(card, bg=WHITE)
        txt_box.pack(side="left", fill="y", pady=10)
        txt_box.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        label_lbl = tk.Label(txt_box, text=cat["label"], font=("Segoe UI", 12, "bold"), fg=INK, bg=WHITE)
        label_lbl.pack(anchor="w")
        label_lbl.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        count = stats.get(cat["label"], 0)
        count_lbl = tk.Label(txt_box, text=f"{count} Tasks", font=("Segoe UI", 9), fg=GRAY, bg=WHITE)
        count_lbl.pack(anchor="w")
        count_lbl.bind("<Button-1>", lambda e: self.show_category_detail(cat))

        # Overflow/Delete Option for custom categories
        if "smart" not in cat and cat["label"] not in ("Personal", "Work", "Shopping"):
            del_lbl = tk.Label(card, text="✕", font=("Segoe UI", 11, "bold"), fg="#D9C9C2", bg=WHITE, cursor="hand2")
            del_lbl.pack(side="right", padx=16)
            del_lbl.bind("<Button-1>", lambda e, c=cat: self.delete_category(c))
            del_lbl.bind("<Enter>", lambda e: del_lbl.config(fg="#FF5D5D"))
            del_lbl.bind("<Leave>", lambda e: del_lbl.config(fg="#D9C9C2"))

    def open_new_list_dialog(self):
        name = simpledialog.askstring("New list", "List name:")
        if name:
            name = name.strip()
            if name:
                try:
                    self.manager.add_category(name)
                    self.show_dashboard()
                except TaskManagerError as e:
                    messagebox.showerror("Error", str(e))

    def delete_category(self, cat):
        confirm = messagebox.askyesno(
            "Delete List",
            f"Are you sure you want to delete the list '{cat['label']}'?\n"
            "All tasks inside this list will be permanently deleted."
        )
        if confirm:
            self.manager.delete_category(cat["label"])
            self.show_dashboard()

    # ------------------------------------------------------------------ #
    # Category Detail Screen View
    # ------------------------------------------------------------------ #
    def show_category_detail(self, cat):
        self.clear_screen()
        self.active_category_data = cat

        # Outer Frame
        detail = tk.Frame(self.screen_container, bg=WHITE)
        detail.pack(fill="both", expand=True)

        # Header Panel
        header = tk.Frame(detail, bg=YELLOW, height=115)
        header.pack(fill="x")
        header.pack_propagate(False)

        top_row = tk.Frame(header, bg=YELLOW)
        top_row.pack(fill="x", padx=16, pady=(18, 0))

        # Navigation row
        back_btn = tk.Label(top_row, text="←", font=("Segoe UI", 15, "bold"), bg=YELLOW, fg=INK, cursor="hand2")
        back_btn.pack(side="left")
        back_btn.bind("<Button-1>", lambda e: self.show_dashboard())

        menu_btn = tk.Label(top_row, text="⋮", font=("Segoe UI", 16, "bold"), bg=YELLOW, fg=INK, cursor="hand2")
        menu_btn.pack(side="right")
        menu_btn.bind("<Button-1>", lambda e: self.open_category_menu(menu_btn))

        # Identity Row
        who = tk.Frame(header, bg=YELLOW)
        who.pack(fill="x", padx=16, pady=(8, 0))

        chip = tk.Frame(who, bg="#FCECB5", width=32, height=32)
        chip.pack(side="left", padx=(0, 8))
        chip.pack_propagate(False)

        icon_lbl = tk.Label(chip, text=cat["icon"], font=("Segoe UI Emoji", 13), bg="#FCECB5", fg=cat["color"])
        icon_lbl.pack(fill="both", expand=True)

        info_box = tk.Frame(who, bg=YELLOW)
        info_box.pack(side="left", padx=8)

        tasks = self.manager.list_by_category(cat["label"])
        open_count = sum(1 for t in tasks if not t.completed)
        self.open_count_lbl = tk.Label(info_box, text=f"{open_count} Tasks left", font=("Segoe UI", 9, "bold"), bg=YELLOW, fg="#6B5A12")
        self.open_count_lbl.pack(anchor="w")

        title_lbl = tk.Label(info_box, text=cat["label"], font=("Segoe UI", 18, "bold"), bg=YELLOW, fg=INK)
        title_lbl.pack(anchor="w")

        # Scrollable Task List Checklist
        list_container = tk.Frame(detail, bg=WHITE)
        list_container.pack(fill="both", expand=True, padx=16, pady=(10, 70)) # Padding bottom to leave room for FAB

        canvas = tk.Canvas(list_container, bg=WHITE, highlightthickness=0)
        vsb = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        task_rows_frame = tk.Frame(canvas, bg=WHITE)

        task_rows_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=task_rows_frame, anchor="nw", width=328)
        canvas.configure(yscrollcommand=vsb.set)

        canvas.pack(side="left", fill="both", expand=True)
        # Bind scrolling mousewheel
        task_rows_frame.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Render Checklist Items
        if not tasks:
            empty_lbl = tk.Label(task_rows_frame, text="Nothing here yet.\nTap the + button to add a task.",
                                 font=("Segoe UI", 10), fg=GRAY, bg=WHITE, justify="center")
            empty_lbl.pack(pady=40, fill="x")
        else:
            # Sort: incomplete first, then by priority, then by due date
            order = {"High": 0, "Medium": 1, "Low": 2}
            tasks.sort(key=lambda t: (t.completed, order.get(t.priority, 1), t.due_date or "9999-99-99"))
            
            for t in tasks:
                self._build_task_row(task_rows_frame, t)

        # Floating Action Button (FAB)
        fab = FAB(detail, command=self.open_task_dialog)
        fab.place(relx=1.0, rely=1.0, x=-24, y=-24, anchor="se")

    def _build_task_row(self, parent, task):
        row = tk.Frame(parent, bg=WHITE, height=44)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        # Custom Canvas Checkbox
        chk = CanvasCheckbox(row, checked=task.completed, command=lambda val, t_id=task.id: self.toggle_task(t_id))
        chk.pack(side="left", padx=(4, 8), pady=12)

        # Text labels - strike-through when completed
        font = ("Segoe UI", 11, "overstrike") if task.completed else ("Segoe UI", 11)
        color = GRAY if task.completed else INK
        title_lbl = tk.Label(row, text=task.title, font=font, fg=color, bg=WHITE, anchor="w", cursor="hand2")
        title_lbl.pack(side="left", fill="both", expand=True)
        title_lbl.bind("<Double-Button-1>", lambda e, t=task: self.open_task_dialog(task=t))

        # Show Priority Code (small filled oval) and date if set
        if not task.completed:
            meta_box = tk.Frame(row, bg=WHITE)
            meta_box.pack(side="right", padx=6)

            if task.due_date:
                tk.Label(meta_box, text=task.due_date, font=("Segoe UI", 9), fg=GRAY, bg=WHITE).pack(side="left", padx=4)

            prio_canvas = tk.Canvas(meta_box, width=10, height=10, bg=WHITE, highlightthickness=0)
            prio_canvas.pack(side="left", padx=2)
            prio_canvas.create_oval(1, 1, 9, 9, fill=PRIORITY_COLORS.get(task.priority, GRAY), outline="")

        # Delete Action Trigger
        del_btn = tk.Label(row, text="✕", font=("Segoe UI", 11, "bold"), fg="#D9C9C2", bg=WHITE, cursor="hand2")
        del_btn.pack(side="right", padx=(8, 4))
        del_btn.bind("<Button-1>", lambda e, t_id=task.id: self.delete_task(t_id))
        del_btn.bind("<Enter>", lambda e: del_btn.config(fg="#FF5D5D"))
        del_btn.bind("<Leave>", lambda e: del_btn.config(fg="#D9C9C2"))

        # Separator line
        sep = tk.Frame(parent, bg=LINE, height=1)
        sep.pack(fill="x", padx=4)

    def toggle_task(self, task_id):
        try:
            self.manager.toggle_task(task_id)
            if self.active_category_data:
                self.show_category_detail(self.active_category_data)
        except TaskManagerError as e:
            messagebox.showerror("Error", str(e))

    def delete_task(self, task_id):
        # Delete instantly matching React UX spec requirement 5
        try:
            self.manager.delete_task(task_id)
            if self.active_category_data:
                self.show_category_detail(self.active_category_data)
        except TaskManagerError as e:
            messagebox.showerror("Error", str(e))

    def open_category_menu(self, anchor):
        """Displays drop down menu with 'Clear completed'."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Clear completed", command=self.clear_completed)
        
        # Display menu directly under coordinates of ⋮ trigger
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height()
        menu.post(x, y)

    def clear_completed(self):
        if not self.active_category_data:
            return
        cat_label = self.active_category_data["label"]
        tasks = self.manager.list_by_category(cat_label)
        completed_ids = [t.id for t in tasks if t.completed]
        
        for t_id in completed_ids:
            self.manager.delete_task(t_id)
            
        self.show_category_detail(self.active_category_data)

    def open_task_dialog(self, task=None):
        cat = self.active_category_data["label"] if self.active_category_data else "Personal"
        TaskDialog(self, self.manager, category=cat, task=task, on_save=self.refresh_current_view)

    def refresh_current_view(self):
        if self.active_category_data:
            self.show_category_detail(self.active_category_data)
        else:
            self.show_dashboard()


class TaskDialog(tk.Toplevel):
    """Refactored Modal Dialog matching the theme styling of the application."""
    def __init__(self, parent, manager: TaskManager, category, task=None, on_save=None):
        super().__init__(parent)
        self.manager = manager
        self.task = task
        self.on_save = on_save
        
        self.title("Edit Task" if task else "Add Task")
        self.configure(bg=WHITE)
        self.geometry("340x350")
        self.resizable(False, False)
        self.grab_set()

        # Modal elements
        pad = {"padx": 20, "pady": 4}

        # Title entry
        tk.Label(self, text="Title", bg=WHITE, fg=INK, font=("Segoe UI", 10, "bold")).pack(anchor="w", **pad)
        self.title_var = tk.StringVar(value=task.title if task else "")
        title_ent = tk.Entry(self, textvariable=self.title_var, font=("Segoe UI", 11), bg=CREAM, bd=0, highlightthickness=1, highlightbackground=LINE, highlightcolor=YELLOW)
        title_ent.pack(fill="x", padx=20, ipady=4)
        title_ent.focus()

        # Category Combobox dropdown (excludes smart lists)
        tk.Label(self, text="Category", bg=WHITE, fg=INK, font=("Segoe UI", 10, "bold")).pack(anchor="w", **pad)
        
        # Pre-fill category contextually matching requirement 5.3 Add Task sheet
        default_cat = category
        if category in ("Today", "Planned"):
            default_cat = "Personal"
        
        self.cat_var = tk.StringVar(value=task.category if task else default_cat)
        cat_menu = tk.OptionMenu(self, self.cat_var, *manager.all_categories())
        cat_menu.config(bg=CREAM, fg=INK, bd=0, highlightthickness=0, font=("Segoe UI", 10))
        cat_menu.pack(fill="x", padx=20)

        # Priority selection dropdown
        tk.Label(self, text="Priority", bg=WHITE, fg=INK, font=("Segoe UI", 10, "bold")).pack(anchor="w", **pad)
        self.prio_var = tk.StringVar(value=task.priority if task else "Medium")
        prio_menu = tk.OptionMenu(self, self.prio_var, *PRIORITIES)
        prio_menu.config(bg=CREAM, fg=INK, bd=0, highlightthickness=0, font=("Segoe UI", 10))
        prio_menu.pack(fill="x", padx=20)

        # Due Date entry
        tk.Label(self, text="Due Date (YYYY-MM-DD, optional)", bg=WHITE, fg=INK, font=("Segoe UI", 10, "bold")).pack(anchor="w", **pad)
        
        # Pre-fill due date as today's date if viewing Today/Planned context
        default_due = ""
        if not task and category in ("Today", "Planned"):
            default_due = datetime.now().strftime("%Y-%m-%d")
        else:
            default_due = task.due_date if task else ""
            
        self.due_var = tk.StringVar(value=default_due)
        due_ent = tk.Entry(self, textvariable=self.due_var, font=("Segoe UI", 11), bg=CREAM, bd=0, highlightthickness=1, highlightbackground=LINE, highlightcolor=YELLOW)
        due_ent.pack(fill="x", padx=20, ipady=4)

        # Action Buttons
        btn_frame = tk.Frame(self, bg=WHITE)
        btn_frame.pack(pady=20)
        
        save_btn = tk.Button(
            btn_frame,
            text="Save",
            bg=TEAL,
            fg=WHITE,
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=20,
            pady=6,
            command=self.save,
            cursor="hand2"
        )
        save_btn.pack(side="left", padx=6)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            bg="#F0F0F3",
            fg=INK,
            font=("Segoe UI", 10),
            bd=0,
            padx=16,
            pady=6,
            command=self.destroy,
            cursor="hand2"
        )
        cancel_btn.pack(side="left", padx=6)

    def save(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Invalid Task", "Task title cannot be empty.")
            return

        due_date = self.due_var.get().strip()
        
        try:
            if self.task:
                self.manager.edit_task(
                    self.task.id,
                    title=title,
                    category=self.cat_var.get(),
                    priority=self.prio_var.get(),
                    due_date=due_date,
                )
            else:
                self.manager.add_task(
                    title=title,
                    category=self.cat_var.get(),
                    priority=self.prio_var.get(),
                    due_date=due_date,
                )
        except TaskManagerError as e:
            messagebox.showerror("Invalid Task", str(e))
            return

        if self.on_save:
            self.on_save()
        self.destroy()
