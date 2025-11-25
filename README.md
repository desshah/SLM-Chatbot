# 🚀 Rackspace Knowledge Chatbot

An end-to-end intelligent chatbot using **Retrieval-Augmented Generation (RAG)** and **YOUR OWN fine-tuned small language model** to answer questions about Rackspace Technology. This is NOT an agent-based system - it's YOUR OWN trained model that you build from scratch using comprehensive web-crawled data and fine-tuning.

## ✨ Features

- 🤖 **YOUR OWN Fine-tuned LLM**: TinyLlama-1.1B model that YOU train on Rackspace knowledge
- 🕷️ **Comprehensive BFS Web Crawling**: Collects extensive data from all Rackspace domains
- 📚 **RAG System**: Vector database (ChromaDB) for accurate information retrieval
- 💬 **Conversation Memory**: Remembers chat history for context-aware responses
- 🎨 **User-friendly UI**: Beautiful Gradio interface
- 🍎 **M3 Optimized**: Leverages Apple Silicon MPS for efficient training and inference
- 🔓 **100% Open Source**: All free and open-source tools
- 🚫 **NO AGENTS**: This is YOUR model, trained by YOU, owned by YOU

## 🎯 Key Difference: Your Own Model vs Agents

**This chatbot uses YOUR OWN trained model, NOT agents:**
- ✅ YOU collect the training data through comprehensive web crawling
- ✅ YOU fine-tune the model on this data
- ✅ The model learns Rackspace knowledge directly (not retrieved on-the-fly)
- ✅ Full control over the model behavior and responses
- ✅ No reliance on external APIs or agent frameworks
- ✅ Your model, your data, your deployment

## 📋 System Requirements

- **Hardware**: Apple M3 Mac (or any Mac with Apple Silicon), 16GB RAM
- **OS**: macOS 15.5 or later
- **Python**: 3.9 or later
- **Storage**: ~10GB for models and data

## 🛠️ Installation

### 1. Clone or Set Up the Project

```bash
cd /Users/deshnashah/Downloads/final/chatbot-rackspace
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: Installation may take 10-15 minutes as it downloads several ML libraries.

## 🚀 Quick Start (Step-by-Step)

### Step 1: Collect Rackspace Data (Comprehensive BFS Crawling)

Collect extensive data from all Rackspace domains using BFS (Breadth-First Search):

```bash
python data_collection.py
```

This will:
- **BFS crawl multiple Rackspace domains**: rackspace.com, docs.rackspace.com, spot.rackspace.com, etc.
- Follow links up to 3 levels deep (/xyz/, /xyz/abc/, etc.)
- Collect up to 100 pages per domain
- Extract clean, structured content
- Add curated knowledge about Rackspace
- Save comprehensive training data to `data/rackspace_knowledge.json`

**Expected output**: 200-500+ documents with rich Rackspace knowledge

**Time**: 10-30 minutes (depending on crawl depth and network speed)

### Step 2: Build Vector Database

Create embeddings and build the vector database for RAG:

```bash
python vector_db.py
```

This will:
- Load collected data
- Generate embeddings using sentence-transformers
- Store in ChromaDB vector database
- Test retrieval functionality

**Expected output**: Vector database with 100-500 chunks

### Step 3: Prepare Training Dataset

Generate Q&A pairs for fine-tuning:

```bash
python prepare_dataset.py
```

This will:
- Create Q&A pairs from collected data
- Format data for model training
- Save to `data/training_data.jsonl`

**Expected output**: 50-200 training examples

### Step 4: Fine-tune the Model (Build YOUR OWN Model)

**This is where YOU create YOUR OWN Rackspace expert model!**

Fine-tune TinyLlama on the comprehensive Rackspace knowledge you collected:

```bash
python fine_tune.py
```

This will:
- Download TinyLlama-1.1B base model
- Fine-tune using LoRA (parameter-efficient)
- Train on YOUR collected Rackspace data
- Create YOUR OWN Rackspace expert model
- Save to `models/rackspace_finetuned/`

**Time**: 30-60 minutes on M3 Mac  
**Note**: This is ESSENTIAL to create YOUR OWN model. The model learns Rackspace knowledge during training, not from external agents. You can skip this and use base model for testing, but fine-tuning is what makes it YOUR specialized Rackspace expert.

**This is NOT an agent** - it's neural network weights that encode Rackspace knowledge!

### Step 5: Launch the Chatbot UI

Start the Gradio web interface:

```bash
python app.py
```

This will:
- Initialize the RAG chatbot
- Start web server on http://localhost:7860
- Open in your browser automatically

## 💡 Usage Examples

Once the chatbot is running, try these questions:

```
User: Tell me about Rackspace
Bot: [Provides overview of Rackspace Technology]

User: What is their mission?
Bot: [Explains Rackspace's mission]

User: What did I ask first?
Bot: Your first question was: Tell me about Rackspace
```

The chatbot maintains conversation history and can recall previous questions!

## 📁 Project Structure

```
chatbot-rackspace/
├── app.py                      # Main Gradio UI application
├── rag_chatbot.py             # RAG chatbot with conversation history
├── fine_tune.py               # Model fine-tuning script
├── vector_db.py               # Vector database manager
├── data_collection.py         # Data scraping script
├── prepare_dataset.py         # Dataset preparation
├── config.py                  # Configuration settings
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── data/                      # Data directory
│   ├── rackspace_knowledge.json
│   ├── training_data.jsonl
│   └── training_qa_pairs.json
├── models/                    # Model directory
│   └── rackspace_finetuned/   # Fine-tuned model
└── vector_db/                 # Vector database
    └── chroma.sqlite3
```

## ⚙️ Configuration

Edit `config.py` to customize:

- **Model selection**: Choose between TinyLlama, Phi-2, or other models
- **Training parameters**: Adjust epochs, batch size, learning rate
- **RAG settings**: Configure retrieval top-k, chunk size
- **Generation parameters**: Temperature, max tokens, etc.

## 🔧 Troubleshooting

### Issue: "MPS backend not available"
**Solution**: Update to latest macOS and ensure you have an M-series Mac.

### Issue: "Out of memory during fine-tuning"
**Solution**: Reduce `BATCH_SIZE` in `config.py` from 4 to 2 or 1.

### Issue: "Vector database empty"
**Solution**: Run `python vector_db.py` to rebuild the database.

### Issue: "Model not found"
**Solution**: The app will automatically use the base model if fine-tuned model isn't available.

### Issue: "ImportError for packages"
**Solution**: Ensure virtual environment is activated and reinstall requirements:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 🎯 How It Works

### 1. **Data Collection**
- Scrapes public Rackspace information
- Adds manually curated knowledge
- Stores structured data

### 2. **Vector Database (RAG)**
- Chunks documents into smaller pieces
- Generates embeddings using sentence-transformers
- Stores in ChromaDB for fast retrieval
- Retrieves top-k relevant chunks for each query

### 3. **Fine-tuning**
- Uses LoRA (Low-Rank Adaptation) for efficient training
- Trains on Rackspace Q&A pairs
- Optimized for Apple Silicon MPS
- Saves adapter weights only (~10MB vs 2GB full model)

### 4. **RAG Pipeline**
- Takes user query
- Retrieves relevant context from vector DB
- Combines context + conversation history
- Generates response with fine-tuned model
- Maintains conversation memory

### 5. **Conversation History**
- Stores last 5 conversation turns
- Enables context-aware follow-up questions
- Can recall previous questions
- Natural conversation flow

## 🔬 Technical Details

### Models Used
- **Base LLM**: TinyLlama-1.1B-Chat-v1.0 (1.1B parameters)
- **Alternative**: Microsoft Phi-2 (2.7B parameters)
- **Embeddings**: all-MiniLM-L6-v2 (384 dimensions)

### Technologies
- **Transformers**: Hugging Face transformers library
- **PEFT**: Parameter-efficient fine-tuning with LoRA
- **ChromaDB**: Vector database for embeddings
- **Sentence-Transformers**: Generate text embeddings
- **Gradio**: Web UI framework
- **PyTorch**: Deep learning framework with MPS support

### Performance
- **Inference speed**: ~1-2 seconds per response on M3
- **Memory usage**: ~4-6GB RAM
- **Model size**: ~2GB base + ~10MB LoRA adapters

## 📊 Dataset

The chatbot is trained on:
- Rackspace official website content
- Rackspace documentation
- Manually curated knowledge base
- Generated Q&A pairs

All data is publicly available information about Rackspace Technology.

## 🤝 Contributing

Feel free to enhance the chatbot:
- Add more Rackspace knowledge sources
- Improve data collection scripts
- Experiment with different models
- Enhance the UI

## 📝 License

This project uses open-source components:
- TinyLlama: Apache 2.0
- Transformers: Apache 2.0
- ChromaDB: Apache 2.0
- Gradio: Apache 2.0

## 🙏 Acknowledgments

- **TinyLlama** team for the efficient base model
- **Hugging Face** for transformers library
- **ChromaDB** for vector database
- **Gradio** for the UI framework
- **Rackspace Technology** for publicly available information

## 📧 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the logs in terminal
3. Ensure all setup steps were completed

## 🎉 Example Conversations

**Example 1: Basic Information**
```
User: What is Rackspace?
Bot: Rackspace Technology is a leading provider of end-to-end multicloud 
     solutions. Founded in 1998, Rackspace delivers expert services across 
     AWS, Azure, Google Cloud, and more.
```

**Example 2: Follow-up Questions**
```
User: Tell me about Rackspace
Bot: [Provides overview]

User: What's their mission?
Bot: Rackspace's mission is to design, build, and operate customers' 
     multi-cloud environments with Fanatical Experience.
```

**Example 3: Conversation Memory**
```
User: What services does Rackspace offer?
Bot: [Lists services]

User: Tell me more about the first one
Bot: [Expands on first service mentioned]

User: What did I ask first?
Bot: Your first question was: What services does Rackspace offer?
```

---

## 🚀 Quick Reference Commands

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build Pipeline
python data_collection.py      # Step 1: Collect data
python vector_db.py            # Step 2: Build vector DB
python prepare_dataset.py      # Step 3: Prepare training data
python fine_tune.py            # Step 4: Fine-tune model (optional)

# Run
python app.py                  # Launch chatbot UI

# Test Components
python rag_chatbot.py          # Test RAG system
```

---

**Ready to chat with your Rackspace Knowledge Chatbot!** 🚀💬
