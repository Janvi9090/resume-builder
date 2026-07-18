@echo off
setlocal enabledelayedexpansion

echo ====================================
echo  Smart Resume Builder - Setup
echo ====================================

REM --- 1. Check for Python ---
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python was not found on this system.
    echo Install it from https://www.python.org/downloads/ and re-run this script.
    echo IMPORTANT: during install, check "Add Python to PATH".
    pause
    exit /b 1
)
echo [1/4] Python found.

REM --- 2. Create a virtual environment if one doesn't exist yet ---
if not exist venv (
    echo [2/4] Creating virtual environment...
    python -m venv venv
) else (
    echo [2/4] Virtual environment already exists, skipping.
)

call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install --upgrade pip -q
pip install -r requirements.txt -q

REM --- 3. Check for pdflatex ---
where pdflatex >nul 2>nul
if %errorlevel% neq 0 (
    echo [3/4] LaTeX was not found on this system.
    echo.
    echo Please install MiKTeX from https://miktex.org/download
    echo During MiKTeX setup, choose "Install missing packages on the fly: Yes"
    echo so it can fetch what it needs automatically the first time you run this.
    echo.
    echo After installing MiKTeX, re-run this script.
    pause
    exit /b 1
) else (
    echo [3/4] LaTeX already installed, skipping.
)

REM --- 4. Launch the desktop app ---
echo [4/4] Starting Smart Resume Builder...
python gui.py

pause