@echo off
echo ========================================================================
echo Weather Data Management System - Automated Setup
echo Indian Meteorological Department (IMD), Chennai
echo ========================================================================
echo.

echo [1/7] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not added to PATH.
    echo.
    echo PREREQUISITE REQUIRED ON COMPANY COMPUTER:
    echo 1. Download Python 3.9 or higher from https://www.python.org/downloads/
    echo 2. During setup, you MUST check the box: "Add Python to PATH"
    echo 3. Restart this terminal and run setup.bat again.
    echo.
    pause
    exit /b 1
)
python --version
echo OK: Python is installed and configured in PATH.
echo.

echo [2/7] Creating virtual environment...
if exist venv (
    echo OK: Virtual environment already exists.
) else (
    python -m venv venv
    echo OK: Virtual environment created successfully.
)
echo.

echo [3/7] Activating virtual environment...
call venv\Scripts\activate.bat
echo OK: Virtual environment activated.
echo.

echo [4/7] Upgrading pip, setuptools, and wheel (build tools)...
python -m pip install --upgrade pip setuptools wheel --quiet
echo OK: Build tools upgraded.
echo.

echo [5/7] Installing required application libraries...
echo This will install Flask, SQLAlchemy, Pandas, OpenPyXL, ReportLab, python-docx, etc.
echo Please wait (2-5 minutes depending on internet speed)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies. Check internet connection.
    pause
    exit /b 1
)
echo OK: All required libraries installed successfully.
echo.

echo [6/7] Verifying application data directories...
if not exist logs mkdir logs
if not exist exports mkdir exports
if not exist daily_archive mkdir daily_archive
if not exist excel_archive mkdir excel_archive
echo OK: Required directories verified.
echo.

echo [7/7] Setup Complete!
echo ========================================================================
echo SYSTEM READY FOR DEPLOYMENT!
echo.
echo TO LAUNCH THE APPLICATION:
echo Double-click: Start_IMD_System.bat
echo (Or run 'python run.py' from terminal)
echo.
echo Application URL: http://localhost:5000 or http://127.0.0.1:5000
echo Default Admin Login: admin / admin123
echo ========================================================================
pause
