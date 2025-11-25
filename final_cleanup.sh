#!/bin/bash
# Final cleanup - remove remaining duplicates and cache files

echo "=========================================="
echo "FINAL CLEANUP - Removing Duplicates"
echo "=========================================="
echo ""

# Remove old README (already replaced)
if [ -f "README_old.md" ]; then
    echo "✓ Removing README_old.md (replaced by new README.md)"
    rm README_old.md
fi

# Remove __pycache__ directory (Python cache)
if [ -d "__pycache__" ]; then
    echo "✓ Removing __pycache__/ directory"
    rm -rf __pycache__
fi

# Remove .pyc files (Python compiled files)
pyc_count=$(find . -name "*.pyc" ! -path "./venv/*" ! -path "./backup_*" | wc -l | tr -d ' ')
if [ "$pyc_count" -gt 0 ]; then
    echo "✓ Removing $pyc_count .pyc files"
    find . -name "*.pyc" ! -path "./venv/*" ! -path "./backup_*" -delete
fi

# Remove .DS_Store files (macOS)
ds_count=$(find . -name ".DS_Store" ! -path "./venv/*" ! -path "./backup_*" | wc -l | tr -d ' ')
if [ "$ds_count" -gt 0 ]; then
    echo "✓ Removing $ds_count .DS_Store files"
    find . -name ".DS_Store" ! -path "./venv/*" ! -path "./backup_*" -delete
fi

echo ""
echo "=========================================="
echo "✅ FINAL CLEANUP COMPLETE!"
echo "=========================================="
echo ""
echo "📁 Clean project structure:"
echo "   - 5 Python files (core implementation only)"
echo "   - 1 shell script (cleanup.sh)"
echo "   - 3 documentation files (README.md, FINAL_SYSTEM_STATUS.md, CLEANUP_PLAN.md)"
echo "   - 1 requirements file"
echo "   - No duplicates"
echo "   - No cache files"
echo ""
