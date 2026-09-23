"""
main.py
SHOX — Main entry point for System Performance & Freeze Guardian.
"""

import sys

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
