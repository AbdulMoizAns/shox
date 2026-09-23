"""
demo_freeze_app.py
A safe simulation app to demonstrate 'Not Responding' (Hung) detection.
Run this script and click the 'FREEZE THIS APP' button.
The window will stop responding to Windows messages for 15 seconds,
allowing you to test the Watchdog application's alert!
"""

import tkinter as tk
import time

def trigger_freeze():
    status_label.config(text="⚠️ APP IS NOW FROZEN! Window is unresponsive for 15s...", fg="#ff5555")
    root.update()
    # Blocking sleep without pumping Windows messages causes Windows to mark it as (Not Responding)
    time.sleep(15)
    status_label.config(text="✅ Recovered from freeze. App is responsive again.", fg="#55ff55")

root = tk.Tk()
root.title("Demo App for Testing Freeze Detection")
root.geometry("450x220")
root.configure(bg="#22272e")

title_lbl = tk.Label(
    root,
    text="Test Frozen / Not Responding App",
    font=("Segoe UI", 13, "bold"),
    fg="#adbac7",
    bg="#22272e"
)
title_lbl.pack(pady=15)

info_lbl = tk.Label(
    root,
    text="Click below to simulate a hanging/unresponsive program.\nThe System Watchdog app will immediately detect and alert you!",
    font=("Segoe UI", 9),
    fg="#768390",
    bg="#22272e",
    justify="center"
)
info_lbl.pack(pady=5)

btn = tk.Button(
    root,
    text="🧊 FREEZE THIS APP (15 Seconds)",
    command=trigger_freeze,
    bg="#e5534b",
    fg="white",
    font=("Segoe UI", 10, "bold"),
    padx=10,
    pady=8,
    relief="flat",
    cursor="hand2"
)
btn.pack(pady=15)

status_label = tk.Label(
    root,
    text="Status: Responsive (Running smoothly)",
    font=("Segoe UI", 9),
    fg="#57ab5a",
    bg="#22272e"
)
status_label.pack()

if __name__ == "__main__":
    root.mainloop()
