@echo off
REM TextGuard - Quick Start Script for Windows

echo.
echo ============================================
echo TextGuard - Plagiarism Checker & Remover
echo Version 2.0.0
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Create virtual environment if not exists
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

echo.
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo 📥 Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ⚠️  Some packages may have failed to install
    echo Continue anyway? (Y/n)
    set /p continue=
    if /i not "%continue%"=="y" (
        pause
        exit /b 1
    )
)

echo.
echo ✅ Setup complete!
echo.
echo 🚀 Starting TextGuard server...
echo.
echo Server will run at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python plagiarism_server.py

pause
