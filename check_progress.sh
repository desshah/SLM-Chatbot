#!/bin/bash

# Progress Monitoring Script for Enhanced Data Collection

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         📊 DATA COLLECTION PROGRESS MONITOR                  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if process is running
if pgrep -f "enhanced_data_collection.py" > /dev/null; then
    echo "✅ Data collection is RUNNING"
    echo ""
else
    echo "❌ Data collection is NOT running"
    echo ""
    echo "To start it:"
    echo "  nohup python enhanced_data_collection.py > data_collection.log 2>&1 &"
    echo ""
    exit 1
fi

# Show latest progress
echo "📋 Latest Progress (last 10 lines):"
echo "═══════════════════════════════════════════════════════════════"
tail -10 data_collection.log | grep -E "Progress:|Crawled:|Phase" || echo "No progress yet..."
echo ""

# Show statistics
echo "📊 Current Statistics:"
echo "═══════════════════════════════════════════════════════════════"

# Count documents collected
docs=$(grep -c "✅ Crawled:" data_collection.log 2>/dev/null || echo "0")
echo "   Documents collected: $docs"

# Show last successful crawl
last_crawl=$(grep "✅ Crawled:" data_collection.log | tail -1)
if [ -n "$last_crawl" ]; then
    echo "   Last crawled: $last_crawl"
fi

echo ""

# Check if data file exists
if [ -f "data/rackspace_knowledge.json" ]; then
    size=$(ls -lh data/rackspace_knowledge.json | awk '{print $5}')
    echo "💾 Data file: $size"
    
    # Count entries in JSON
    entries=$(python -c "import json; print(len(json.load(open('data/rackspace_knowledge.json'))))" 2>/dev/null || echo "?")
    echo "   JSON entries: $entries"
else
    echo "⏳ Data file not created yet (will be created when collection completes)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "💡 Tips:"
echo "   - Collection takes ~20-40 minutes total"
echo "   - Run this script again to check progress: ./check_progress.sh"
echo "   - View full log: tail -f data_collection.log"
echo "   - Check if done: grep 'DATA COLLECTION COMPLETE' data_collection.log"
echo ""
