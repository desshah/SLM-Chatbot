# Backup of Unused Files - November 25, 2025

## Purpose
This folder contains files that were used during setup/development but are not needed for running the chatbot application.

## Files Backed Up

### Setup & Build Scripts (One-time use)
1. **enhanced_vector_db.py** - Vector database builder (already executed, DB is built)
2. **rebuild_rag_system.py** - Web crawler for data collection (already executed)
3. **integrate_raw_data.py** - Script to integrate raw training data (already executed)
4. **integrate_training_data.py** - Script to prepare training datasets (already executed)

### Cleanup Scripts (Historical)
5. **cleanup.sh** - Initial cleanup script (already executed)
6. **final_cleanup.sh** - Final cleanup script (already executed)

## Why These Files Are Not Needed

- **Vector DB is already built** - The `vector_db/` folder contains the complete ChromaDB with 507 documents and 1,158 chunks
- **Training data is already integrated** - The `data/` folder contains processed data files
- **Cleanup is complete** - Project structure is already organized

## Active Implementation Files (Kept in Root)

1. **streamlit_app.py** - Main UI application
2. **enhanced_rag_chatbot.py** - Core chatbot logic with dual-mode system
3. **config.py** - Configuration settings
4. **requirements.txt** - Python dependencies
5. **README.md** - Main documentation
6. **start_enhanced_chatbot.sh** - Launch script

## How to Restore (if needed)

If you need any of these files for rebuilding or debugging:
```bash
cp backup_unused_files_20251125/<filename> .
```

To restore all files:
```bash
cp backup_unused_files_20251125/*.{py,sh} .
```

## Verification

All files were verified to NOT be imported or used by the active implementation:
- No Python imports reference these files
- Streamlit app only imports: enhanced_rag_chatbot, config
- Enhanced chatbot only imports: config (plus external libraries)

## Data Status

- ✅ Vector DB: 507 documents, 1,158 chunks (290MB)
- ✅ Training Data: 1,220 entries + 5,327 Q&A pairs
- ✅ Embeddings: sentence-transformers/all-MiniLM-L6-v2
- ✅ Model: TinyLlama/TinyLlama-1.1B-Chat-v1.0 (base, no fine-tuning)

