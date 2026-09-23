@echo off
title SHOX — System Performance Guardian
cd /d "%~dp0"

echo ================================================================
echo           SHOX — SYSTEM PERFORMANCE & FREEZE GUARDIAN
echo ================================================================
echo.
echo [INFO] Starting SHOX Application...

:: Find and launch with the first available Python executable
where pythonw >nul 2>&1 && (
    start "" pythonw main.py
    exit /b
)
where pyw >nul 2>&1 && (
    start "" pyw main.py
    exit /b
)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" main.py
    exit /b
)

:: Console fallback
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application could not be started.
    echo Please make sure Python is installed and added to your system PATH.
    pause
)
