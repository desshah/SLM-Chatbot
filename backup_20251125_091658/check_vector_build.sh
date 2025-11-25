#!/bin/bash

# Check vector database build progress

echo "🔍 Checking Vector Database Build Progress..."
echo ""

# Check if process is running
if ps aux | grep -q "[p]ython enhanced_vector_db.py"; then
    echo "✅ Build process is RUNNING"
    echo ""
    
    # Show last 30 lines of log
    echo "📊 Latest Progress:"
    echo "─────────────────────────────────────────────────────────"
    tail -30 vector_build.log
    
    # Extract current progress
    if grep -q "Added.*chunks\.\.\." vector_build.log; then
        echo ""
        echo "📈 Current Progress:"
        grep "Added.*chunks\.\.\." vector_build.log | tail -1
    fi
else
    echo "⚠️  Build process is NOT running"
    echo ""
    
    # Check if completed
    if grep -q "VECTOR DATABASE BUILD COMPLETE" vector_build.log 2>/dev/null; then
        echo "✅ BUILD COMPLETE!"
        echo ""
        echo "📊 Final Summary:"
        echo "─────────────────────────────────────────────────────────"
        grep -A 10 "VECTOR DATABASE BUILD COMPLETE" vector_build.log
    else
        echo "❌ Build may have failed. Check vector_build.log for errors"
        echo ""
        echo "Last 20 lines of log:"
        echo "─────────────────────────────────────────────────────────"
        tail -20 vector_build.log 2>/dev/null || echo "No log file found"
    fi
fi

echo ""
echo "─────────────────────────────────────────────────────────"
echo "To view full log: cat vector_build.log"
echo "To monitor in real-time: tail -f vector_build.log"
