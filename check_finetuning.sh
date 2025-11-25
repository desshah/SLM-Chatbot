#!/bin/bash

# Monitor fine-tuning progress

echo "🔍 Checking Fine-Tuning Progress..."
echo ""

# Check if process is running
if ps aux | grep -q "[f]ine_tune_cpu.py"; then
    echo "✅ Fine-tuning process is RUNNING"
    PID=$(ps aux | grep "[f]ine_tune_cpu.py" | awk '{print $2}')
    echo "📍 Process ID: $PID"
    echo ""
    
    # Show recent progress
    if [ -f "fine_tune.log" ]; then
        echo "📊 Recent Progress:"
        echo "─────────────────────────────────────────────────────────"
        tail -50 fine_tune.log
        echo ""
        echo "─────────────────────────────────────────────────────────"
        
        # Extract training stats if available
        if grep -q "Training" fine_tune.log; then
            echo ""
            echo "📈 Training Statistics:"
            grep -E "(Epoch|Step|Loss|completed)" fine_tune.log | tail -10
        fi
    else
        echo "⏳ Log file not created yet, starting up..."
    fi
else
    echo "⚠️  Fine-tuning process is NOT running"
    echo ""
    
    # Check if completed
    if [ -f "fine_tune.log" ]; then
        if grep -q "Fine-tuning complete" fine_tune.log; then
            echo "✅ FINE-TUNING COMPLETE!"
            echo ""
            echo "📊 Final Summary:"
            echo "─────────────────────────────────────────────────────────"
            grep -A 20 "Fine-tuning complete" fine_tune.log
        else
            echo "❌ Process stopped. Check fine_tune.log for errors"
            echo ""
            echo "Last 20 lines:"
            echo "─────────────────────────────────────────────────────────"
            tail -20 fine_tune.log
        fi
    else
        echo "❌ No log file found. Fine-tuning may not have started."
    fi
fi

echo ""
echo "─────────────────────────────────────────────────────────"
echo "💡 Commands:"
echo "   View full log: cat fine_tune.log"
echo "   Monitor live: tail -f fine_tune.log"
echo "   Check process: ps aux | grep fine_tune"
