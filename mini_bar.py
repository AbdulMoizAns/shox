"""
mini_bar.py
SHOX Mini Bar — Ultra-Sleek, High-DPI Floating Mini Bar Widget.
Positions directly above the Windows Taskbar Date & Time.
Razor-sharp fonts, Obsidian theme, live CPU/RAM metrics, and interactive Freeze Alerts.
"""

import tkinter as tk
from tkinter import messagebox
import ctypes
from ctypes import wintypes
import threading
import time
import os

# --- Enable Windows High-DPI Awareness (Crisp, zero-blur rendering) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# --- Set Explicit Windows AppUserModelID (Fixes Taskbar Icon) ---
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("shox.performance.guardian.app.v1")
except Exception:
    pass

from monitor_engine import SystemMonitorEngine
from alert_manager import AlertManager
from toast_popup import show_toast_popup
from network_engine import NetworkMonitorEngine
from optimizer_engine import SystemOptimizerEngine


def get_taskbar_anchor_position(bar_width=570, bar_height=42):
    """
    Retrieves the Windows usable screen work area (excluding taskbar)
    and computes the exact (x, y) coordinates to sit right above the clock.
    """
    rect = wintypes.RECT()
    # SPI_GETWORKAREA = 0x0030
    if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
        x = rect.right - bar_width - 12
        y = rect.bottom - bar_height - 8
        return max(0, x), max(0, y)
    return 800, 600


class MiniBarWidget:
    def __init__(self, root, on_expand_callback=None):
        self.root = root
        self.on_expand_callback = on_expand_callback

        self.root.title("SHOX Mini Bar")
        try:
            icon_ico = os.path.join(os.path.dirname(__file__), "shox.ico")
            icon_png = os.path.join(os.path.dirname(__file__), "shox_logo.png")
            if os.path.exists(icon_ico):
                self.root.iconbitmap(icon_ico)
            if os.path.exists(icon_png):
                self._app_taskbar_icon = tk.PhotoImage(file=icon_png)
                self.root.iconphoto(True, self._app_taskbar_icon)
        except Exception:
            pass

        # Window dimensions & styling
        self.bar_width = 570
        self.bar_height = 42
        self.root.overrideredirect(True)      # Frameless floating widget
        self.root.attributes("-topmost", True)  # Always on top
        self.root.configure(bg="#0a0c10")

        # Initial positioning right above Windows Taskbar Clock
        x, y = get_taskbar_anchor_position(self.bar_width, self.bar_height)
        self.root.geometry(f"{self.bar_width}x{self.bar_height}+{x}+{y}")

        # Drag tracking
        self._drag_x = 0
        self._drag_y = 0

        # Engines
        self.engine = SystemMonitorEngine()
        self.alert_mgr = AlertManager()
        self.net_engine = NetworkMonitorEngine()
        self.optimizer = SystemOptimizerEngine()
        self.is_running = True
        self.blink_state = False

        self._build_ui()
        self._bind_drag_and_actions()

        # Background worker
        self.worker_thread = threading.Thread(target=self._monitor_worker, daemon=True)
        self.worker_thread.start()

    def _build_ui(self):
        # Outer border frame with obsidian dark surface
        self.outer_border = tk.Frame(
            self.root,
            bg="#11141c",
            highlightbackground="#232735",
            highlightthickness=1,
            bd=0
        )
        self.outer_border.pack(fill="both", expand=True)

        # Drag Grip Handle
        self.grip = tk.Label(
            self.outer_border,
            text="⋮⋮",
            font=("Segoe UI", 10, "bold"),
            fg="#475569",
            bg="#11141c",
            cursor="fleur"
        )
        self.grip.pack(side="left", padx=(8, 2))

        # SHOX Brand Badge
        shox_badge = tk.Label(
            self.outer_border,
            text="SHOX",
            font=("Segoe UI", 8, "bold"),
            fg="#38bdf8",
            bg="#161f30",
            padx=4,
            pady=1,
            relief="flat"
        )
        shox_badge.pack(side="left", padx=(1, 3))

        # Battery / Power Badge
        self.battery_badge = tk.Label(
            self.outer_border,
            text="⚡ AC",
            font=("Segoe UI", 8, "bold"),
            fg="#34d399",
            bg="#11141c"
        )
        self.battery_badge.pack(side="left", padx=(1, 3))

        # CPU Metric
        cpu_box = tk.Frame(self.outer_border, bg="#11141c")
        cpu_box.pack(side="left", padx=3)

        tk.Label(
            cpu_box,
            text="⚡ CPU",
            font=("Segoe UI", 8, "bold"),
            fg="#38bdf8",
            bg="#11141c"
        ).pack(side="left")

        self.cpu_val = tk.Label(
            cpu_box,
            text="0%",
            font=("Segoe UI", 9, "bold"),
            fg="#f8fafc",
            bg="#11141c",
            width=5,
            anchor="w"
        )
        self.cpu_val.pack(side="left", padx=(2, 0))

        # Divider
        tk.Label(self.outer_border, text="|", font=("Segoe UI", 8), fg="#232735", bg="#11141c").pack(side="left", padx=2)

        # RAM Metric
        ram_box = tk.Frame(self.outer_border, bg="#11141c")
        ram_box.pack(side="left", padx=3)

        tk.Label(
            ram_box,
            text="💾 RAM",
            font=("Segoe UI", 8, "bold"),
            fg="#a78bfa",
            bg="#11141c"
        ).pack(side="left")

        self.ram_val = tk.Label(
            ram_box,
            text="0% (0G)",
            font=("Segoe UI", 9, "bold"),
            fg="#f8fafc",
            bg="#11141c",
            width=11,
            anchor="w"
        )
        self.ram_val.pack(side="left", padx=(2, 0))

        # Divider
        tk.Label(self.outer_border, text="|", font=("Segoe UI", 8), fg="#232735", bg="#11141c").pack(side="left", padx=2)

        # Net Metric
        net_box = tk.Frame(self.outer_border, bg="#11141c")
        net_box.pack(side="left", padx=3)

        tk.Label(
            net_box,
            text="🌐",
            font=("Segoe UI", 8),
            fg="#38bdf8",
            bg="#11141c"
        ).pack(side="left")

        self.net_val = tk.Label(
            net_box,
            text="↓0K ↑0K",
            font=("Segoe UI", 8, "bold"),
            fg="#f8fafc",
            bg="#11141c",
            width=13,
            anchor="w"
        )
        self.net_val.pack(side="left", padx=(2, 0))

        # Divider
        tk.Label(self.outer_border, text="|", font=("Segoe UI", 8), fg="#232735", bg="#11141c").pack(side="left", padx=2)

        # Status / Freeze Pill Badge
        self.status_badge = tk.Label(
            self.outer_border,
            text="● OK",
            font=("Segoe UI", 8, "bold"),
            fg="#34d399",
            bg="#13241c",
            padx=7,
            pady=2,
            relief="flat",
            cursor="hand2"
        )
        self.status_badge.pack(side="left", padx=4)
        self.status_badge.bind("<Button-1>", self.on_status_clicked)

        # Action Buttons (Clean RAM, Expand & Close)
        btn_box = tk.Frame(self.outer_border, bg="#11141c")
        btn_box.pack(side="right", padx=(2, 8))

        # Quick Clean RAM Micro-Button
        self.quick_clean_btn = tk.Button(
            btn_box,
            text="🧹",
            command=self.quick_clean_ram,
            font=("Segoe UI", 9),
            fg="#fbbf24",
            bg="#11141c",
            activeforeground="#fef08a",
            activebackground="#1e2330",
            bd=0,
            padx=4,
            cursor="hand2",
            relief="flat"
        )
        self.quick_clean_btn.pack(side="left", padx=1)

        # Expand to full Dashboard
        self.expand_btn = tk.Button(
            btn_box,
            text="⛶",
            command=self.expand_to_full,
            font=("Segoe UI", 9, "bold"),
            fg="#64748b",
            bg="#11141c",
            activeforeground="#38bdf8",
            activebackground="#1e2330",
            bd=0,
            padx=5,
            cursor="hand2",
            relief="flat"
        )
        self.expand_btn.pack(side="left", padx=1)

        # Close
        close_btn = tk.Button(
            btn_box,
            text="✕",
            command=self.close_app,
            font=("Segoe UI", 9, "bold"),
            fg="#64748b",
            bg="#11141c",
            activeforeground="#f43f5e",
            activebackground="#1e2330",
            bd=0,
            padx=5,
            cursor="hand2",
            relief="flat"
        )
        close_btn.pack(side="left", padx=1)

    def _bind_drag_and_actions(self):
        draggable_widgets = [self.outer_border, self.grip]
        for w in draggable_widgets:
            w.bind("<Button-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)
            w.bind("<Double-Button-1>", lambda e: self.expand_to_full())

    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event):
        deltax = event.x - self._drag_x
        deltay = event.y - self._drag_y
        new_x = self.root.winfo_x() + deltax
        new_y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{new_x}+{new_y}")

    def on_status_clicked(self, event=None):
        for alert in self.alert_mgr.active_alerts:
            if alert.get("type") == "HUNG" and alert.get("pid"):
                confirm = messagebox.askyesno(
                    "Kill Frozen App",
                    f"Application '{alert['name']}' (PID {alert['pid']}) is NOT RESPONDING.\nDo you want to terminate it now?"
                )
                if confirm:
                    success, msg = self.engine.kill_process(alert["pid"])
                    if success:
                        messagebox.showinfo("Closed", msg)
                return
        self.expand_to_full()

    def quick_clean_ram(self):
        def _work():
            freed_mb, count = self.optimizer.clean_system_ram()
            show_toast_popup({
                "name": "SHOX Mini",
                "type": "RAM_CLEANED",
                "message": f"Purged {freed_mb:.1f} MB RAM across {count} processes.",
                "severity": "NORMAL"
            })
        threading.Thread(target=_work, daemon=True).start()

    def expand_to_full(self):
        if self.on_expand_callback:
            self.on_expand_callback()
        else:
            from app_gui import ModernSystemWatchdogApp
            self.root.withdraw()
            top = tk.Toplevel()
            app = ModernSystemWatchdogApp(top)

            def on_top_close():
                top.destroy()
                self.root.deiconify()

            top.protocol("WM_DELETE_WINDOW", on_top_close)

    def close_app(self):
        self.is_running = False
        self.root.destroy()

    def _monitor_worker(self):
        while self.is_running:
            try:
                cpu_pct = self.engine.get_system_cpu_percent()
                mem = self.engine.get_memory_stats()
                procs = self.engine.get_processes()
                down_kb, up_kb, down_str, up_str = self.net_engine.get_bandwidth_speeds()
                power = self.optimizer.get_power_status()

                d_compact = f"{down_kb:.0f}K" if down_kb < 1000 else f"{down_kb/1024.0:.1f}M"
                u_compact = f"{up_kb:.0f}K" if up_kb < 1000 else f"{up_kb/1024.0:.1f}M"
                net_text = f"↓{d_compact} ↑{u_compact}"

                sys_summary = {
                    "cpu_percent": cpu_pct,
                    "ram_percent": mem["percent"],
                    "disk_percent": 0
                }
                alerts = self.alert_mgr.evaluate(sys_summary, procs)

                self.root.after(0, self._update_ui, cpu_pct, mem, alerts, net_text, power)
            except Exception:
                pass
            time.sleep(1.0)

    def _update_ui(self, cpu_pct, mem, alerts, net_text="↓0K ↑0K", power=None):
        self.cpu_val.config(text=f"{cpu_pct:.0f}%")
        self.ram_val.config(text=f"{mem['percent']}% ({mem['used_gb']}G)")
        if hasattr(self, 'net_val') and self.net_val:
            self.net_val.config(text=net_text)

        if power and hasattr(self, 'battery_badge') and self.battery_badge:
            b_icon = power.get("icon", "⚡")
            if power.get("is_ac"):
                self.battery_badge.config(text=f"{b_icon} AC", fg="#34d399")
            else:
                pct = power.get("percent", 0)
                self.battery_badge.config(text=f"{b_icon} {pct}%", fg="#fbbf24" if pct < 30 else "#38bdf8")

        hung_alerts = [a for a in alerts if a["type"] == "HUNG"]
        heavy_alerts = [a for a in alerts if a["type"] in ("HIGH_RAM", "HIGH_CPU")]

        if hung_alerts:
            self.blink_state = not self.blink_state
            app_name = hung_alerts[0]["name"]
            if len(app_name) > 11:
                app_name = app_name[:9] + ".."

            if self.blink_state:
                self.status_badge.config(
                    text=f"⚠️ FROZEN: {app_name}",
                    fg="#ffffff",
                    bg="#e11d48"
                )
                self.outer_border.config(highlightbackground="#f43f5e")
            else:
                self.status_badge.config(
                    text=f"⚠️ FROZEN: {app_name}",
                    fg="#fda4af",
                    bg="#381318"
                )
                self.outer_border.config(highlightbackground="#be123c")
        elif heavy_alerts:
            self.status_badge.config(
                text=f"● {len(heavy_alerts)} HEAVY",
                fg="#fcd34d",
                bg="#2a1f11"
            )
            self.outer_border.config(highlightbackground="#fbbf24")
        else:
            self.status_badge.config(
                text="● OK",
                fg="#34d399",
                bg="#13241c"
            )
            self.outer_border.config(highlightbackground="#232735")

        # Check and display Toast Popups
        pending_popups = self.alert_mgr.pop_pending_notifications()
        for alert_item in pending_popups:
            show_toast_popup(alert_item, kill_callback=self._kill_process_by_pid)

    def _kill_process_by_pid(self, pid, name):
        confirm = messagebox.askyesno(
            "End Task",
            f"Are you sure you want to terminate '{name}' (PID {pid})?"
        )
        if confirm:
            success, msg = self.engine.kill_process(pid)
            if success:
                messagebox.showinfo("Terminated", f"'{name}' (PID {pid}) was terminated.")
            else:
                messagebox.showerror("Error", msg)


def launch_mini():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("shox.performance.guardian.app.v1")
    except Exception:
        pass
    root = tk.Tk()
    root.title("SHOX Mini Bar")
    try:
        icon_ico = os.path.join(os.path.dirname(__file__), "shox.ico")
        icon_png = os.path.join(os.path.dirname(__file__), "shox_logo.png")
        if os.path.exists(icon_ico):
            root.iconbitmap(icon_ico)
        if os.path.exists(icon_png):
            photo = tk.PhotoImage(file=icon_png)
            root.iconphoto(True, photo)
    except Exception:
        pass
    widget = MiniBarWidget(root)
    root.mainloop()

if __name__ == "__main__":
    launch_mini()
