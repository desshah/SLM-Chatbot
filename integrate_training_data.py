"""
Data Integration Script
Integrates trained data from rackspace-rag-chatbot into chatbot-rackspace project.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Dict, List

# Paths
SOURCE_DATA_DIR = Path("/Users/deshnashah/Downloads/final/rackspace-rag-chatbot/data")
TARGET_DATA_DIR = Path("/Users/deshnashah/Downloads/final/chatbot-rackspace/data")

# Source files
CHUNKS_FILE = SOURCE_DATA_DIR / "processed" / "rackspace_chunks.jsonl"
TRAIN_FILE = SOURCE_DATA_DIR / "processed" / "rackspace_train.jsonl"
VAL_FILE = SOURCE_DATA_DIR / "processed" / "rackspace_val.jsonl"
FEEDBACK_FILE = SOURCE_DATA_DIR / "feedback" / "user_feedback.jsonl"

# Target files
KNOWLEDGE_FILE = TARGET_DATA_DIR / "rackspace_knowledge_enhanced.json"
TRAINING_FILE = TARGET_DATA_DIR / "training_data_enhanced.jsonl"
QA_PAIRS_FILE = TARGET_DATA_DIR / "training_qa_pairs_enhanced.json"


def extract_url_from_chunk(text: str) -> str:
    """Extract URL from chunk text"""
    match = re.match(r'^URL:\s+(https?://[^\s]+)', text)
    if match:
        return match.group(1)
    return ""


def extract_title_from_url(url: str) -> str:
    """Generate a title from URL"""
    # Extract the last part of the URL and make it readable
    parts = url.rstrip('/').split('/')
    last_part = parts[-1] if parts else 'Unknown'
    
    # Clean up the title
    title = last_part.replace('-', ' ').replace('_', ' ').title()
    return f"{title} | Rackspace Documentation"


def consolidate_chunks() -> List[Dict]:
    """
    Consolidate chunks into full documents matching chatbot-rackspace format
    """
    print("📚 Processing chunks data...")
    
    # Group chunks by doc_id
    doc_chunks = defaultdict(list)
    
    with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                chunk = json.loads(line.strip())
                doc_id = chunk.get('doc_id', '')
                doc_chunks[doc_id].append(chunk)
            except json.JSONDecodeError as e:
                print(f"⚠️  Error parsing line {line_num}: {e}")
                continue
    
    print(f"✅ Found {len(doc_chunks)} unique documents from {line_num} chunks")
    
    # Consolidate chunks into full documents
    documents = []
    
    for doc_id, chunks in doc_chunks.items():
        # Sort chunks by chunk_index
        chunks.sort(key=lambda x: x.get('chunk_index', 0))
        
        # Extract URL from first chunk
        url = extract_url_from_chunk(chunks[0].get('text', ''))
        
        # Consolidate all chunk texts
        full_text = ' '.join([chunk.get('text', '') for chunk in chunks])
        
        # Remove "URL: ..." prefix from the beginning
        full_text = re.sub(r'^URL:\s+https?://[^\s]+\s+', '', full_text)
        
        # Generate title
        title = extract_title_from_url(url) if url else f"Document {doc_id}"
        
        # Calculate word count
        word_count = len(full_text.split())
        
        # Create document in chatbot-rackspace format
        doc = {
            "url": url,
            "title": title,
            "content": full_text.strip(),
            "word_count": word_count,
            "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "rackspace-rag-chatbot",
            "num_chunks": len(chunks)
        }
        
        documents.append(doc)
    
    print(f"✅ Consolidated {len(documents)} documents")
    return documents


def convert_training_data() -> tuple[List[Dict], List[Dict]]:
    """
    Convert training and validation data to chatbot-rackspace format
    Returns: (training_jsonl_entries, qa_pairs)
    """
    print("\n📚 Processing training data...")
    
    training_entries = []
    qa_pairs = []
    
    # Process training file
    train_count = 0
    with open(TRAIN_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                
                # Keep original format for training_data.jsonl
                training_entries.append(entry)
                
                # Convert to Q&A pair format
                qa_pair = {
                    "question": entry.get('instruction', ''),
                    "context": entry.get('input', ''),
                    "answer": entry.get('output', ''),
                    "source": "training",
                    "type": "summarization"
                }
                qa_pairs.append(qa_pair)
                train_count += 1
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Error parsing training line {line_num}: {e}")
                continue
    
    print(f"✅ Processed {train_count} training examples")
    
    # Process validation file
    val_count = 0
    with open(VAL_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                
                # Keep original format for training_data.jsonl
                training_entries.append(entry)
                
                # Convert to Q&A pair format
                qa_pair = {
                    "question": entry.get('instruction', ''),
                    "context": entry.get('input', ''),
                    "answer": entry.get('output', ''),
                    "source": "validation",
                    "type": "summarization"
                }
                qa_pairs.append(qa_pair)
                val_count += 1
                
            except json.JSONDecodeError as e:
                print(f"⚠️  Error parsing validation line {line_num}: {e}")
                continue
    
    print(f"✅ Processed {val_count} validation examples")
    print(f"✅ Total: {len(training_entries)} entries, {len(qa_pairs)} Q&A pairs")
    
    return training_entries, qa_pairs


def merge_with_existing_data(new_docs: List[Dict], new_qa_pairs: List[Dict]):
    """
    Merge new data with existing data, avoiding duplicates
    """
    print("\n🔄 Merging with existing data...")
    
    # Load existing knowledge data
    existing_docs = []
    if KNOWLEDGE_FILE.parent.joinpath("rackspace_knowledge_clean.json").exists():
        with open(KNOWLEDGE_FILE.parent / "rackspace_knowledge_clean.json", 'r', encoding='utf-8') as f:
            existing_docs = json.load(f)
        print(f"📚 Loaded {len(existing_docs)} existing documents")
    
    # Load existing QA pairs
    existing_qa = []
    if KNOWLEDGE_FILE.parent.joinpath("training_qa_pairs.json").exists():
        with open(KNOWLEDGE_FILE.parent / "training_qa_pairs.json", 'r', encoding='utf-8') as f:
            existing_qa = json.load(f)
        print(f"📚 Loaded {len(existing_qa)} existing Q&A pairs")
    
    # Merge documents (avoid duplicates by URL)
    existing_urls = {doc.get('url') for doc in existing_docs}
    unique_new_docs = [doc for doc in new_docs if doc.get('url') not in existing_urls]
    
    all_docs = existing_docs + unique_new_docs
    print(f"✅ Merged documents: {len(existing_docs)} existing + {len(unique_new_docs)} new = {len(all_docs)} total")
    
    # Merge QA pairs
    all_qa = existing_qa + new_qa_pairs
    print(f"✅ Merged Q&A pairs: {len(existing_qa)} existing + {len(new_qa_pairs)} new = {len(all_qa)} total")
    
    return all_docs, all_qa


def save_integrated_data(documents: List[Dict], training_entries: List[Dict], qa_pairs: List[Dict]):
    """
    Save the integrated data to target files
    """
    print("\n💾 Saving integrated data...")
    
    # Ensure target directory exists
    TARGET_DATA_DIR.mkdir(exist_ok=True)
    
    # Save consolidated knowledge base
    with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(documents)} documents to {KNOWLEDGE_FILE}")
    
    # Save training data in JSONL format
    with open(TRAINING_FILE, 'w', encoding='utf-8') as f:
        for entry in training_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f"✅ Saved {len(training_entries)} training entries to {TRAINING_FILE}")
    
    # Save Q&A pairs
    with open(QA_PAIRS_FILE, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(qa_pairs)} Q&A pairs to {QA_PAIRS_FILE}")


def create_backup():
    """
    Create backup of existing data files
    """
    print("\n📦 Creating backup of existing data...")
    
    backup_dir = TARGET_DATA_DIR / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(exist_ok=True)
    
    # Files to backup
    files_to_backup = [
        "rackspace_knowledge_clean.json",
        "training_data.jsonl",
        "training_qa_pairs.json"
    ]
    
    backed_up = 0
    for filename in files_to_backup:
        source = TARGET_DATA_DIR / filename
        if source.exists():
            dest = backup_dir / filename
            import shutil
            shutil.copy2(source, dest)
            backed_up += 1
    
    print(f"✅ Backed up {backed_up} files to {backup_dir}")
    return backup_dir


def main():
    """
    Main integration process
    """
    print("=" * 60)
    print("🚀 Data Integration: rackspace-rag-chatbot → chatbot-rackspace")
    print("=" * 60)
    
    # Verify source files exist
    missing_files = []
    for file_path, name in [
        (CHUNKS_FILE, "Chunks"),
        (TRAIN_FILE, "Training"),
        (VAL_FILE, "Validation")
    ]:
        if not file_path.exists():
            missing_files.append(f"{name}: {file_path}")
    
    if missing_files:
        print("❌ Missing source files:")
        for f in missing_files:
            print(f"   - {f}")
        return
    
    print("✅ All source files found\n")
    
    # Create backup
    backup_dir = create_backup()
    
    # Step 1: Consolidate chunks
    consolidated_docs = consolidate_chunks()
    
    # Step 2: Convert training data
    training_entries, qa_pairs = convert_training_data()
    
    # Step 3: Merge with existing data
    all_docs, all_qa = merge_with_existing_data(consolidated_docs, qa_pairs)
    
    # Step 4: Save integrated data
    save_integrated_data(all_docs, training_entries, all_qa)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ INTEGRATION COMPLETE!")
    print("=" * 60)
    print(f"📊 Summary:")
    print(f"   - Total documents: {len(all_docs)}")
    print(f"   - Total training entries: {len(training_entries)}")
    print(f"   - Total Q&A pairs: {len(all_qa)}")
    print(f"   - Backup location: {backup_dir}")
    print("\n📝 Next steps:")
    print("   1. Review the generated files:")
    print(f"      - {KNOWLEDGE_FILE}")
    print(f"      - {TRAINING_FILE}")
    print(f"      - {QA_PAIRS_FILE}")
    print("   2. Rebuild the vector database:")
    print("      python enhanced_vector_db.py")
    print("   3. Test the enhanced chatbot:")
    print("      streamlit run streamlit_app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
