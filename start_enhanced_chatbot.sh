#!/bin/bash

# Quick Start Script for Enhanced Rackspace Chatbot
# This script activates the virtual environment and starts the Streamlit app

echo "🤖 Starting Enhanced Rackspace Knowledge Chatbot..."
echo "=================================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create one with: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📥 Installing required packages..."
    pip install -r requirements.txt
fi

echo ""
echo "✅ Starting Streamlit app..."
echo "=================================================="
echo ""
echo "📝 The chatbot will open in your browser at:"
echo "   http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start Streamlit
streamlit run streamlit_app.py
