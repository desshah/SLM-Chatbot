"""
Safe Raw Data Integration Script
Processes raw .txt files from rackspace-rag-chatbot and adds them to chatbot-rackspace
WITHOUT breaking existing functionality.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import shutil

# Paths
SOURCE_RAW_DIR = Path("/Users/deshnashah/Downloads/final/rackspace-rag-chatbot/data/raw")
TARGET_DATA_DIR = Path("/Users/deshnashah/Downloads/final/chatbot-rackspace/data")
ENHANCED_KNOWLEDGE_FILE = TARGET_DATA_DIR / "rackspace_knowledge_enhanced.json"

# Output file for the new integration
NEW_INTEGRATION_FILE = TARGET_DATA_DIR / "rackspace_knowledge_from_raw.json"
FINAL_MERGED_FILE = TARGET_DATA_DIR / "rackspace_knowledge_complete.json"


def extract_url_from_filename(filename: str) -> str:
    """
    Extract URL from filename pattern: rackspace_0001_https_www_rackspace_com.txt
    Converts underscores to slashes and adds proper protocol
    """
    # Remove the prefix (rackspace_XXXX_) and .txt suffix
    url_part = re.sub(r'^rackspace_\d+_', '', filename)
    url_part = url_part.replace('.txt', '')
    
    # Replace underscores with appropriate characters
    # First occurrence of http or https
    if url_part.startswith('https_'):
        url_part = url_part.replace('https_', 'https://', 1)
        url_part = url_part.replace('_', '/', 1)  # Replace first _ after https with /
    elif url_part.startswith('http_'):
        url_part = url_part.replace('http_', 'http://', 1)
        url_part = url_part.replace('_', '/', 1)  # Replace first _ after http with /
    
    # Replace remaining underscores with dashes or slashes based on context
    url_part = url_part.replace('_', '-')
    
    # Fix common patterns
    url_part = url_part.replace('docs-rackspace-com', 'docs.rackspace.com')
    url_part = url_part.replace('www-rackspace-com', 'www.rackspace.com')
    url_part = url_part.replace('fair-rackspace-com', 'fair.rackspace.com')
    url_part = url_part.replace('spot-rackspace-com', 'spot.rackspace.com')
    url_part = url_part.replace('/-', '/')
    
    return url_part


def read_raw_file(filepath: Path) -> Dict[str, str]:
    """
    Read a raw .txt file and extract URL and content
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extract URL from first line if present
        url_match = re.match(r'^URL:\s+(https?://[^\s]+)', content)
        if url_match:
            url = url_match.group(1)
            # Remove the URL line from content
            content = re.sub(r'^URL:\s+https?://[^\s]+\n*', '', content)
        else:
            # Try to extract from filename
            url = extract_url_from_filename(filepath.name)
        
        # Clean content
        content = content.strip()
        
        return {
            "url": url,
            "content": content
        }
    except Exception as e:
        print(f"⚠️  Error reading {filepath.name}: {e}")
        return None


def generate_title_from_url(url: str) -> str:
    """Generate a descriptive title from URL"""
    # Extract path from URL
    parts = url.rstrip('/').split('/')
    
    # Get the last meaningful part
    if len(parts) > 3:
        last_part = parts[-1] if parts[-1] else parts[-2]
    else:
        last_part = "Rackspace Documentation"
    
    # Clean up the title
    title = last_part.replace('-', ' ').replace('_', ' ').title()
    
    # Add context based on domain
    if 'docs.rackspace' in url:
        title = f"{title} | Rackspace Docs"
    elif 'fair.rackspace' in url:
        title = f"{title} | FAIR by Rackspace"
    elif 'spot.rackspace' in url:
        title = f"{title} | SPOT Marketplace"
    else:
        title = f"{title} | Rackspace"
    
    return title


def process_raw_files() -> List[Dict]:
    """
    Process all raw .txt files from rackspace-rag-chatbot
    """
    print("🔍 Scanning raw files...")
    
    if not SOURCE_RAW_DIR.exists():
        print(f"❌ Source directory not found: {SOURCE_RAW_DIR}")
        return []
    
    raw_files = sorted(SOURCE_RAW_DIR.glob("*.txt"))
    print(f"📁 Found {len(raw_files)} raw files to process")
    
    documents = []
    processed = 0
    skipped = 0
    
    for filepath in raw_files:
        # Read and extract
        data = read_raw_file(filepath)
        
        if not data or not data.get('content') or len(data['content']) < 200:
            skipped += 1
            continue
        
        # Calculate word count
        word_count = len(data['content'].split())
        
        # Create document entry
        doc = {
            "url": data['url'],
            "title": generate_title_from_url(data['url']),
            "content": data['content'],
            "word_count": word_count,
            "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "rackspace-rag-chatbot-raw",
            "source_file": filepath.name
        }
        
        documents.append(doc)
        processed += 1
        
        if processed % 50 == 0:
            print(f"  Processed {processed}/{len(raw_files)} files...")
    
    print(f"✅ Processed {processed} files successfully")
    print(f"⚠️  Skipped {skipped} files (too short or empty)")
    
    return documents


def load_existing_documents() -> List[Dict]:
    """Load existing enhanced knowledge base"""
    if ENHANCED_KNOWLEDGE_FILE.exists():
        with open(ENHANCED_KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            docs = json.load(f)
        print(f"📚 Loaded {len(docs)} existing documents from enhanced knowledge base")
        return docs
    else:
        print("⚠️  No existing enhanced knowledge base found")
        return []


def merge_documents(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """
    Merge new documents with existing, avoiding duplicates by URL
    """
    print("\n🔄 Merging documents...")
    
    # Create URL index for existing docs
    existing_urls = {doc['url']: doc for doc in existing}
    
    added = 0
    updated = 0
    duplicates = 0
    
    for doc in new:
        url = doc['url']
        
        if url in existing_urls:
            # Check if new doc has more content
            if doc['word_count'] > existing_urls[url].get('word_count', 0):
                existing_urls[url] = doc
                updated += 1
            else:
                duplicates += 1
        else:
            existing_urls[url] = doc
            added += 1
    
    merged = list(existing_urls.values())
    
    print(f"✅ Merge complete:")
    print(f"   - Added: {added} new documents")
    print(f"   - Updated: {updated} existing documents (better content)")
    print(f"   - Duplicates skipped: {duplicates}")
    print(f"   - Total documents: {len(merged)}")
    
    return merged


def create_backup():
    """Create backup of existing files"""
    print("\n📦 Creating backup...")
    
    backup_dir = TARGET_DATA_DIR / f"backup_raw_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        ENHANCED_KNOWLEDGE_FILE,
    ]
    
    backed_up = 0
    for source_file in files_to_backup:
        if source_file.exists():
            dest = backup_dir / source_file.name
            shutil.copy2(source_file, dest)
            backed_up += 1
    
    print(f"✅ Backed up {backed_up} files to {backup_dir.name}")
    return backup_dir


def save_documents(documents: List[Dict], filepath: Path):
    """Save documents to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    print(f"💾 Saved {len(documents)} documents to {filepath.name}")


def main():
    """Main integration process"""
    print("=" * 70)
    print("🚀 Safe Raw Data Integration")
    print("   rackspace-rag-chatbot/data/raw → chatbot-rackspace")
    print("=" * 70)
    print()
    
    # Step 1: Create backup
    backup_dir = create_backup()
    
    # Step 2: Process raw files
    print("\n" + "=" * 70)
    print("📄 Processing raw files from rackspace-rag-chatbot")
    print("=" * 70)
    new_documents = process_raw_files()
    
    if not new_documents:
        print("❌ No documents processed. Exiting.")
        return
    
    # Save new documents separately first
    save_documents(new_documents, NEW_INTEGRATION_FILE)
    
    # Step 3: Load existing documents
    print("\n" + "=" * 70)
    print("📚 Loading existing documents")
    print("=" * 70)
    existing_documents = load_existing_documents()
    
    # Step 4: Merge
    print("\n" + "=" * 70)
    print("🔀 Merging documents")
    print("=" * 70)
    merged_documents = merge_documents(existing_documents, new_documents)
    
    # Step 5: Save merged result
    print("\n" + "=" * 70)
    print("💾 Saving final merged data")
    print("=" * 70)
    save_documents(merged_documents, FINAL_MERGED_FILE)
    
    # Also update the enhanced file
    save_documents(merged_documents, ENHANCED_KNOWLEDGE_FILE)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ INTEGRATION COMPLETE!")
    print("=" * 70)
    print(f"📊 Summary:")
    print(f"   - Original documents: {len(existing_documents)}")
    print(f"   - New documents processed: {len(new_documents)}")
    print(f"   - Final total documents: {len(merged_documents)}")
    print(f"   - Backup location: {backup_dir}")
    print()
    print(f"📝 Files created:")
    print(f"   - {NEW_INTEGRATION_FILE.name} (new documents only)")
    print(f"   - {FINAL_MERGED_FILE.name} (complete merged dataset)")
    print(f"   - {ENHANCED_KNOWLEDGE_FILE.name} (updated)")
    print()
    print("📝 Next steps:")
    print("   1. Review the merged data in rackspace_knowledge_complete.json")
    print("   2. Rebuild vector database: source venv/bin/activate && python enhanced_vector_db.py")
    print("   3. Test the chatbot: ./start_enhanced_chatbot.sh")
    print("=" * 70)


if __name__ == "__main__":
    main()
