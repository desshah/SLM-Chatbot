#!/bin/bash

# Build pipeline script for Rackspace Knowledge Chatbot
# Runs all preparation steps in sequence

set -e  # Exit on error

echo "========================================="
echo "Rackspace Chatbot - Build Pipeline"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Virtual environment not activated. Activating...${NC}"
    source venv/bin/activate
fi

echo "This script will run the following steps:"
echo "1. Collect Rackspace data from public sources"
echo "2. Build vector database for RAG"
echo "3. Prepare training dataset"
echo "4. (Optional) Fine-tune the model"
echo ""

# Step 1: Data Collection
echo "========================================="
echo -e "${BLUE}Step 1/4: Collecting Rackspace Data${NC}"
echo "========================================="
echo ""
python data_collection.py
echo ""
echo -e "${GREEN}✓ Step 1 Complete${NC}"
echo ""

# Step 2: Build Vector Database
echo "========================================="
echo -e "${BLUE}Step 2/4: Building Vector Database${NC}"
echo "========================================="
echo ""
python vector_db.py
echo ""
echo -e "${GREEN}✓ Step 2 Complete${NC}"
echo ""

# Step 3: Prepare Dataset
echo "========================================="
echo -e "${BLUE}Step 3/4: Preparing Training Dataset${NC}"
echo "========================================="
echo ""
python prepare_dataset.py
echo ""
echo -e "${GREEN}✓ Step 3 Complete${NC}"
echo ""

# Step 4: Fine-tune Model (optional)
echo "========================================="
echo -e "${BLUE}Step 4/4: Fine-tune Model (Optional)${NC}"
echo "========================================="
echo ""
echo -e "${YELLOW}Fine-tuning will take 30-60 minutes on M3 Mac${NC}"
read -p "Do you want to fine-tune the model? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting fine-tuning..."
    python fine_tune.py
    echo ""
    echo -e "${GREEN}✓ Step 4 Complete - Model fine-tuned${NC}"
else
    echo ""
    echo -e "${YELLOW}⊘ Skipping fine-tuning - will use base model${NC}"
fi

echo ""
echo "========================================="
echo -e "${GREEN}Build Pipeline Complete!${NC}"
echo "========================================="
echo ""
echo "Your chatbot is ready to use!"
echo ""
echo "To start the chatbot:"
echo "  python app.py"
echo ""
echo "Then open your browser to: http://localhost:7860"
echo ""
