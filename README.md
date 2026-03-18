# SLM-Chatbot

A Streamlit-based RAG chatbot powered by Groq and ChromaDB.

## What this repo runs

- UI entrypoint: `streamlit_app.py`
- Core chatbot: `enhanced_rag_chatbot.py`
- Config/env handling: `config.py`

## Local run

1. Create and activate a Python environment.
2. Install dependencies from `requirements.txt`.
3. Set `GROQ_API_KEY` in your environment or `.env`.
4. Start the app with Streamlit.

### Required environment variable

- `GROQ_API_KEY`: your Groq API key

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub.
2. In Streamlit Community Cloud, click **Create app**.
3. Select:
	- Repository: `desshah/SLM-Chatbot`
	- Branch: `main`
	- Main file path: `streamlit_app.py`
4. In app **Settings → Secrets**, add:

```toml
GROQ_API_KEY = "your-groq-api-key"
```

5. Deploy.

## Notes

- The app supports both `data/` (legacy) and `document/` (current) folders for data path resolution.
- If your vector DB is missing in deployment, rebuild it locally and commit the required artifacts (if intended), or adjust startup to generate it at runtime.
