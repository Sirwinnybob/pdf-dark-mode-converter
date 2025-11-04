@echo off
echo ====================================
echo PDF Dark Mode Converter - Vector Edition
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Installing Python dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Starting backend server...
echo Server will start on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo [3/3] Open index.html in your browser to use the converter
echo.
echo Press Ctrl+C to stop the server
echo.

python main.py
