"""
monitor_engine.py
Native Windows System & Process Monitoring Engine with Hung (Not Responding) Application Detection.
Zero third-party pip dependencies required.
"""

import ctypes
from ctypes import wintypes
import shutil
import time
import subprocess

# --- Windows API Definitions ---
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32
psapi = ctypes.windll.psapi

TH32CS_SNAPPROCESS = 0x00000002
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010
PROCESS_TERMINATE = 0x0001

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]

class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

def _filetime_to_u64(ft):
    return (ft.dwHighDateTime << 32) | ft.dwLowDateTime


class SystemMonitorEngine:
    def __init__(self):
        self.last_sys_idle = 0
        self.last_sys_kernel = 0
        self.last_sys_user = 0
        self.last_calc_time = 0
        self.last_cpu_percent = 0.0
        
        # Process CPU tracking: pid -> (last_time, last_proc_time)
        self.proc_cpu_history = {}
        self._init_system_cpu()

    def _init_system_cpu(self):
        i, k, u = FILETIME(), FILETIME(), FILETIME()
        if kernel32.GetSystemTimes(ctypes.byref(i), ctypes.byref(k), ctypes.byref(u)):
            self.last_sys_idle = _filetime_to_u64(i)
            self.last_sys_kernel = _filetime_to_u64(k)
            self.last_sys_user = _filetime_to_u64(u)
            self.last_calc_time = time.time()

    def get_system_cpu_percent(self):
        """Calculates system-wide CPU percentage using GetSystemTimes deltas."""
        i, k, u = FILETIME(), FILETIME(), FILETIME()
        now = time.time()
        if not kernel32.GetSystemTimes(ctypes.byref(i), ctypes.byref(k), ctypes.byref(u)):
            return self.last_cpu_percent

        curr_idle = _filetime_to_u64(i)
        curr_kernel = _filetime_to_u64(k)
        curr_user = _filetime_to_u64(u)

        idle_delta = curr_idle - self.last_sys_idle
        kernel_delta = curr_kernel - self.last_sys_kernel
        user_delta = curr_user - self.last_sys_user

        total_system = kernel_delta + user_delta

        if total_system > 0 and (now - self.last_calc_time) >= 0.4:
            # On Windows, kernel time includes idle time!
            busy_time = (kernel_delta - idle_delta) + user_delta
            if busy_time < 0:
                busy_time = 0
            cpu_pct = (busy_time / total_system) * 100.0
            self.last_cpu_percent = round(max(0.0, min(100.0, cpu_pct)), 1)
            self.last_sys_idle = curr_idle
            self.last_sys_kernel = curr_kernel
            self.last_sys_user = curr_user
            self.last_calc_time = now

        return self.last_cpu_percent

    def get_memory_stats(self):
        """Returns physical memory information in GB and load percentage."""
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            total_gb = stat.ullTotalPhys / (1024**3)
            avail_gb = stat.ullAvailPhys / (1024**3)
            used_gb = total_gb - avail_gb
            return {
                "percent": stat.dwMemoryLoad,
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "avail_gb": round(avail_gb, 2)
            }
        return {"percent": 0, "total_gb": 0, "used_gb": 0, "avail_gb": 0}

    def get_disk_stats(self, drive="C:\\"):
        """Returns disk space usage for the specified drive."""
        try:
            usage = shutil.disk_usage(drive)
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            percent = (usage.used / usage.total) * 100 if usage.total > 0 else 0
            return {
                "drive": drive,
                "percent": round(percent, 1),
                "total_gb": round(total_gb, 1),
                "used_gb": round(used_gb, 1),
                "free_gb": round(free_gb, 1)
            }
        except Exception:
            return {"drive": drive, "percent": 0, "total_gb": 0, "used_gb": 0, "free_gb": 0}

    def get_hung_windows(self):
        """
        Scans all top-level windows and identifies any that are marked as 'Not Responding'
        by the Windows message subsystem using IsHungAppWindow API.
        Returns a dict: pid -> list of window titles
        """
        hung_apps = {}  # pid -> [titles]

        def enum_proc(hwnd, lParam):
            try:
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        is_hung = bool(user32.IsHungAppWindow(hwnd))
                        if is_hung:
                            buf = ctypes.create_unicode_buffer(length + 1)
                            user32.GetWindowTextW(hwnd, buf, length + 1)
                            title = buf.value.strip()
                            pid = wintypes.DWORD()
                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                            if pid.value > 0:
                                if pid.value not in hung_apps:
                                    hung_apps[pid.value] = []
                                hung_apps[pid.value].append(title or "Untitled Window")
            except Exception:
                pass
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
        return hung_apps

    def get_visible_window_titles(self):
        """Maps PID to their visible window titles for easy user recognition."""
        titles = {}
        def enum_proc(hwnd, lParam):
            try:
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        pid = wintypes.DWORD()
                        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                        if pid.value > 0 and pid.value not in titles:
                            buf = ctypes.create_unicode_buffer(length + 1)
                            user32.GetWindowTextW(hwnd, buf, length + 1)
                            t = buf.value.strip()
                            if t and t not in ("Default IME", "MSCTFIME UI"):
                                titles[pid.value] = t
            except Exception:
                pass
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_proc), 0)
        return titles

    def get_processes(self):
        """
        Enumerates all running processes with PID, Process Name, RAM usage (MB),
        CPU usage estimate, and Hung status.
        """
        hung_dict = self.get_hung_windows()
        window_titles = self.get_visible_window_titles()
        now = time.time()
        new_cpu_history = {}

        hSnapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if hSnapshot == -1:
            return []

        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)

        processes = []

        if kernel32.Process32FirstW(hSnapshot, ctypes.byref(entry)):
            while True:
                pid = entry.th32ProcessID
                name = entry.szExeFile
                mem_mb = 0.0
                cpu_pct = 0.0

                if pid > 0:
                    hProcess = kernel32.OpenProcess(
                        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid
                    )
                    if not hProcess:
                        # Try limited rights if elevated
                        hProcess = kernel32.OpenProcess(
                            PROCESS_QUERY_LIMITED_INFORMATION, False, pid
                        )

                    if hProcess:
                        # Memory
                        pmc = PROCESS_MEMORY_COUNTERS_EX()
                        pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
                        if psapi.GetProcessMemoryInfo(hProcess, ctypes.byref(pmc), pmc.cb):
                            mem_mb = round(pmc.WorkingSetSize / (1024 * 1024), 1)

                        # Process CPU Time
                        ct, et, kt, ut = FILETIME(), FILETIME(), FILETIME(), FILETIME()
                        if kernel32.GetProcessTimes(
                            hProcess, ctypes.byref(ct), ctypes.byref(et),
                            ctypes.byref(kt), ctypes.byref(ut)
                        ):
                            proc_time = _filetime_to_u64(kt) + _filetime_to_u64(ut)
                            new_cpu_history[pid] = (now, proc_time)

                            if pid in self.proc_cpu_history:
                                prev_time, prev_proc_time = self.proc_cpu_history[pid]
                                dt = now - prev_time
                                if dt > 0.3:
                                    # 1 FILETIME unit = 100 nanoseconds = 1e-7 seconds
                                    cpu_used_sec = (proc_time - prev_proc_time) * 1e-7
                                    cpu_pct = round((cpu_used_sec / dt) * 100.0, 1)

                        kernel32.CloseHandle(hProcess)

                is_hung = pid in hung_dict
                w_title = window_titles.get(pid, "")
                if is_hung and pid in hung_dict:
                    w_title = "; ".join(hung_dict[pid])

                processes.append({
                    "pid": pid,
                    "name": name,
                    "ram_mb": mem_mb,
                    "cpu_pct": cpu_pct,
                    "is_hung": is_hung,
                    "window_title": w_title,
                })

                if not kernel32.Process32NextW(hSnapshot, ctypes.byref(entry)):
                    break

        kernel32.CloseHandle(hSnapshot)
        self.proc_cpu_history = new_cpu_history
        return processes

    def kill_process(self, pid):
        """
        Attempts to terminate a process by PID using native API first,
        then falls back to taskkill for forceful tree kill if needed.
        """
        if pid <= 4:
            return False, "Cannot terminate critical system process."

        # Method 1: Native Win32 TerminateProcess
        hProcess = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        if hProcess:
            res = kernel32.TerminateProcess(hProcess, 1)
            kernel32.CloseHandle(hProcess)
            if res:
                return True, f"Process {pid} terminated successfully."

        # Method 2: Forceful taskkill fallback
        try:
            cmd = ["taskkill", "/F", "/PID", str(pid), "/T"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if proc.returncode == 0:
                return True, f"Process {pid} forcefully terminated."
            else:
                return False, f"Failed to terminate: {proc.stderr.strip() or proc.stdout.strip()}"
        except Exception as e:
            return False, str(e)
