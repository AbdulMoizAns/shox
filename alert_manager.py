"""
alert_manager.py
Manages alert evaluation, 1-minute sustained usage tracking, popup notifications, and alert history.
Repetitive sound on heavy usage is completely disabled.
Alerts for heavy usage only trigger if usage is sustained continuously for > 1 minute (60 seconds).
"""

import time
import threading

class AlertManager:
    def __init__(self):
        # Configurable Thresholds
        self.ram_threshold_mb = 500.0          # Process RAM limit (MB)
        self.cpu_threshold_pct = 30.0          # Process CPU limit (%)
        self.system_ram_threshold_pct = 90.0   # System Total RAM alert limit (%)
        self.sound_enabled = False             # Sound disabled as requested

        # Sustained Duration Requirement: 60 seconds (1 minute)
        self.sustained_duration_sec = 60.0

        # Tracker for continuous heavy usage:
        # key: (pid, alert_type) -> { 'start_time': float, 'last_seen': float, 'notified': bool, 'val': str, 'name': str }
        self.usage_tracker = {}

        # Alerts and Popups state
        self.active_alerts = []
        self.alert_history = []
        self.pending_popups = []  # List of popups to display in GUI: list of dicts

    def set_thresholds(self, ram_mb=None, cpu_pct=None, sys_ram_pct=None, sound=None, sustained_sec=None):
        if ram_mb is not None:
            self.ram_threshold_mb = float(ram_mb)
        if cpu_pct is not None:
            self.cpu_threshold_pct = float(cpu_pct)
        if sys_ram_pct is not None:
            self.system_ram_threshold_pct = float(sys_ram_pct)
        if sound is not None:
            self.sound_enabled = bool(sound)
        if sustained_sec is not None:
            self.sustained_duration_sec = float(sustained_sec)

    def evaluate(self, system_stats, processes):
        """
        Evaluates system stats and processes.
        Heavy usage is only converted into an alert/popup if it persists for >= 60 seconds.
        Returns active_alerts list.
        """
        now = time.time()
        new_active_alerts = []
        current_heavy_keys = set()

        # 1. Not Responding (Hung) Applications -> Immediate Critical Alert
        for p in processes:
            if p.get("is_hung"):
                title_desc = f" ({p['window_title']})" if p.get("window_title") else ""
                alert = {
                    "id": f"hung_{p['pid']}_{int(now)}",
                    "type": "HUNG",
                    "severity": "CRITICAL",
                    "pid": p["pid"],
                    "name": p["name"],
                    "title": f"⚠️ NOT RESPONDING: {p['name']}",
                    "message": f"{p['name']} (PID {p['pid']}){title_desc} is frozen and not responding to Windows.",
                    "value": "FROZEN",
                    "duration": "Immediate",
                    "time": time.strftime("%H:%M:%S"),
                    "can_kill": True,
                }
                new_active_alerts.append(alert)

                # Queue a popup once for new frozen apps
                hung_key = (p["pid"], "HUNG")
                if hung_key not in self.usage_tracker:
                    self.usage_tracker[hung_key] = {"start_time": now, "notified": True}
                    self.pending_popups.append(alert)
                    self.alert_history.insert(0, alert)

        # 2. Check Process High RAM Usage (Sustained >= 60 seconds)
        for p in processes:
            pid = p["pid"]
            if p["ram_mb"] >= self.ram_threshold_mb:
                key = (pid, "HIGH_RAM")
                current_heavy_keys.add(key)

                if key not in self.usage_tracker:
                    # First time seen exceeding threshold -> start the timer
                    self.usage_tracker[key] = {
                        "start_time": now,
                        "last_seen": now,
                        "notified": False,
                        "name": p["name"],
                        "val": f"{p['ram_mb']:.0f} MB"
                    }
                else:
                    self.usage_tracker[key]["last_seen"] = now
                    self.usage_tracker[key]["val"] = f"{p['ram_mb']:.0f} MB"

                duration = now - self.usage_tracker[key]["start_time"]

                # Only if usage has sustained for 1 minute (60s) or more!
                if duration >= self.sustained_duration_sec:
                    mins = int(duration // 60)
                    secs = int(duration % 60)
                    duration_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

                    alert = {
                        "id": f"ram_{pid}_{int(now)}",
                        "type": "HIGH_RAM",
                        "severity": "WARNING",
                        "pid": pid,
                        "name": p["name"],
                        "title": f"🔥 HIGH MEMORY: {p['name']}",
                        "message": f"{p['name']} (PID {pid}) has been using {p['ram_mb']:.0f} MB RAM continuously for {duration_str}.",
                        "value": f"{p['ram_mb']:.0f} MB",
                        "duration": duration_str,
                        "time": time.strftime("%H:%M:%S"),
                        "can_kill": True,
                    }
                    new_active_alerts.append(alert)

                    # Trigger popup notification only once per continuous episode
                    if not self.usage_tracker[key]["notified"]:
                        self.usage_tracker[key]["notified"] = True
                        self.pending_popups.append(alert)
                        self.alert_history.insert(0, alert)

        # 3. Check Process High CPU Usage (Sustained >= 60 seconds)
        for p in processes:
            pid = p["pid"]
            if p["cpu_pct"] >= self.cpu_threshold_pct:
                key = (pid, "HIGH_CPU")
                current_heavy_keys.add(key)

                if key not in self.usage_tracker:
                    self.usage_tracker[key] = {
                        "start_time": now,
                        "last_seen": now,
                        "notified": False,
                        "name": p["name"],
                        "val": f"{p['cpu_pct']:.0f}%"
                    }
                else:
                    self.usage_tracker[key]["last_seen"] = now
                    self.usage_tracker[key]["val"] = f"{p['cpu_pct']:.0f}%"

                duration = now - self.usage_tracker[key]["start_time"]

                # Only if usage has sustained for 1 minute (60s) or more!
                if duration >= self.sustained_duration_sec:
                    mins = int(duration // 60)
                    secs = int(duration % 60)
                    duration_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

                    alert = {
                        "id": f"cpu_{pid}_{int(now)}",
                        "type": "HIGH_CPU",
                        "severity": "WARNING",
                        "pid": pid,
                        "name": p["name"],
                        "title": f"⚡ HIGH CPU: {p['name']}",
                        "message": f"{p['name']} (PID {pid}) has been using {p['cpu_pct']:.0f}% CPU continuously for {duration_str}.",
                        "value": f"{p['cpu_pct']:.0f}%",
                        "duration": duration_str,
                        "time": time.strftime("%H:%M:%S"),
                        "can_kill": True,
                    }
                    new_active_alerts.append(alert)

                    if not self.usage_tracker[key]["notified"]:
                        self.usage_tracker[key]["notified"] = True
                        self.pending_popups.append(alert)
                        self.alert_history.insert(0, alert)

        # 4. Clean up processes that dropped below threshold or exited
        for key in list(self.usage_tracker.keys()):
            if key[1] in ("HIGH_RAM", "HIGH_CPU"):
                if key not in current_heavy_keys:
                    # Usage dropped back to normal! Reset timer for this app
                    del self.usage_tracker[key]
            elif key[1] == "HUNG":
                # Remove hung status if app closed or recovered
                hung_pids = {p["pid"] for p in processes if p.get("is_hung")}
                if key[0] not in hung_pids:
                    del self.usage_tracker[key]

        # 5. Trim History
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[:100]

        self.active_alerts = new_active_alerts
        return self.active_alerts

    def pop_pending_notifications(self):
        """Retrieves and clears any pending popup notifications."""
        popups = list(self.pending_popups)
        self.pending_popups.clear()
        return popups

    def clear_history(self):
        self.alert_history.clear()
        self.usage_tracker.clear()
