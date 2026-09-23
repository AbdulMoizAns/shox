"""
main.py
SHOX — Main entry point for System Performance & Freeze Guardian.
"""

import sys
import ctypes

# Set explicit Windows AppUserModelID so Windows Taskbar uses SHOX icon instead of Python's icon
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("shox.performance.guardian.app.v1")
except Exception:
    pass

if __name__ == "__main__":
    try:
        if "--mini" in sys.argv or "-m" in sys.argv:
            from mini_bar import launch_mini
            launch_mini()
        else:
            from app_gui import launch
            launch()
    except KeyboardInterrupt:
        sys.exit(0)
