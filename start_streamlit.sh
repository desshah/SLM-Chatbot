#!/bin/bash

# Streamlit launcher for Rackspace Chatbot
# Simpler and faster than Gradio!

echo "=================================="
echo "🚀 Rackspace Chatbot - Streamlit"
echo "=================================="
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Run ./setup.sh first"
    exit 1
fi

# Check if streamlit is installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing Streamlit..."
    pip install streamlit>=1.28.0
fi

# Launch Streamlit app
echo ""
echo "=================================="
echo "✨ Starting Streamlit app..."
echo "=================================="
echo ""
echo "📱 The app will open in your browser at:"
echo "   http://localhost:8501"
echo ""
echo "💡 Tips:"
echo "   - First launch takes 1-2 minutes to load model"
echo "   - The model is cached after first load"
echo "   - Press Ctrl+C to stop the server"
echo ""
echo "=================================="
echo ""

# Run streamlit with custom config
streamlit run streamlit_app.py \
    --server.port=8501 \
    --server.address=localhost \
    --browser.gatherUsageStats=false \
    --theme.primaryColor="#667eea" \
    --theme.backgroundColor="#ffffff" \
    --theme.secondaryBackgroundColor="#f0f2f6" \
    --theme.textColor="#262730"
