@echo off
title SHOX Mini Bar
cd /d "%~dp0"

echo ================================================================
echo                 SHOX MINI FLOATING BAR
echo ================================================================
echo.
echo [INFO] Launching SHOX Mini Bar above Taskbar Clock...

:: Try launching with pythonw (quiet background mode, no black console)
start "" pythonw mini_bar.py 2>nul
if %ERRORLEVEL% EQU 0 exit /b

:: Try Python Launcher pyw
start "" pyw mini_bar.py 2>nul
if %ERRORLEVEL% EQU 0 exit /b

:: Try direct Python 3.12 installation path
if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" mini_bar.py
    exit /b
)

:: Console fallback
python mini_bar.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Could not start Mini Bar.
    pause
)

exit /b
