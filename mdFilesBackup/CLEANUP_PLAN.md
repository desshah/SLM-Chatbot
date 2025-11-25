# Project Cleanup Analysis

## Files Currently Used in Production

### Core Application Files (KEEP)
- `streamlit_app.py` - Main UI (uses enhanced_rag_chatbot)
- `enhanced_rag_chatbot.py` - Main RAG chatbot implementation
- `enhanced_vector_db.py` - Vector database builder
- `config.py` - Configuration
- `requirements.txt` - Dependencies
- `rebuild_rag_system.py` - NEW proper crawler and RAG builder

### Data Files (KEEP)
- `data/rackspace_knowledge_clean.json` - NEW clean crawled data (13 docs, 12K words)
- `data/training_qa_pairs.json` - Training data for fine-tuning
- `data/training_data.jsonl` - Fine-tuning dataset

### Model Files (KEEP)
- `models/rackspace_finetuned/` - Fine-tuned model

## Duplicate/Unused Files to DELETE

### Old/Deprecated Chatbot Versions
- `rag_chatbot.py` - OLD version (replaced by enhanced_rag_chatbot.py)
- `vector_db.py` - OLD version (replaced by enhanced_vector_db.py)
- `app.py` - OLD Flask app (replaced by streamlit_app.py)

### Old Data Collection Scripts
- `data_collection.py` - OLD crawler (poor content extraction)
- `enhanced_data_collection.py` - OLD enhanced crawler
- `proper_crawler.py` - Intermediate version
- `crawl_specific_urls.py` - ONE-TIME script (already used)
- `prepare_dataset.py` - Duplicate of prepare_finetuning_dataset.py
- `prepare_finetuning_dataset.py` - ONE-TIME script (training data already prepared)

### Old Data Files
- `data/rackspace_knowledge.json` - OLD crawled data (poor quality - 686 docs with nav text)
- `data/crawl_statistics.json` - Statistics file (not used)
- `data/rackspace_knowledge.txt` - Text dump (not used)

### Testing Scripts (Not needed in production)
- `test_system.py` - Testing script
- `quick_test.py` - Quick test script

### Old Pipeline Scripts
- `build_pipeline.sh` - OLD pipeline
- `enhanced_build_pipeline.sh` - OLD enhanced pipeline
- `auto_complete_pipeline.sh` - Old automation
- `setup.sh` - OLD setup
- `quick_start.sh` - OLD quick start
- `start_chatbot.sh` - OLD start script
- `start_streamlit.sh` - OLD streamlit start (just use: streamlit run streamlit_app.py)

### Old Monitoring Scripts
- `check_progress.sh` - Not needed
- `check_finetuning.sh` - Not needed
- `check_vector_build.sh` - Not needed

### Fine-tuning Scripts (ONE-TIME USE - Already completed)
- `fine_tune.py` - Training script (model already trained for 6h 13min)
- `fine_tune_cpu.py` - CPU training script

### Documentation Files (KEEP ONLY USEFUL ONES, DELETE REST)

#### KEEP (Useful):
- `README.md` - Main documentation
- `FINAL_SYSTEM_STATUS.md` - Current system status

#### DELETE (Outdated/Redundant):
- `BACKEND_API_GUIDE.md` - Not using API
- `BEFORE_AFTER_COMPARISON.md` - Historical comparison
- `COLLECTION_SUCCESS_SUMMARY.md` - Old collection stats
- `COMPLETE_SOLUTION.md` - Redundant
- `CURRENT_STATUS.md` - Outdated (use FINAL_SYSTEM_STATUS.md)
- `DATA_PREPROCESSING_EXPLAINED.md` - Outdated process docs
- `EMBEDDINGS_VECTOR_DB_GUIDE.md` - Outdated guide
- `ENHANCED_REBUILD_GUIDE.md` - Outdated guide
- `FINAL_RAG_PIPELINE.md` - Outdated pipeline docs
- `FINETUNING_STATUS.md` - Historical status
- `FIXES_APPLIED.md` - Historical fixes
- `FRONTEND_UI_GUIDE.md` - Outdated UI guide
- `GETTING_STARTED.md` - Outdated
- `LAUNCH_GUIDE.md` - Outdated
- `PROJECT_STRUCTURE.md` - Outdated structure
- `PROPOSED_CHANGES.md` - Historical proposals
- `QUICKSTART.md` - Redundant with README
- `START_HERE.md` - Redundant with README
- `SUMMARY.md` - Historical summary
- `TEXT_PREPROCESSING_PIPELINE.md` - Outdated preprocessing docs
- `TRAINING_PROGRESS_REPORT.md` - Historical training report
- `TRAINING_STARTED.md` - Historical training status
- `UI_COMPARISON.md` - Historical UI comparison
- `VISUAL_GUIDE.md` - Historical visual guide
- `WHAT_TO_DO_NOW.md` - Outdated next steps
- `YOUR_OWN_MODEL.md` - Historical model docs

### Log Files (DELETE)
- `app_output.log`
- `data_collection.log`
- `fine_tune.log`
- `vector_build.log`
- `logs/` directory (if any logs inside)

## Summary
- **Total files to delete**: ~50+ files
- **Core files to keep**: ~10 files
- **Space saved**: Significant (removing old data files, logs, redundant docs)
