"""
app_gui.py
SHOX — Ultra-Modern, Crisp Dark Desktop UI for System Usage & Freeze Guardian.
High-DPI Aware (Zero Blur), Obsidian-Slate Aesthetic, Sleek Micro-Bars & Responsive Controls.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
from ctypes import wintypes
import threading
import time

# --- Enable Windows High-DPI Awareness (Fixes Blurry Fonts completely) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from monitor_engine import SystemMonitorEngine
from alert_manager import AlertManager
from toast_popup import show_toast_popup

# --- Modern Design System & Color Palette ---
C_BG_ROOT = "#0a0c10"        # Deep Obsidian Charcoal
C_BG_HEADER = "#0e1117"      # Elevated Header Dark
C_BG_CARD = "#14171f"        # Sleek Card Surface
C_BG_ROW_ALT = "#12141c"     # Alternating Table Row
C_BORDER = "#222633"         # Subtle 1px Crisp Border
C_BORDER_ACCENT = "#303648"  # Active/Hover Border

C_TXT_MAIN = "#f8fafc"       # Crisp Pure White
C_TXT_SUB = "#94a3b8"        # Soft Slate
C_TXT_MUTED = "#64748b"      # Muted Graphite

# Vibrant Accent Highlights
C_ACCENT_CYAN = "#38bdf8"    # CPU Neon Sky
C_ACCENT_VIOLET = "#a78bfa"  # RAM Soft Violet
C_ACCENT_GREEN = "#34d399"   # Healthy Emerald
C_ACCENT_AMBER = "#fbbf24"   # Warning Warm Amber
C_ACCENT_ROSE = "#f43f5e"    # Critical Frozen Red
C_ACCENT_INDIGO = "#6366f1"  # Mini View Pill


class ModernProgressBar(tk.Canvas):
    """Ultra-clean, modern canvas progress bar with smooth rounded pill look."""
    def __init__(self, parent, height=6, bg_color="#202430", fill_color=C_ACCENT_CYAN, **kwargs):
        super().__init__(parent, height=height, bg=parent["bg"], highlightthickness=0, bd=0, **kwargs)
        self.height = height
        self.bg_color = bg_color
        self.fill_color = fill_color
        self.value = 0
        self.bind("<Configure>", self._draw)

    def set_value(self, val):
        self.value = max(0.0, min(100.0, float(val)))
        self._draw()

    def set_color(self, color):
        self.fill_color = color
        self._draw()

    def _draw(self, event=None):
        self.delete("all")
        w = self.winfo_width()
        h = self.height
        if w <= 1:
            return
        # Background Track
        self.create_rectangle(0, 1, w, h - 1, fill=self.bg_color, outline="")
        # Active Fill
        fill_w = int((self.value / 100.0) * w)
        if fill_w > 0:
            self.create_rectangle(0, 1, fill_w, h - 1, fill=self.fill_color, outline="")


class ModernSystemWatchdogApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SHOX — System Performance & Freeze Guardian")
        self.root.geometry("1100x740")
        self.root.minsize(960, 620)
        self.root.configure(bg=C_BG_ROOT)

        # Apply Window Icon
        try:
            import os
            icon_path = os.path.join(os.path.dirname(__file__), "shox.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

        # Engines
        self.engine = SystemMonitorEngine()
        self.alert_mgr = AlertManager()

        # Monitoring State
        self.is_monitoring = True
        self.refresh_interval = 1.0
        self.selected_pid = None
        self.search_filter = ""
        self.sort_criterion = "ram"
        self.monitor_thread = None

        self._setup_styles()
        self._build_header()
        self._build_metric_cards()
        self._build_alerts_section()
        self._build_main_tabs()
        self._build_status_bar()

        self.start_monitoring_thread()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Clean Flat Notebook Tabs
        style.configure("TNotebook", background=C_BG_ROOT, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#161922",
            foreground=C_TXT_SUB,
            padding=[18, 9],
            font=("Segoe UI", 9, "bold"),
            borderwidth=0
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", C_BG_CARD)],
            foreground=[("selected", C_TXT_MAIN)]
        )

        # High-Contrast Modern Treeview
        style.configure(
            "Treeview",
            background=C_BG_CARD,
            foreground="#e2e8f0",
            fieldbackground=C_BG_CARD,
            rowheight=32,
            font=("Segoe UI", 9),
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background="#1c202a",
            foreground=C_TXT_SUB,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=[8, 8]
        )
        style.map(
            "Treeview",
            background=[("selected", "#2d3345")],
            foreground=[("selected", "#ffffff")]
        )

        # Modern Scrollbars
        style.configure(
            "Vertical.TScrollbar",
            troughcolor=C_BG_ROOT,
            background="#252a38",
            bordercolor=C_BG_ROOT,
            arrowcolor=C_TXT_MUTED,
            relief="flat",
            width=10
        )

        # Sliders
        style.configure("Horizontal.TScale", troughcolor="#202430", background=C_ACCENT_CYAN, borderwidth=0)

    def _build_header(self):
        header = tk.Frame(self.root, bg=C_BG_HEADER, height=58, highlightbackground=C_BORDER, highlightthickness=1)
        header.pack(fill="x", side="top")

        title_box = tk.Frame(header, bg=C_BG_HEADER)
        title_box.pack(side="left", padx=20, pady=11)

        # App Logo / Icon in Header
        self.header_logo_img = None
        try:
            import os
            logo_path = os.path.join(os.path.dirname(__file__), "shox_logo.png")
            if os.path.exists(logo_path):
                raw_img = tk.PhotoImage(file=logo_path)
                # Subsample 1024x1024 by 32 to get crisp ~32x32 icon
                self.header_logo_img = raw_img.subsample(32, 32)
        except Exception:
            self.header_logo_img = None

        if self.header_logo_img:
            logo_badge = tk.Label(
                title_box,
                image=self.header_logo_img,
                bg=C_BG_HEADER
            )
        else:
            logo_badge = tk.Label(
                title_box,
                text="⚡",
                font=("Segoe UI", 12, "bold"),
                fg=C_ACCENT_CYAN,
                bg="#182535",
                padx=8,
                pady=2,
                relief="flat"
            )
        logo_badge.pack(side="left", padx=(0, 10))

        app_title = tk.Label(
            title_box,
            text="SHOX",
            font=("Segoe UI", 13, "bold"),
            fg=C_TXT_MAIN,
            bg=C_BG_HEADER
        )
        app_title.pack(side="left")

        app_sub = tk.Label(
            title_box,
            text="PRO  •  Real-time Performance & Freeze Watchdog",
            font=("Segoe UI", 9),
            fg=C_TXT_MUTED,
            bg=C_BG_HEADER
        )
        app_sub.pack(side="left", padx=(8, 0))

        # Top Control Action Buttons
        btn_box = tk.Frame(header, bg=C_BG_HEADER)
        btn_box.pack(side="right", padx=20, pady=11)

        # Mini Bar Mode Button (Vibrant Indigo Pill)
        self.mini_btn = tk.Button(
            btn_box,
            text="📌 Mini Bar View",
            command=self.switch_to_mini_view,
            bg="#312e81",
            fg="#e0e7ff",
            activebackground="#4338ca",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2"
        )
        self.mini_btn.pack(side="left", padx=(0, 8))

        # Pause / Resume Button
        self.pause_btn = tk.Button(
            btn_box,
            text="⏸️ Pause",
            command=self.toggle_pause,
            bg="#1e2330",
            fg=C_TXT_SUB,
            activebackground="#2a3142",
            activeforeground=C_TXT_MAIN,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2"
        )
        self.pause_btn.pack(side="left", padx=(0, 8))

        # Refresh Button
        refresh_btn = tk.Button(
            btn_box,
            text="🔄 Refresh",
            command=self.manual_refresh,
            bg="#065f46",
            fg="#ecfdf5",
            activebackground="#047857",
            activeforeground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2"
        )
        refresh_btn.pack(side="left")

    def _build_metric_cards(self):
        cards_frame = tk.Frame(self.root, bg=C_BG_ROOT)
        cards_frame.pack(fill="x", padx=20, pady=(14, 8))

        for i in range(4):
            cards_frame.columnconfigure(i, weight=1)

        # Card 1: CPU Usage
        self.cpu_card = self._create_card(cards_frame, 0, "● CPU LOAD", "0%", C_ACCENT_CYAN)
        self.cpu_val_lbl = self.cpu_card["val_lbl"]
        self.cpu_sub_lbl = self.cpu_card["sub_lbl"]
        self.cpu_bar = self.cpu_card["bar"]

        # Card 2: RAM Memory
        self.ram_card = self._create_card(cards_frame, 1, "● RAM MEMORY", "0%", C_ACCENT_VIOLET)
        self.ram_val_lbl = self.ram_card["val_lbl"]
        self.ram_sub_lbl = self.ram_card["sub_lbl"]
        self.ram_bar = self.ram_card["bar"]

        # Card 3: Disk C:
        self.disk_card = self._create_card(cards_frame, 2, "● STORAGE (C:)", "0%", C_ACCENT_GREEN)
        self.disk_val_lbl = self.disk_card["val_lbl"]
        self.disk_sub_lbl = self.disk_card["sub_lbl"]
        self.disk_bar = self.disk_card["bar"]

        # Card 4: Health Status
        self.status_card = self._create_card(cards_frame, 3, "● SYSTEM HEALTH", "HEALTHY", C_ACCENT_GREEN, is_status=True)
        self.health_val_lbl = self.status_card["val_lbl"]
        self.health_sub_lbl = self.status_card["sub_lbl"]

    def _create_card(self, parent, col, title, initial_val, accent_color, is_status=False):
        card = tk.Frame(
            parent,
            bg=C_BG_CARD,
            highlightbackground=C_BORDER,
            highlightthickness=1,
            bd=0
        )
        card.grid(row=0, column=col, sticky="nsew", padx=6, pady=4)

        t_lbl = tk.Label(
            card,
            text=title,
            font=("Segoe UI", 8, "bold"),
            fg=accent_color,
            bg=C_BG_CARD
        )
        t_lbl.pack(anchor="w", padx=16, pady=(12, 2))

        val_lbl = tk.Label(
            card,
            text=initial_val,
            font=("Segoe UI", 22, "bold"),
            fg=C_TXT_MAIN,
            bg=C_BG_CARD
        )
        val_lbl.pack(anchor="w", padx=16, pady=(0, 4))

        bar = None
        if not is_status:
            bar = ModernProgressBar(card, height=5, fill_color=accent_color)
            bar.pack(fill="x", padx=16, pady=(2, 8))

        sub_lbl = tk.Label(
            card,
            text="Calculating..." if not is_status else "All applications responsive",
            font=("Segoe UI", 8),
            fg=C_TXT_MUTED,
            bg=C_BG_CARD
        )
        sub_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        return {"val_lbl": val_lbl, "sub_lbl": sub_lbl, "bar": bar, "frame": card}

    def _build_alerts_section(self):
        self.alerts_frame = tk.Frame(self.root, bg=C_BG_ROOT)
        self.alerts_frame.pack(fill="x", padx=20, pady=(2, 10))

        # Sleek banner with subtle border
        self.alert_banner = tk.Frame(
            self.alerts_frame,
            bg="#141c18",
            highlightbackground="#1b3d2b",
            highlightthickness=1,
            bd=0
        )
        self.alert_banner.pack(fill="x")

        self.alert_text_lbl = tk.Label(
            self.alert_banner,
            text="● Watchdog Active: All running applications are responsive and within normal thresholds.",
            font=("Segoe UI", 9),
            fg=C_ACCENT_GREEN,
            bg="#141c18",
            padx=14,
            pady=9
        )
        self.alert_text_lbl.pack(side="left")

        self.alert_kill_btn = tk.Button(
            self.alert_banner,
            text="⛔ Force Kill Frozen App",
            command=self.kill_first_hung_app,
            bg="#e11d48",
            fg="white",
            activebackground="#be123c",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2"
        )
        self.alert_kill_btn.pack_forget()

    def _build_main_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(2, 8))

        # Tab 1: Running Processes
        self.tab_proc = tk.Frame(self.notebook, bg=C_BG_ROOT)
        self.notebook.add(self.tab_proc, text="  ⚡ Active Processes  ")
        self._build_processes_tab()

        # Tab 2: Alert History Log
        self.tab_history = tk.Frame(self.notebook, bg=C_BG_ROOT)
        self.notebook.add(self.tab_history, text="  📜 Alert History  ")
        self._build_history_tab()

        # Tab 3: Alert Thresholds & Settings
        self.tab_settings = tk.Frame(self.notebook, bg=C_BG_ROOT)
        self.notebook.add(self.tab_settings, text="  ⚙️ Watchdog Settings  ")
        self._build_settings_tab()

    def _build_processes_tab(self):
        toolbar = tk.Frame(self.tab_proc, bg=C_BG_ROOT)
        toolbar.pack(fill="x", pady=(10, 8))

        # Search Bar
        search_box = tk.Frame(toolbar, bg="#161922", highlightbackground=C_BORDER, highlightthickness=1)
        search_box.pack(side="left", padx=(0, 14))

        tk.Label(search_box, text="🔍", font=("Segoe UI", 9), fg=C_TXT_MUTED, bg="#161922").pack(side="left", padx=(8, 2))
        self.search_entry = tk.Entry(
            search_box,
            font=("Segoe UI", 9),
            bg="#161922",
            fg=C_TXT_MAIN,
            insertbackground=C_ACCENT_CYAN,
            relief="flat",
            width=24
        )
        self.search_entry.pack(side="left", ipady=4, padx=(2, 8))
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

        # Sort Filter
        tk.Label(toolbar, text="Sort by:", font=("Segoe UI", 9), fg=C_TXT_MUTED, bg=C_BG_ROOT).pack(side="left", padx=(0, 6))

        self.sort_var = tk.StringVar(value="RAM (Highest)")
        sort_combo = ttk.Combobox(
            toolbar,
            textvariable=self.sort_var,
            values=["RAM (Highest)", "CPU (Highest)", "Not Responding First", "Process Name (A-Z)"],
            state="readonly",
            width=19
        )
        sort_combo.pack(side="left", padx=(0, 14))
        sort_combo.bind("<<ComboboxSelected>>", self.on_sort_change)

        # End Task Action Button
        self.end_task_btn = tk.Button(
            toolbar,
            text="⛔ End Task / Terminate",
            command=self.kill_selected_process,
            bg="#be123c",
            fg="white",
            activebackground="#9f1239",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2"
        )
        self.end_task_btn.pack(side="right")

        # Table Container
        table_container = tk.Frame(self.tab_proc, bg=C_BG_CARD, highlightbackground=C_BORDER, highlightthickness=1)
        table_container.pack(fill="both", expand=True)

        cols = ("name", "pid", "ram", "cpu", "status", "title")
        self.proc_tree = ttk.Treeview(
            table_container,
            columns=cols,
            show="headings",
            selectmode="browse"
        )

        self.proc_tree.heading("name", text="APPLICATION", anchor="w")
        self.proc_tree.heading("pid", text="PID", anchor="center")
        self.proc_tree.heading("ram", text="RAM (MB)", anchor="e")
        self.proc_tree.heading("cpu", text="CPU (%)", anchor="e")
        self.proc_tree.heading("status", text="STATUS", anchor="w")
        self.proc_tree.heading("title", text="WINDOW TITLE", anchor="w")

        self.proc_tree.column("name", width=190, minwidth=130)
        self.proc_tree.column("pid", width=80, minwidth=60, anchor="center")
        self.proc_tree.column("ram", width=110, minwidth=80, anchor="e")
        self.proc_tree.column("cpu", width=95, minwidth=70, anchor="e")
        self.proc_tree.column("status", width=180, minwidth=140)
        self.proc_tree.column("title", width=360, minwidth=180)

        # Row styling tags (Modern high-contrast palette)
        self.proc_tree.tag_configure("hung", background="#381318", foreground="#fda4af")
        self.proc_tree.tag_configure("high_ram", background="#2a1f11", foreground="#fcd34d")
        self.proc_tree.tag_configure("high_cpu", background="#152636", foreground="#7dd3fc")
        self.proc_tree.tag_configure("normal", background=C_BG_CARD, foreground="#cbd5e1")
        self.proc_tree.tag_configure("normal_alt", background=C_BG_ROW_ALT, foreground="#cbd5e1")

        v_scroll = ttk.Scrollbar(table_container, orient="vertical", command=self.proc_tree.yview)
        self.proc_tree.configure(yscrollcommand=v_scroll.set)

        self.proc_tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        self.proc_tree.bind("<<TreeviewSelect>>", self.on_process_selected)
        self.proc_tree.bind("<Double-1>", lambda e: self.kill_selected_process())

    def _build_history_tab(self):
        history_toolbar = tk.Frame(self.tab_history, bg=C_BG_ROOT)
        history_toolbar.pack(fill="x", pady=(10, 8))

        tk.Label(
            history_toolbar,
            text="Logged Triggers & Sustained (> 1 Min) Resource Events:",
            font=("Segoe UI", 9),
            fg=C_TXT_MUTED,
            bg=C_BG_ROOT
        ).pack(side="left")

        tk.Button(
            history_toolbar,
            text="🗑️ Clear Log",
            command=self.clear_alert_history,
            bg="#1e2330",
            fg=C_TXT_SUB,
            activebackground="#2a3142",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2"
        ).pack(side="right")

        hist_container = tk.Frame(self.tab_history, bg=C_BG_CARD, highlightbackground=C_BORDER, highlightthickness=1)
        hist_container.pack(fill="both", expand=True)

        cols = ("time", "severity", "type", "name", "pid", "message")
        self.hist_tree = ttk.Treeview(hist_container, columns=cols, show="headings", selectmode="browse")
        self.hist_tree.heading("time", text="TIME", anchor="center")
        self.hist_tree.heading("severity", text="SEVERITY", anchor="center")
        self.hist_tree.heading("type", text="TYPE", anchor="w")
        self.hist_tree.heading("name", text="PROCESS", anchor="w")
        self.hist_tree.heading("pid", text="PID", anchor="center")
        self.hist_tree.heading("message", text="DETAILS", anchor="w")

        self.hist_tree.column("time", width=90, anchor="center")
        self.hist_tree.column("severity", width=100, anchor="center")
        self.hist_tree.column("type", width=120)
        self.hist_tree.column("name", width=170)
        self.hist_tree.column("pid", width=75, anchor="center")
        self.hist_tree.column("message", width=460)

        self.hist_tree.tag_configure("CRITICAL", background="#381318", foreground="#fda4af")
        self.hist_tree.tag_configure("WARNING", background="#2a1f11", foreground="#fcd34d")

        h_scroll = ttk.Scrollbar(hist_container, orient="vertical", command=self.hist_tree.yview)
        self.hist_tree.configure(yscrollcommand=h_scroll.set)
        self.hist_tree.pack(side="left", fill="both", expand=True)
        h_scroll.pack(side="right", fill="y")

    def _build_settings_tab(self):
        container = tk.Frame(self.tab_settings, bg=C_BG_ROOT)
        container.pack(fill="both", expand=True, padx=20, pady=15)

        card = tk.Frame(container, bg=C_BG_CARD, highlightbackground=C_BORDER, highlightthickness=1)
        card.pack(fill="x", pady=8, ipady=12)

        tk.Label(
            card,
            text="⚙️ Alert & Threshold Configuration",
            font=("Segoe UI", 11, "bold"),
            fg=C_TXT_MAIN,
            bg=C_BG_CARD
        ).pack(anchor="w", padx=20, pady=(14, 16))

        # Setting 1: Process RAM Alert Slider
        s1 = tk.Frame(card, bg=C_BG_CARD)
        s1.pack(fill="x", padx=20, pady=6)
        self.ram_val_display = tk.Label(s1, text="500 MB", font=("Segoe UI", 9, "bold"), fg=C_ACCENT_VIOLET, bg=C_BG_CARD)
        self.ram_val_display.pack(side="right")
        tk.Label(s1, text="Process High RAM Alert Threshold (MB):", font=("Segoe UI", 9), fg=C_TXT_SUB, bg=C_BG_CARD).pack(side="left")

        self.ram_slider = ttk.Scale(
            card, from_=100, to=3000, value=self.alert_mgr.ram_threshold_mb,
            command=lambda v: self.ram_val_display.config(text=f"{int(float(v))} MB")
        )
        self.ram_slider.pack(fill="x", padx=20, pady=(0, 10))

        # Setting 2: Process CPU Alert Slider
        s2 = tk.Frame(card, bg=C_BG_CARD)
        s2.pack(fill="x", padx=20, pady=6)
        self.cpu_val_display = tk.Label(s2, text="30%", font=("Segoe UI", 9, "bold"), fg=C_ACCENT_CYAN, bg=C_BG_CARD)
        self.cpu_val_display.pack(side="right")
        tk.Label(s2, text="Process High CPU Alert Threshold (%):", font=("Segoe UI", 9), fg=C_TXT_SUB, bg=C_BG_CARD).pack(side="left")

        self.cpu_slider = ttk.Scale(
            card, from_=5, to=90, value=self.alert_mgr.cpu_threshold_pct,
            command=lambda v: self.cpu_val_display.config(text=f"{int(float(v))}%")
        )
        self.cpu_slider.pack(fill="x", padx=20, pady=(0, 10))

        # Setting 3: Sustained Duration Slider (1-Minute Rule)
        s3 = tk.Frame(card, bg=C_BG_CARD)
        s3.pack(fill="x", padx=20, pady=6)
        self.duration_display = tk.Label(s3, text="60 sec (1 min)", font=("Segoe UI", 9, "bold"), fg=C_ACCENT_GREEN, bg=C_BG_CARD)
        self.duration_display.pack(side="right")
        tk.Label(s3, text="Sustained Duration Required Before Alert Popup:", font=("Segoe UI", 9), fg=C_TXT_SUB, bg=C_BG_CARD).pack(side="left")

        self.duration_slider = ttk.Scale(
            card, from_=15, to=300, value=self.alert_mgr.sustained_duration_sec,
            command=lambda v: self.duration_display.config(
                text=f"{int(float(v))} sec ({int(float(v))//60}m {int(float(v))%60}s)" if int(float(v)) >= 60 else f"{int(float(v))} sec"
            )
        )
        self.duration_slider.pack(fill="x", padx=20, pady=(0, 10))

        # Setting 4: Audio Sound Checkbox (Default False)
        s4 = tk.Frame(card, bg=C_BG_CARD)
        s4.pack(fill="x", padx=20, pady=10)

        self.sound_var = tk.BooleanVar(value=False)
        sound_chk = tk.Checkbutton(
            s4,
            text="🔊 Enable Audio Beep Sound (Disabled by default for silent operation)",
            variable=self.sound_var,
            font=("Segoe UI", 9),
            fg=C_TXT_SUB,
            bg=C_BG_CARD,
            selectcolor="#0f1219",
            activebackground=C_BG_CARD,
            activeforeground=C_ACCENT_CYAN
        )
        sound_chk.pack(side="left")

        # Save Button
        apply_btn = tk.Button(
            card,
            text="💾 Save & Apply Settings",
            command=self.save_settings,
            bg="#065f46",
            fg="#ecfdf5",
            activebackground="#047857",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=18,
            pady=6,
            cursor="hand2"
        )
        apply_btn.pack(anchor="e", padx=20, pady=(10, 5))

    def _build_status_bar(self):
        self.status_bar = tk.Frame(self.root, bg=C_BG_HEADER, height=30, highlightbackground=C_BORDER, highlightthickness=1)
        self.status_bar.pack(fill="x", side="bottom")

        self.status_procs_lbl = tk.Label(
            self.status_bar,
            text="Scanning processes...",
            font=("Segoe UI", 8),
            fg=C_TXT_MUTED,
            bg=C_BG_HEADER
        )
        self.status_procs_lbl.pack(side="left", padx=16, pady=5)

        self.status_update_lbl = tk.Label(
            self.status_bar,
            text="● Live Monitoring Active",
            font=("Segoe UI", 8),
            fg=C_ACCENT_GREEN,
            bg=C_BG_HEADER
        )
        self.status_update_lbl.pack(side="right", padx=16, pady=5)

    # --- Actions & Handlers ---
    def toggle_pause(self):
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.pause_btn.config(text="⏸️ Pause", bg="#1e2330")
            self.status_update_lbl.config(text="● Live Monitoring Active", fg=C_ACCENT_GREEN)
        else:
            self.pause_btn.config(text="▶️ Resume", bg="#4338ca")
            self.status_update_lbl.config(text="● Monitoring Paused", fg=C_ACCENT_AMBER)

    def manual_refresh(self):
        threading.Thread(target=self._update_cycle, daemon=True).start()

    def on_search_change(self, event=None):
        self.search_filter = self.search_entry.get().strip().lower()

    def on_sort_change(self, event=None):
        val = self.sort_var.get()
        if "RAM" in val:
            self.sort_criterion = "ram"
        elif "CPU" in val:
            self.sort_criterion = "cpu"
        elif "Not Responding" in val:
            self.sort_criterion = "hung"
        else:
            self.sort_criterion = "name"

    def on_process_selected(self, event=None):
        selected_item = self.proc_tree.selection()
        if selected_item:
            values = self.proc_tree.item(selected_item[0], "values")
            if values:
                self.selected_pid = int(values[1])
                self.end_task_btn.config(text=f"⛔ End Task ({values[0]} : {self.selected_pid})")

    def kill_selected_process(self):
        if not self.selected_pid:
            messagebox.showinfo("Select Process", "Please select a process from the list first.")
            return

        confirm = messagebox.askyesno(
            "Confirm End Task",
            f"Are you sure you want to terminate process PID {self.selected_pid}?\nUnsaved data in that application may be lost."
        )
        if confirm:
            success, msg = self.engine.kill_process(self.selected_pid)
            if success:
                messagebox.showinfo("Success", msg)
                self.manual_refresh()
            else:
                messagebox.showerror("Error", msg)

    def kill_first_hung_app(self):
        for alert in self.alert_mgr.active_alerts:
            if alert.get("type") == "HUNG" and alert.get("pid"):
                pid = alert["pid"]
                name = alert["name"]
                confirm = messagebox.askyesno(
                    "Kill Frozen App",
                    f"Terminate unresponsive app '{name}' (PID {pid}) now?"
                )
                if confirm:
                    success, msg = self.engine.kill_process(pid)
                    if success:
                        messagebox.showinfo("Terminated", msg)
                        self.manual_refresh()
                    else:
                        messagebox.showerror("Error", msg)
                break

    def _popup_kill_callback(self, pid, name):
        confirm = messagebox.askyesno(
            "End Task",
            f"Are you sure you want to terminate '{name}' (PID {pid})?"
        )
        if confirm:
            success, msg = self.engine.kill_process(pid)
            if success:
                messagebox.showinfo("Terminated", f"'{name}' (PID {pid}) was terminated.")
                self.manual_refresh()
            else:
                messagebox.showerror("Error", msg)

    def clear_alert_history(self):
        self.alert_mgr.clear_history()
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)

    def save_settings(self):
        ram_val = self.ram_slider.get()
        cpu_val = self.cpu_slider.get()
        sound_val = self.sound_var.get()
        duration_val = self.duration_slider.get()

        self.alert_mgr.set_thresholds(
            ram_mb=ram_val,
            cpu_pct=cpu_val,
            sound=sound_val,
            sustained_sec=duration_val
        )
        messagebox.showinfo("Settings Saved", "Watchdog settings successfully updated!")

    # --- Background Monitoring Loop ---
    def start_monitoring_thread(self):
        self.monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self.monitor_thread.start()

    def _monitor_worker(self):
        while True:
            if self.is_monitoring:
                self._update_cycle()
            time.sleep(self.refresh_interval)

    def _update_cycle(self):
        try:
            cpu_pct = self.engine.get_system_cpu_percent()
            mem_stats = self.engine.get_memory_stats()
            disk_stats = self.engine.get_disk_stats("C:\\")
            processes = self.engine.get_processes()

            sys_summary = {
                "cpu_percent": cpu_pct,
                "ram_percent": mem_stats["percent"],
                "disk_percent": disk_stats["percent"]
            }
            active_alerts = self.alert_mgr.evaluate(sys_summary, processes)

            self.root.after(0, self._render_ui_updates, cpu_pct, mem_stats, disk_stats, processes, active_alerts)
        except Exception:
            pass

    def _render_ui_updates(self, cpu_pct, mem_stats, disk_stats, processes, active_alerts):
        # Update Metric Cards
        self.cpu_val_lbl.config(text=f"{cpu_pct:.0f}%")
        self.cpu_bar.set_value(cpu_pct)
        self.cpu_sub_lbl.config(text=f"⚡ {len(processes)} active tasks")

        ram_pct = mem_stats["percent"]
        self.ram_val_lbl.config(text=f"{ram_pct}%")
        self.ram_bar.set_value(ram_pct)
        self.ram_sub_lbl.config(text=f"💾 {mem_stats['used_gb']} GB of {mem_stats['total_gb']} GB Used")

        disk_pct = disk_stats["percent"]
        self.disk_val_lbl.config(text=f"{disk_pct:.0f}%")
        self.disk_bar.set_value(disk_pct)
        self.disk_sub_lbl.config(text=f"💿 {disk_stats['free_gb']} GB free of {disk_stats['total_gb']} GB")

        # Update Health Status Card & Alerts Banner
        hung_count = sum(1 for a in active_alerts if a["type"] == "HUNG")
        high_res_count = sum(1 for a in active_alerts if a["type"] in ("HIGH_RAM", "HIGH_CPU"))

        if hung_count > 0:
            self.health_val_lbl.config(text=f"⚠️ {hung_count} FROZEN", fg=C_ACCENT_ROSE)
            self.health_sub_lbl.config(text="App(s) Not Responding to Windows!")
            self.alert_banner.config(bg="#2b1115", highlightbackground="#5c1d24")
            self.alert_text_lbl.config(
                text=f"🚨 CRITICAL ALERT: {hung_count} application is NOT RESPONDING (HUNG)! Click below to force kill.",
                fg=C_ACCENT_ROSE,
                bg="#2b1115"
            )
            self.alert_kill_btn.pack(side="right", padx=14, pady=6)
        elif high_res_count > 0:
            self.health_val_lbl.config(text=f"⚡ {high_res_count} HEAVY", fg=C_ACCENT_AMBER)
            self.health_sub_lbl.config(text="Apps exceeding sustained 1-min limit")
            self.alert_banner.config(bg="#261b0e", highlightbackground="#543818")
            self.alert_text_lbl.config(
                text=f"⚠️ NOTICE: {high_res_count} process(es) sustained heavy usage for > 1 minute. Check the process list.",
                fg=C_ACCENT_AMBER,
                bg="#261b0e"
            )
            self.alert_kill_btn.pack_forget()
        else:
            self.health_val_lbl.config(text="HEALTHY", fg=C_ACCENT_GREEN)
            self.health_sub_lbl.config(text="All applications responsive")
            self.alert_banner.config(bg="#141c18", highlightbackground="#1b3d2b")
            self.alert_text_lbl.config(
                text="● Watchdog Active: All running applications are responsive and within normal thresholds.",
                fg=C_ACCENT_GREEN,
                bg="#141c18"
            )
            self.alert_kill_btn.pack_forget()

        # Check and trigger Toast Popups (only when sustained for > 1 minute or on freeze)
        pending_popups = self.alert_mgr.pop_pending_notifications()
        for alert_item in pending_popups:
            show_toast_popup(alert_item, kill_callback=self._popup_kill_callback)

        # Filter & Sort Processes
        filtered = []
        q = self.search_filter
        for p in processes:
            if not q or (q in p["name"].lower()) or (q in str(p["pid"])) or (q in p["window_title"].lower()):
                filtered.append(p)

        if self.sort_criterion == "ram":
            filtered.sort(key=lambda x: x["ram_mb"], reverse=True)
        elif self.sort_criterion == "cpu":
            filtered.sort(key=lambda x: x["cpu_pct"], reverse=True)
        elif self.sort_criterion == "hung":
            filtered.sort(key=lambda x: (not x["is_hung"], -x["ram_mb"]))
        else:
            filtered.sort(key=lambda x: x["name"].lower())

        # Preserve Treeview Selection
        selected_id = self.proc_tree.selection()
        selected_pid_str = None
        if selected_id:
            vals = self.proc_tree.item(selected_id[0], "values")
            if vals:
                selected_pid_str = str(vals[1])

        # Batch insert into Treeview
        self.proc_tree.delete(*self.proc_tree.get_children())
        for idx, p in enumerate(filtered[:140]):
            pid = p["pid"]
            name = p["name"]
            ram = f"{p['ram_mb']:.1f}"
            cpu = f"{p['cpu_pct']:.1f}"
            title = p["window_title"]

            if p.get("is_hung"):
                status = "⚠️ NOT RESPONDING"
                tag = "hung"
            elif p["ram_mb"] >= self.alert_mgr.ram_threshold_mb:
                status = "🔥 High RAM"
                tag = "high_ram"
            elif p["cpu_pct"] >= self.alert_mgr.cpu_threshold_pct:
                status = "⚡ High CPU"
                tag = "high_cpu"
            else:
                status = "● Normal"
                tag = "normal" if idx % 2 == 0 else "normal_alt"

            item_id = self.proc_tree.insert(
                "",
                "end",
                values=(name, pid, ram, cpu, status, title),
                tags=(tag,)
            )
            if selected_pid_str and str(pid) == selected_pid_str:
                self.proc_tree.selection_set(item_id)

        # Update Alert History Tree
        self.hist_tree.delete(*self.hist_tree.get_children())
        for a in self.alert_mgr.alert_history[:40]:
            self.hist_tree.insert(
                "",
                "end",
                values=(
                    a["time"],
                    a["severity"],
                    a["type"],
                    a.get("name", "System"),
                    a.get("pid") or "-",
                    a["message"]
                ),
                tags=(a["severity"],)
            )

        # Update Status Bar
        self.status_procs_lbl.config(
            text=f"Total: {len(processes)} processes  |  Visible: {len(filtered)}  |  Updated: {time.strftime('%H:%M:%S')}"
        )

    def switch_to_mini_view(self):
        from mini_bar import MiniBarWidget
        self.root.withdraw()
        self.mini_win = tk.Toplevel()
        self.mini_widget = MiniBarWidget(self.mini_win, on_expand_callback=self.restore_from_mini_view)

    def restore_from_mini_view(self):
        if hasattr(self, 'mini_widget') and self.mini_widget:
            self.mini_widget.is_running = False
        if hasattr(self, 'mini_win') and self.mini_win:
            try:
                self.mini_win.destroy()
            except Exception:
                pass
        self.root.deiconify()
        self.manual_refresh()

    def on_close(self):
        self.is_monitoring = False
        if hasattr(self, 'mini_win') and self.mini_win:
            try:
                self.mini_win.destroy()
            except Exception:
                pass
        self.root.destroy()


def launch():
    root = tk.Tk()
    app = ModernSystemWatchdogApp(root)
    root.mainloop()

if __name__ == "__main__":
    launch()
