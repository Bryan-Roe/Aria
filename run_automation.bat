@echo off
REM Aria Automation Runner Batch File
REM Automatically runs core Aria systems and utilities

echo.
echo Aria Automation Runner
echo ======================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Try to use the .venv environment first
if exist ".venv\Scripts\python.exe" (
    echo Using .venv Python environment
    set PYTHON_EXEC=.venv\Scripts\python.exe
) else (
    echo Using system Python
    set PYTHON_EXEC=python
)

REM Check if Python is available
%PYTHON_EXEC% --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Run the automation script
echo Starting automation runner...
echo.

%PYTHON_EXEC% run_automation.py
if errorlevel 1 (
    echo.
    echo Error: Automation runner failed
    pause
    exit /b 1
)

echo.
echo Automation runner completed successfully!
pause
