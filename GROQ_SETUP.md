# Groq API Integration Setup Guide

This guide explains the changes made to integrate Groq API into the Rackspace Knowledge Chatbot.

## What Changed?

### 1. **Removed Local Model (TinyLlama)**
- No longer using `TinyLlama/TinyLlama-1.1B-Chat-v1.0` 
- No longer loading local models with PyTorch
- Removed heavy dependencies: `transformers`, `torch`, `accelerate`, `peft`, `bitsandbytes`

### 2. **Added Groq API Integration**
- Using `groq` Python SDK
- Model: `llama-3.3-70b-versatile` (70B parameters vs 1.1B!)
- Much faster inference with Groq's LPU architecture
- Cloud-based, no local compute needed

### 3. **Files Modified**

#### `config.py`
```python
# OLD (commented out):
# BASE_MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
# FINE_TUNED_MODEL_PATH = MODELS_DIR / "rackspace_finetuned"

# NEW:
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
```

#### `enhanced_rag_chatbot.py`
- Replaced PyTorch model loading with Groq client initialization
- Updated `generate_response()` to use Groq API
- Updated `generate_summary_with_citations()` to use Groq API
- Removed all `torch` dependencies

#### `requirements.txt`
- Removed: `torch`, `transformers`, `accelerate`, `peft`, `bitsandbytes`
- Added: `groq>=0.4.0`

#### `streamlit_app.py`
- Updated to work with Groq-powered chatbot
- Removed reference to fine-tuned model path

## Setup Instructions

### Step 1: Get Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `gsk_...`)

### Step 2: Set Environment Variable

**On macOS/Linux:**
```bash
export GROQ_API_KEY="your_api_key_here"
```

**Make it permanent (add to `~/.zshrc` or `~/.bashrc`):**
```bash
echo 'export GROQ_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

**On Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="your_api_key_here"
```

### Step 3: Install Dependencies

```bash
cd "/Users/deshnashah/Documents/Groq version/chatbot-rackspace"
pip install -r requirements.txt
```

### Step 4: Test the Integration

```bash
python test_groq.py
```

You should see:
```
Testing Groq API connection...
✅ API Key found: gsk_...
✅ Groq client initialized

Testing chat completion...
✅ Response received: Hello from Groq!

🎉 Groq API integration successful!
```

### Step 5: Run the Chatbot

**Option A: Command Line**
```bash
python enhanced_rag_chatbot.py
```

**Option B: Streamlit UI**
```bash
streamlit run streamlit_app.py
```

## Benefits of Groq Integration

### 1. **Performance**
- **Speed**: 300+ tokens/second (vs 10-20 with local TinyLlama)
- **Quality**: 70B parameter model (vs 1.1B)
- **Latency**: ~100ms response time

### 2. **Resource Savings**
- **No GPU needed**: Runs in cloud
- **Lower RAM usage**: No 4GB+ model in memory
- **No disk space**: No model weights to store

### 3. **Better Responses**
- More accurate answers
- Better context understanding
- Natural language generation
- Fewer hallucinations

### 4. **Cost Effective**
- Free tier: 30 requests/minute
- Very affordable paid tiers
- Pay per use (no server costs)

## Available Groq Models

You can change the model in `config.py`:

```python
GROQ_MODEL = "llama-3.3-70b-versatile"  # Default (best quality)
# GROQ_MODEL = "llama-3.1-70b-versatile"  # Alternative
# GROQ_MODEL = "mixtral-8x7b-32768"      # Longer context
# GROQ_MODEL = "gemma2-9b-it"             # Faster, smaller
```

## Troubleshooting

### Error: "GROQ_API_KEY environment variable not set!"
**Solution**: Set the environment variable as shown in Step 2.

### Error: "Invalid API key"
**Solution**: Double-check your API key from Groq console.

### Error: "Rate limit exceeded"
**Solution**: Wait a minute or upgrade your Groq plan.

### Error: "Module 'groq' not found"
**Solution**: Run `pip install groq`

## Architecture Comparison

### OLD (Local Model)
```
User Query → Embedding → Vector DB → Context
    ↓
TinyLlama (local, 1.1B params, slow) → Response
```

### NEW (Groq API)
```
User Query → Embedding → Vector DB → Context
    ↓
Groq API (cloud, 70B params, fast) → Response
```

## Code Example

```python
from groq import Groq
import os

# Initialize client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Generate response
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "What services does Rackspace offer?",
        }
    ],
    model="llama-3.3-70b-versatile",
)

print(chat_completion.choices[0].message.content)
```

## Next Steps

1. ✅ Set up Groq API key
2. ✅ Install dependencies
3. ✅ Test integration
4. ✅ Run chatbot
5. 🎯 Customize prompts in `enhanced_rag_chatbot.py`
6. 🎯 Adjust model parameters (temperature, max_tokens)
7. 🎯 Add conversation history features

## Support

- **Groq Documentation**: [docs.groq.com](https://docs.groq.com)
- **Groq Console**: [console.groq.com](https://console.groq.com)
- **Python SDK**: [github.com/groq/groq-python](https://github.com/groq/groq-python)

---

**Note**: The vector database and RAG pipeline remain unchanged. Only the LLM inference was moved to Groq.
