# 🚀 QUICK START GUIDE

## Get Your Chatbot Running in 3 Steps!

### Step 1: Setup (5 minutes)
```bash
./setup.sh
```
This installs all required dependencies.

### Step 2: Build Pipeline (10-15 minutes, or 30-60 min with fine-tuning)
```bash
source venv/bin/activate
./build_pipeline.sh
```
This collects data, builds the vector database, and optionally fine-tunes the model.

### Step 3: Launch Chatbot
```bash
./start_chatbot.sh
```
Opens at http://localhost:7860

---

## ⚡ Super Quick Start (No Fine-tuning)

If you want to get started immediately without fine-tuning:

```bash
# 1. Setup
./setup.sh

# 2. Activate environment
source venv/bin/activate

# 3. Quick build (skip fine-tuning)
python data_collection.py
python vector_db.py

# 4. Launch
python app.py
```

The chatbot will use the base TinyLlama model (still works great!).

---

## 📊 What Each Step Does

### Setup (`setup.sh`)
- Creates Python virtual environment
- Installs all dependencies
- Creates project directories
- **Time**: ~5-10 minutes

### Build Pipeline (`build_pipeline.sh`)
1. **Data Collection** (1-2 min)
   - Scrapes public Rackspace info
   - Creates knowledge base

2. **Vector Database** (2-3 min)
   - Generates embeddings
   - Builds RAG system

3. **Prepare Dataset** (1 min)
   - Creates Q&A pairs for training

4. **Fine-tune Model** (30-60 min, optional)
   - Trains model on Rackspace knowledge
   - **Can skip this and use base model!**

### Launch (`start_chatbot.sh` or `python app.py`)
- Starts web interface
- Opens in browser
- Ready to chat!

---

## 🎯 Feature Highlights

✅ **Conversation Memory**: Remembers chat history  
✅ **Context-Aware**: Understands follow-up questions  
✅ **RAG-Powered**: Retrieves accurate information  
✅ **Fast**: 1-2 second responses on M3  
✅ **Beautiful UI**: User-friendly Gradio interface  

---

## 💬 Try These Questions

Once running, try:
- "What is Rackspace?"
- "What's their mission?"
- "What did I ask first?" ← Tests conversation memory!
- "Tell me about Fanatical Experience"
- "What cloud platforms do they support?"

---

## 🔧 Troubleshooting

**Dependencies fail to install?**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Out of memory during fine-tuning?**
- Edit `config.py`: Change `BATCH_SIZE = 4` to `BATCH_SIZE = 2`
- Or skip fine-tuning entirely (base model works fine!)

**MPS not available?**
- Ensure you have macOS 12.3+ and M-series Mac
- Model will automatically fall back to CPU

**Chatbot won't start?**
```bash
# Check if vector DB is built
python vector_db.py

# Then try again
python app.py
```

---

## 📁 What Gets Created

```
data/
├── rackspace_knowledge.json     # Collected data
├── rackspace_knowledge.txt      # Human-readable version
├── training_data.jsonl          # Training dataset
└── training_qa_pairs.json       # Q&A pairs

vector_db/
└── chroma.sqlite3              # Vector database

models/
└── rackspace_finetuned/        # Fine-tuned model (if trained)
```

---

## ⏱️ Time Estimates

| Task | Time | Required? |
|------|------|-----------|
| Setup | 5-10 min | ✅ Yes |
| Data Collection | 1-2 min | ✅ Yes |
| Vector Database | 2-3 min | ✅ Yes |
| Dataset Prep | 1 min | ✅ Yes |
| Fine-tuning | 30-60 min | ⭕ Optional |
| **Total (no fine-tuning)** | **~10-15 min** | - |
| **Total (with fine-tuning)** | **~45-75 min** | - |

---

## 🎉 You're All Set!

Your chatbot is a complete RAG system with:
- ✅ Custom-trained model (if fine-tuned)
- ✅ Vector database for accurate retrieval
- ✅ Conversation history management
- ✅ Beautiful user interface
- ✅ Optimized for your M3 Mac

**Enjoy your Rackspace Knowledge Chatbot!** 🚀

---

## 📚 Learn More

See [README.md](README.md) for:
- Detailed architecture
- Configuration options
- Advanced usage
- Technical details
