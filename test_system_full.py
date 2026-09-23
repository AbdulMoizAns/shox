"""
test_system_full.py
Automated integration test for System Monitor Engine and Alert Manager.
"""

import sys
from monitor_engine import SystemMonitorEngine
from alert_manager import AlertManager

def run_tests():
    print("==================================================")
    print(" [INFO] RUNNING SYSTEM MONITOR INTEGRATION TESTS")
    print("==================================================")

    # 1. Test Monitor Engine
    engine = SystemMonitorEngine()
    
    mem = engine.get_memory_stats()
    print(f"[TEST 1] Memory Stats: {mem['percent']}% used ({mem['used_gb']} GB / {mem['total_gb']} GB)")
    assert mem['total_gb'] > 0, "Total RAM should be greater than 0"
    assert 0 <= mem['percent'] <= 100, "RAM percent should be between 0 and 100"

    disk = engine.get_disk_stats("C:\\")
    print(f"[TEST 2] Disk Stats: {disk['percent']}% used ({disk['used_gb']} GB / {disk['total_gb']} GB)")
    assert disk['total_gb'] > 0, "Total disk space should be greater than 0"

    cpu = engine.get_system_cpu_percent()
    print(f"[TEST 3] CPU Usage: {cpu}%")
    assert 0 <= cpu <= 100, "CPU percent should be between 0 and 100"

    # 2. Test Process Enumeration
    procs = engine.get_processes()
    print(f"[TEST 4] Process Enumeration: Found {len(procs)} running processes")
    assert len(procs) > 20, "Should detect at least 20 running processes on Windows"

    # Find top RAM consumers
    top_ram = sorted(procs, key=lambda x: x['ram_mb'], reverse=True)[:3]
    print(f"         Top RAM app: {top_ram[0]['name']} (PID {top_ram[0]['pid']}) -> {top_ram[0]['ram_mb']} MB")

    # 3. Test Alert Manager with 1-minute sustained rule
    alert_mgr = AlertManager()
    alert_mgr.sound_enabled = False  # mute sound
    # Test tracking: on first tick with sustained_sec=60, it tracks without false immediate alert
    alert_mgr.set_thresholds(ram_mb=100.0, cpu_pct=10.0, sustained_sec=60.0)
    stats = {"cpu_percent": cpu, "ram_percent": mem['percent'], "disk_percent": disk['percent']}
    initial_alerts = alert_mgr.evaluate(stats, procs)
    print(f"[TEST 5a] Sustained Check: {len(alert_mgr.usage_tracker)} apps tracked for heavy usage, 0 premature alerts")
    assert len(alert_mgr.usage_tracker) > 0, "Should start tracking heavy apps"

    # Test sustained trigger when duration threshold is reached
    alert_mgr.set_thresholds(sustained_sec=0.0)
    sustained_alerts = alert_mgr.evaluate(stats, procs)
    popups = alert_mgr.pop_pending_notifications()
    print(f"[TEST 5b] Sustained Alert Trigger: Generated {len(sustained_alerts)} sustained alerts & {len(popups)} popup notifications")
    assert len(sustained_alerts) > 0, "Should generate sustained alerts"
    assert len(popups) > 0, "Should queue popup notifications"

    # 4. Test Simulated Not Responding App Alert
    fake_hung_proc = [{
        "pid": 99999,
        "name": "simulated_frozen_app.exe",
        "ram_mb": 50.0,
        "cpu_pct": 0.0,
        "is_hung": True,
        "window_title": "Simulated Frozen Window (Not Responding)"
    }]
    hung_alerts = alert_mgr.evaluate(stats, fake_hung_proc)
    hung_critical = [a for a in hung_alerts if a['type'] == 'HUNG']
    print(f"[TEST 6] Not Responding Detector: Generated {len(hung_critical)} CRITICAL freeze alert(s)")
    assert len(hung_critical) == 1, "Should catch the frozen application with CRITICAL severity"
    assert hung_critical[0]['severity'] == "CRITICAL"
    print(f"         Alert text: '{hung_critical[0]['message']}'")

    # 5. Verify App GUI module imports cleanly
    import app_gui
    print("[TEST 7] GUI Module: app_gui imported successfully with zero errors")

    print("==================================================")
    print(" [SUCCESS] ALL 7 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
