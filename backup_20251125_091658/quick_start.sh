#!/bin/bash

# Quick Start Script for Enhanced Rackspace Chatbot
# This script provides a simple interface to rebuild and run the chatbot

clear
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║    🚀 ENHANCED RACKSPACE CHATBOT - QUICK START              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "This script will help you rebuild the chatbot with:"
echo "  ✅ Perfect data collection (ALL Rackspace websites)"
echo "  ✅ No navigation text (filtered content only)"
echo "  ✅ Full training data integration (4,107 Q&A pairs)"
echo "  ✅ Enhanced vector database"
echo "  ✅ Better responses"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo ""
    echo "Please activate it first:"
    echo "  source venv/bin/activate"
    echo "  or"
    echo "  source .venv/bin/activate"
    echo ""
    exit 1
fi

echo "✅ Virtual environment: activated"
echo ""

# Menu
echo "What would you like to do?"
echo ""
echo "  1) 🔨 Full Rebuild (recommended)"
echo "     - Collect data from ALL Rackspace sites"
echo "     - Build enhanced vector database"
echo "     - Test the system"
echo "     Time: ~20-40 minutes"
echo ""
echo "  2) 🏃 Quick Launch (skip rebuild)"
echo "     - Launch chatbot with existing data"
echo "     - Use current vector database"
echo "     Time: ~30 seconds"
echo ""
echo "  3) 🧪 Test Only"
echo "     - Run test queries"
echo "     - Verify system quality"
echo "     Time: ~1 minute"
echo ""
echo "  4) ℹ️  Show System Info"
echo "     - Check data collection status"
echo "     - Show vector database stats"
echo ""
echo "  5) 📖 View Documentation"
echo "     - Open rebuild guide"
echo ""
echo "  6) ❌ Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "🔨 STARTING FULL REBUILD"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        echo "⏱️  This will take approximately 20-40 minutes"
        echo ""
        read -p "Continue? (y/n): " confirm
        if [[ $confirm == [yY] ]]; then
            ./enhanced_build_pipeline.sh
            
            echo ""
            echo "═══════════════════════════════════════════════════════════════"
            echo "✅ REBUILD COMPLETE!"
            echo "═══════════════════════════════════════════════════════════════"
            echo ""
            echo "🚀 Ready to launch chatbot!"
            echo ""
            read -p "Launch Streamlit UI now? (y/n): " launch
            if [[ $launch == [yY] ]]; then
                echo ""
                echo "Starting Streamlit..."
                echo "Access at: http://localhost:8501"
                echo ""
                streamlit run streamlit_app.py
            fi
        fi
        ;;
    
    2)
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "🏃 QUICK LAUNCH"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        
        # Check if enhanced data exists
        if [ ! -f "data/rackspace_knowledge.json" ]; then
            echo "⚠️  Warning: No data found!"
            echo "   Please run 'Full Rebuild' first (option 1)"
            echo ""
            exit 1
        fi
        
        # Check if vector DB exists
        if [ ! -d "vector_db" ]; then
            echo "⚠️  Warning: No vector database found!"
            echo "   Please run 'Full Rebuild' first (option 1)"
            echo ""
            exit 1
        fi
        
        echo "✅ Data found"
        echo "✅ Vector database found"
        echo ""
        echo "🚀 Starting Streamlit..."
        echo "   Access at: http://localhost:8501"
        echo ""
        streamlit run streamlit_app.py
        ;;
    
    3)
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "🧪 RUNNING SYSTEM TESTS"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        
        python -c "
from enhanced_rag_chatbot import get_chatbot

print('Initializing chatbot...\n')
chatbot = get_chatbot()

test_questions = [
    'What are Rackspace cloud adoption and migration services?',
    'How does Rackspace help with AWS deployment?',
    'What security services does Rackspace offer?'
]

print('═' * 80)
for i, question in enumerate(test_questions, 1):
    print(f'\n🧪 Test {i}/3: {question}\n')
    response = chatbot.chat(question)
    print(f'🤖 Response:\n{response}\n')
    print('─' * 80)

print('\n✅ All tests complete!')
print('═' * 80)
"
        ;;
    
    4)
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "ℹ️  SYSTEM INFORMATION"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
        
        echo "📊 Data Collection Status:"
        if [ -f "data/rackspace_knowledge.json" ]; then
            size=$(ls -lh data/rackspace_knowledge.json | awk '{print $5}')
            echo "   ✅ Data file exists: $size"
            
            if [ -f "data/crawl_statistics.json" ]; then
                docs=$(python -c "import json; print(json.load(open('data/crawl_statistics.json'))['total_documents'])" 2>/dev/null)
                words=$(python -c "import json; print(json.load(open('data/crawl_statistics.json'))['total_words'])" 2>/dev/null)
                echo "   📄 Documents: $docs"
                echo "   📝 Words: $words"
            fi
        else
            echo "   ❌ No data file found"
            echo "   → Run 'Full Rebuild' (option 1)"
        fi
        
        echo ""
        echo "🗄️  Vector Database Status:"
        if [ -d "vector_db" ]; then
            size=$(du -sh vector_db | awk '{print $1}')
            echo "   ✅ Vector DB exists: $size"
        else
            echo "   ❌ No vector database found"
            echo "   → Run 'Full Rebuild' (option 1)"
        fi
        
        echo ""
        echo "📚 Training Data Status:"
        if [ -f "data/training_qa_pairs.json" ]; then
            pairs=$(python -c "import json; print(len(json.load(open('data/training_qa_pairs.json'))))" 2>/dev/null)
            echo "   ✅ Training data: $pairs Q&A pairs"
        else
            echo "   ❌ No training data found"
        fi
        
        echo ""
        echo "🤖 Model Status:"
        if [ -d "models/rackspace_finetuned" ]; then
            echo "   ✅ Fine-tuned model available"
        else
            echo "   ⚠️  Using base model (fine-tuned not available)"
            echo "   → Optional: Run 'python fine_tune_cpu.py' to create"
        fi
        
        echo ""
        ;;
    
    5)
        echo ""
        echo "📖 Opening documentation..."
        echo ""
        
        if [ -f "ENHANCED_REBUILD_GUIDE.md" ]; then
            if command -v open &> /dev/null; then
                open ENHANCED_REBUILD_GUIDE.md
            elif command -v xdg-open &> /dev/null; then
                xdg-open ENHANCED_REBUILD_GUIDE.md
            else
                cat ENHANCED_REBUILD_GUIDE.md
            fi
        else
            echo "❌ Documentation not found"
        fi
        ;;
    
    6)
        echo ""
        echo "👋 Goodbye!"
        echo ""
        exit 0
        ;;
    
    *)
        echo ""
        echo "❌ Invalid choice"
        echo ""
        exit 1
        ;;
esac

echo ""
echo "Done! 🎉"
echo ""
