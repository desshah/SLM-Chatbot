# 📁 Project Structure

```
chatbot-rackspace/
│
├── 📄 README.md                    # Complete documentation
├── 📄 QUICKSTART.md                # Quick start guide
├── 📄 requirements.txt             # Python dependencies
├── 📄 .gitignore                   # Git ignore rules
│
├── 🔧 Configuration & Core
│   ├── config.py                   # Central configuration
│   └── test_system.py              # System verification script
│
├── 🛠️ Setup Scripts
│   ├── setup.sh                    # Initial setup (makes venv, installs deps)
│   ├── build_pipeline.sh           # Builds data & model pipeline
│   └── start_chatbot.sh            # Launches the chatbot UI
│
├── 📊 Data Pipeline
│   ├── data_collection.py          # Scrapes Rackspace information
│   ├── prepare_dataset.py          # Creates Q&A training pairs
│   └── vector_db.py                # Builds vector database for RAG
│
├── 🤖 Model & AI
│   ├── fine_tune.py                # Fine-tunes LLM with LoRA
│   └── rag_chatbot.py              # RAG system with conversation history
│
├── 🎨 User Interface
│   └── app.py                      # Gradio web interface
│
├── 📁 data/                        # Data directory (created after build)
│   ├── rackspace_knowledge.json    # Collected Rackspace data
│   ├── rackspace_knowledge.txt     # Human-readable version
│   ├── training_data.jsonl         # Formatted training data
│   └── training_qa_pairs.json      # Q&A pairs for training
│
├── 📁 models/                      # Models directory
│   └── rackspace_finetuned/        # Fine-tuned model (after training)
│       ├── adapter_config.json
│       ├── adapter_model.bin
│       └── tokenizer files...
│
├── 📁 vector_db/                   # Vector database directory
│   └── chroma.sqlite3              # ChromaDB database file
│
├── 📁 logs/                        # Logs directory
│
└── 📁 venv/                        # Virtual environment (after setup)
```

## 🔍 File Descriptions

### Configuration & Core
- **config.py**: Central configuration file with all settings (models, paths, hyperparameters)
- **test_system.py**: Verifies all components are installed and working correctly

### Setup Scripts
- **setup.sh**: Automated setup script (creates venv, installs dependencies)
- **build_pipeline.sh**: Runs the complete data & model pipeline
- **start_chatbot.sh**: Quick script to launch the chatbot

### Data Pipeline
- **data_collection.py**: 
  - Scrapes Rackspace public websites
  - Adds curated knowledge
  - Saves to JSON
  
- **prepare_dataset.py**:
  - Creates Q&A pairs from collected data
  - Formats for instruction-following training
  - Generates training dataset
  
- **vector_db.py**:
  - Chunks documents for embedding
  - Generates embeddings with sentence-transformers
  - Builds ChromaDB vector database
  - Enables semantic search for RAG

### Model & AI
- **fine_tune.py**:
  - Downloads TinyLlama base model
  - Fine-tunes using LoRA (parameter-efficient)
  - Optimized for Apple Silicon M3
  - Saves fine-tuned adapter weights
  
- **rag_chatbot.py**:
  - Implements RAG (Retrieval-Augmented Generation)
  - Manages conversation history
  - Retrieves relevant context from vector DB
  - Generates responses with fine-tuned model

### User Interface
- **app.py**:
  - Beautiful Gradio web interface
  - Chat interface with history display
  - Example questions
  - Real-time responses

## 📦 Generated Directories

### data/
Created after running data collection scripts. Contains all collected and processed data.

**Size**: ~1-5 MB
**Required for**: RAG retrieval and model training

### models/
Contains the fine-tuned model (if training is completed).

**Size**: ~10 MB (LoRA adapters) + ~2 GB (base model, cached by transformers)
**Required for**: Using the fine-tuned model

### vector_db/
ChromaDB vector database for RAG retrieval.

**Size**: ~10-50 MB (depends on data size)
**Required for**: RAG functionality (essential!)

### venv/
Python virtual environment with all dependencies.

**Size**: ~5-8 GB
**Required for**: Running the application

## 🔄 Workflow

```
1. Setup
   setup.sh → Creates venv, installs packages

2. Data Collection
   data_collection.py → data/rackspace_knowledge.json

3. Vector Database
   vector_db.py → vector_db/chroma.sqlite3

4. Dataset Preparation
   prepare_dataset.py → data/training_data.jsonl

5. Fine-tuning (optional)
   fine_tune.py → models/rackspace_finetuned/

6. Launch
   app.py → Web interface at localhost:7860
```

## 💾 Disk Space Requirements

| Component | Size | Required |
|-----------|------|----------|
| Virtual Environment | ~5-8 GB | ✅ Yes |
| Base Model (cached) | ~2 GB | ✅ Yes |
| Fine-tuned Adapters | ~10 MB | ⭕ Optional |
| Vector Database | ~10-50 MB | ✅ Yes |
| Training Data | ~1-5 MB | ✅ Yes |
| **Total** | **~7-10 GB** | - |

## 🎯 Key Features Per File

| File | Key Features |
|------|-------------|
| **config.py** | Centralized settings, easy customization |
| **data_collection.py** | Web scraping, manual knowledge, structured data |
| **vector_db.py** | Semantic search, embeddings, ChromaDB |
| **prepare_dataset.py** | Q&A generation, instruction format |
| **fine_tune.py** | LoRA training, MPS support, checkpoint saving |
| **rag_chatbot.py** | Context retrieval, history management, generation |
| **app.py** | Beautiful UI, examples, real-time chat |

## 🔧 Customization Points

Want to customize? Edit these files:

- **Model selection**: `config.py` → `BASE_MODEL_NAME`
- **Training parameters**: `config.py` → LoRA settings, batch size, epochs
- **Retrieval settings**: `config.py` → `TOP_K_RETRIEVAL`, `CHUNK_SIZE`
- **UI appearance**: `app.py` → Custom CSS, examples
- **Data sources**: `data_collection.py` → `RACKSPACE_URLS`
- **Knowledge**: `data_collection.py` → `add_manual_knowledge()`

## 🐛 Debug Mode

To enable verbose logging, edit any Python file and change:
```python
logging.basicConfig(level=logging.DEBUG)  # Instead of INFO
```

## 📊 Monitoring

Check these logs during operation:
- Terminal output shows all operations
- Gradio shows request/response in UI
- Model generates in real-time (you can see it in terminal)

---

**Need help? Check the troubleshooting section in README.md**
