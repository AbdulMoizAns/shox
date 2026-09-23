"""
toast_popup.py
Modern non-blocking desktop toast notification for Windows.
Positions itself above the Taskbar, shows sustained high resource or frozen app warnings,
and allows 1-click 'End Task' or auto-dismisses after 12 seconds.
"""

import tkinter as tk
import ctypes
from ctypes import wintypes

def show_toast_popup(alert, kill_callback=None):
    """
    Spawns a clean, modern floating notification toast above the taskbar.
    """
    try:
        toast = tk.Toplevel()
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg="#0d1117")

        # Calculate position directly above taskbar
        rect = wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
        tw, th = 380, 118
        tx = max(10, rect.right - tw - 16)
        ty = max(10, rect.bottom - th - 52)
        toast.geometry(f"{tw}x{th}+{tx}+{ty}")

        is_hung = alert.get("type") == "HUNG"
        border_col = "#f85149" if is_hung else "#d29922"
        badge_fg = "#ff7b72" if is_hung else "#f0883e"
        title_text = "⚠️ APP NOT RESPONDING (FROZEN)" if is_hung else "🔥 SUSTAINED HIGH USAGE (> 1 MIN)"

        frame = tk.Frame(toast, bg="#161b22", highlightbackground=border_col, highlightthickness=1)
        frame.pack(fill="both", expand=True)

        header = tk.Frame(frame, bg="#161b22")
        header.pack(fill="x", padx=10, pady=(8, 2))

        tk.Label(
            header,
            text=title_text,
            font=("Segoe UI", 9, "bold"),
            fg=badge_fg,
            bg="#161b22"
        ).pack(side="left")

        close_btn = tk.Button(
            header,
            text="✕",
            font=("Segoe UI", 8, "bold"),
            fg="#8b949e",
            bg="#161b22",
            activeforeground="#ffffff",
            activebackground="#30363d",
            bd=0,
            cursor="hand2",
            command=toast.destroy
        )
        close_btn.pack(side="right")

        msg_lbl = tk.Label(
            frame,
            text=alert.get("message", ""),
            font=("Segoe UI", 9),
            fg="#c9d1d9",
            bg="#161b22",
            wraplength=355,
            justify="left"
        )
        msg_lbl.pack(anchor="w", padx=10, pady=4)

        btn_bar = tk.Frame(frame, bg="#161b22")
        btn_bar.pack(fill="x", padx=10, pady=(2, 8))

        if alert.get("can_kill") and alert.get("pid") and kill_callback:
            def on_kill():
                kill_callback(alert["pid"], alert["name"])
                if toast.winfo_exists():
                    toast.destroy()

            tk.Button(
                btn_bar,
                text=f"⛔ End Task ({alert['name']})",
                font=("Segoe UI", 8, "bold"),
                fg="white",
                bg="#da3633",
                activebackground="#b62324",
                relief="flat",
                padx=10,
                pady=2,
                cursor="hand2",
                command=on_kill
            ).pack(side="left")

        tk.Button(
            btn_bar,
            text="Dismiss",
            font=("Segoe UI", 8),
            fg="#8b949e",
            bg="#21262d",
            activeforeground="#c9d1d9",
            activebackground="#30363d",
            relief="flat",
            padx=10,
            pady=2,
            cursor="hand2",
            command=toast.destroy
        ).pack(side="right")

        # Auto-close after 14 seconds
        toast.after(14000, lambda: toast.destroy() if toast.winfo_exists() else None)
    except Exception:
        pass
