#!/bin/bash

# Quick start script - runs the chatbot
# Make sure you've run setup.sh and build_pipeline.sh first

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "Rackspace Knowledge Chatbot"
echo "========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Please run setup.sh first:"
    echo "  ./setup.sh"
    exit 1
fi

# Activate virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check if vector database exists
if [ ! -d "vector_db" ] || [ -z "$(ls -A vector_db)" ]; then
    echo -e "${YELLOW}Warning: Vector database not found${NC}"
    echo "Please run the build pipeline first:"
    echo "  ./build_pipeline.sh"
    echo ""
    read -p "Do you want to build it now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ./build_pipeline.sh
    else
        exit 1
    fi
fi

# Start the chatbot
echo ""
echo -e "${GREEN}Starting Rackspace Knowledge Chatbot...${NC}"
echo ""
echo "The web interface will open at: http://localhost:7860"
echo "Press Ctrl+C to stop the server"
echo ""
echo "========================================="
echo ""

python app.py
