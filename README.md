<p align="center">
  <img src="assets/shox_logo.png" width="180" height="180" alt="SHOX Logo" style="border-radius: 24px;"/>
</p>

<h1 align="center">⚡ SHOX — Windows System Performance & Freeze Guardian</h1>

<p align="center">
  <b>Ultra-fast, zero-dependency Windows system resource monitor, RAM optimizer, hang watchdog, per-app firewall & floating taskbar mini-bar.</b>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python 3.10+"/></a>
  <a href="https://microsoft.com/windows"><img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white" alt="Windows 10/11"/></a>
  <img src="https://img.shields.io/badge/Dependencies-Zero%20External-success" alt="Zero Dependencies"/>
  <img src="https://img.shields.io/badge/DPI%20Aware-100%25%20Crisp%20(Zero%20Blur)-blueviolet" alt="High DPI"/>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License: MIT"/></a>
</p>

---

## 📖 Overview (Ta'aruf)

**SHOX** is an ultra-modern, high-performance Windows desktop performance guardian built specifically for developers, gamers, and power users. It combines real-time hardware telemetry, freeze/hang detection via native Win32 APIs, instant memory purging, process suspension, per-app internet blocking, and auto-start management into a sleek obsidian dark interface.

> **Urdu:** SHOX ek ultra-modern aur powerful Windows utility hay jo real-time CPU, RAM, Network aur Battery health monitor karti hay. Is mein 1-Click Clean RAM, process pause/resume, Game Mode, Windows Firewall per-app internet block, startup apps manager, aur floating Taskbar Mini Bar shamil hain—aur ye **100% zero external dependencies** par chalti hay!

---

## 🌟 Key Highlights & Mega-Features

### 1. 🧹 1-Click Clean RAM & Working Set Purge
- Flushes inactive memory and trims working sets across all accessible processes using native `psapi.EmptyWorkingSet`.
- Instantly frees hundreds of megabytes to gigabytes of locked memory without closing any apps.
- **Auto-Purge Mode:** Optionally auto-cleans RAM whenever system memory usage crosses **85%**.

### 2. ⏸️ Process Suspend (Pause) & ▶️ Resume
- Freeze unwanted background games or heavy software without terminating them using native `ntdll.NtSuspendProcess` and `ntdll.NtResumeProcess`.
- Resumes instantly when you need them, saving battery and CPU cycles.

### 3. 🚀 Game / Focus Mode (Priority Booster)
- Elevates active games or critical applications to `HIGH` CPU scheduling priority via `kernel32.SetPriorityClass`.
- Maximizes frame rates and minimizes input latency during gaming or intensive compilation tasks.

### 4. 📈 60-Second Real-Time Wave Graphs (Canvas Sparklines)
- Ultra-smooth, anti-aliased live performance wave charts rendered natively using Tkinter vector canvas.
- Real-time visualization for **CPU Load Wave**, **RAM Committed Wave**, and **Network Bandwidth Wave** without heavy plotting dependencies.

### 5. 🌐 Real-Time Network Sockets & Data Usage Tracker
- **Active Socket Tracking:** Leverages Windows IP Helper API (`GetExtendedTcpTable`, `GetExtendedUdpTable`) to list every app using the internet.
- **Inspect Remote Connections:** View Process Name, PID, Protocol (TCP/UDP), Local Port, Remote IP, and Service type (e.g. `HTTPS`, `DNS`, `SSH`).
- **Live Bandwidth Speeds:** Real-time download (`↓ KB/s`) and upload (`↑ KB/s`) calculation via `GetIfTable2`.
- **Cumulative Session Data Usage:** Tracks total MB/GB downloaded and uploaded since SHOX started.

### 6. 🛡️ 1-Click App Internet Block (Windows Firewall)
- Instantly block any suspicious or bandwidth-hogging application from accessing the internet via native Windows Defender Firewall rules (`netsh advfirewall`).
- Easily remove firewall block rules with 1 click.

### 7. 🔋 Laptop Battery & AC Power Health Monitor
- Continuously inspects AC power supply, battery health percentage, and charging state via `kernel32.GetSystemPowerStatus`.
- Integrated directly into both the main dashboard and the floating mini bar.

### 8. 🚀 Windows Startup Applications Manager
- Enumerate and inspect all apps configured to auto-start with Windows across `HKCU` and `HKLM` Run registries.
- **Start SHOX with Windows:** Built-in 1-click toggle to auto-start SHOX in lightweight Mini Bar mode on boot.

### 9. 🧊 Instant "Not Responding" (Freeze) Watchdog
- Communicates directly with the Windows window manager via native `user32.IsHungAppWindow`.
- If an app freezes, SHOX immediately alerts you with an obsidian toast notification and 1-click force kill.

### 10. 📌 Floating Mini Bar (Docked Above Taskbar Clock)
- Compact, frameless floating widget designed to sit directly above the Windows system clock.
- Displays live CPU, RAM, Network traffic, battery status, and a quick **🧹 Clean RAM** button.
- Fully draggable with grip handle (`⋮⋮`) and 1-click expand (`⛶`) to the full dashboard.

### 11. 🎨 Obsidian Dark Modern UI (Zero Blur)
- **High-DPI Per-Monitor Aware:** Configured via `shcore.SetProcessDpiAwareness(2)` for razor-sharp rendering on 1080p, 2K, 4K, and high-DPI laptop displays.
- Custom vector canvas micro-bars, obsidian card styling, alternating table rows, and color-coded status badges.

---

## 📁 Repository Structure

```
shox/
├── assets/
│   ├── shox_logo.png        # Official high-resolution logo (PNG)
│   ├── shox_logo.jpg        # High-definition source image
│   └── shox.ico             # Windows multi-resolution icon (16x16 to 256x256)
├── app_gui.py               # Main Obsidian Dark dashboard (Tkinter UI)
├── mini_bar.py              # Floating mini bar widget (taskbar dock)
├── optimizer_engine.py      # Win32 optimization, RAM purge, suspend, firewall, battery
├── network_engine.py        # Native Win32 network & bandwidth engine
├── monitor_engine.py        # Native Win32 ctypes engine (CPU, RAM, Hung detector)
├── alert_manager.py         # Smart sustained 1-minute alert watchdog & history
├── toast_popup.py           # Smooth non-blocking desktop toast notifications
├── demo_freeze_app.py       # Test utility to safely simulate hung applications
├── main.py                  # CLI and GUI entry point (supports --mini flag)
├── run.bat                  # Double-click launcher for Full Dashboard
├── run_mini.bat             # Double-click launcher for Mini Bar View
├── test_system_full.py      # Automated integration test suite (14 tests)
├── .gitignore               # Clean git exclusions
├── LICENSE                  # MIT License
└── README.md                # Project documentation
```

---

## 🚀 Quick Start (Kaise Chalayein)

### Prerequisites
- Windows 10 or Windows 11 (64-bit or 32-bit)
- Python 3.10+ (Python 3.12 recommended)
- **No `pip install` required! Zero external dependencies.**

### Launching the Application

#### Option 1: Floating Mini Bar (Recommended for daily use)
Double-click [`run_mini.bat`](run_mini.bat) or run:
```powershell
python main.py --mini
```
*A sleek, unobtrusive bar will dock directly above your Windows taskbar clock.*

#### Option 2: Full Detailed Dashboard
Double-click [`run.bat`](run.bat) or run:
```powershell
python main.py
```
*Opens the comprehensive performance monitoring suite with live wave graphs, process suspension, and RAM optimization.*

---

## 🧪 Testing Freeze Detection

Want to verify how SHOX catches frozen programs?

1. Open a terminal and run the test simulator:
   ```powershell
   python demo_freeze_app.py
   ```
2. Click **"🧊 FREEZE THIS APP (15 Seconds)"** on the test window.
3. Instantly, SHOX will:
   - Blink the status badge to **`⚠️ 1 FROZEN!`**
   - Pop up a desktop toast notification with an **"End Task"** button.
   - Highlight the process in red in the Active Processes table.

---

## ⚙️ Architecture & Technical Details

```
   ┌────────────────────────────────────────────────────────────────────────┐
   │                        Native Windows Subsystem                        │
   │  kernel32.dll • user32.dll • psapi.dll • ntdll.dll • iphlpapi • winreg │
   └───────────────┬──────────────────────────┬─────────────────────────────┘
                   │                          │
                   ▼                          ▼
        ┌──────────────────────┐   ┌──────────────────────┐
        │ monitor_engine.py    │   │ optimizer_engine.py  │
        │ - GlobalMemoryStatus │   │ - EmptyWorkingSet    │
        │ - GetSystemTimes     │   │ - NtSuspendProcess   │
        │ - IsHungAppWindow    │   │ - SetPriorityClass   │
        └──────────┬───────────┘   │ - Windows Firewall   │
                   │               │ - Power Status (AC)  │
                   ▼               └──────────┬───────────┘
        ┌──────────────────────┐              │
        │ network_engine.py    │              │
        │ - GetIfTable2        │              │
        │ - ExtendedTcpTable   │              │
        │ - Session Usage      │              │
        └──────────┬───────────┘              │
                   │                          │
                   ▼                          ▼
        ┌─────────────────────────────────────────────────┐
        │              app_gui.py / mini_bar.py           │
        │   Sparklines • Micro-Bars • Obsidian Theme      │
        └─────────────────────────────────────────────────┘
```

---

## 🧪 Running Automated Tests

To run the full suite of 14 integration tests:
```powershell
python -u test_system_full.py
```

Expected result:
```
==================================================
 [INFO] RUNNING SYSTEM MONITOR INTEGRATION TESTS
==================================================
[TEST 1] Memory Stats: PASSED
[TEST 2] Disk Stats: PASSED
[TEST 3] CPU Usage: PASSED
[TEST 4] Process Enumeration: PASSED
[TEST 5a] Sustained Check: PASSED
[TEST 5b] Sustained Alert Trigger: PASSED
[TEST 6] Not Responding Detector: PASSED
[TEST 7] GUI Modules: PASSED
[TEST 8] Network Connections: PASSED
[TEST 9] Network Bandwidth: PASSED
[TEST 10] Session Data Tracker: PASSED
[TEST 11] Clean RAM Purge: PASSED
[TEST 12] Power Status: PASSED
[TEST 13] Startup Manager: PASSED
[TEST 14] Process Priority Control: PASSED
==================================================
 [SUCCESS] ALL 14 INTEGRATION TESTS PASSED SUCCESSFULLY!
==================================================
```

---

## 👤 Author & Credits

- **Developer:** [Abdul Moiz Ansari](https://github.com/AbdulMoizAns)
- **Project:** SHOX System Performance & Freeze Guardian

---

## 📄 License

This project is licensed under the [MIT License](LICENSE). Feel free to use, modify, and distribute for personal or commercial projects.
