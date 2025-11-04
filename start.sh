#!/bin/bash

echo "===================================="
echo "PDF Dark Mode Converter - Vector Edition"
echo "===================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9+ from https://www.python.org/downloads/"
    exit 1
fi

echo "[1/3] Installing Python dependencies..."
cd backend
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "[2/3] Starting backend server..."
echo "Server will start on http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "[3/3] Open index.html in your browser to use the converter"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 main.py
