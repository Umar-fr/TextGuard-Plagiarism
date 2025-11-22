#!/bin/bash

# TextGuard - Quick Start Script for Linux/Mac

echo ""
echo "============================================"
echo "TextGuard - Plagiarism Checker & Remover"
echo "Version 2.0.0"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo ""
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "⚠️  Some packages may have failed to install"
    read -p "Continue anyway? (Y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting TextGuard server..."
echo ""
echo "Server will run at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python plagiarism_server.py
