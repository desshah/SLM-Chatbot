"""
COMPLETE RAG SYSTEM REBUILD
Fixes hallucination issues by:
1. Crawling high-quality content from key Rackspace pages
2. Extracting ONLY main article content (no navigation/menus)
3. Creating proper embeddings with clean chunks
4. Building correct Vector DB for retrieval

This addresses the root cause: poor data quality → bad embeddings → hallucinations
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import List, Dict
import re
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from urllib.parse import urljoin

# Paths
DATA_DIR = Path("data")
VECTOR_DB_DIR = Path("vector_db")
DATA_DIR.mkdir(exist_ok=True)

print("="*80)
print("REBUILDING RAG SYSTEM FROM SCRATCH")
print("="*80)


# Step 1: Define HIGH-VALUE URLs with actual content
HIGH_VALUE_URLS = [
    # Cloud Services
    'https://www.rackspace.com/cloud/cloud-migration',
    'https://www.rackspace.com/cloud/aws',
    'https://www.rackspace.com/cloud/azure',
    'https://www.rackspace.com/cloud/google-cloud',
    'https://www.rackspace.com/cloud/multi-cloud',
    'https://www.rackspace.com/cloud/private-cloud',
    
    # Security
    'https://www.rackspace.com/security',
    'https://www.rackspace.com/security/data-security',
    'https://www.rackspace.com/security/compliance',
    
    # Managed Services
    'https://www.rackspace.com/managed-hosting',
    'https://www.rackspace.com/managed-kubernetes',
    'https://www.rackspace.com/managed-aws',
    'https://www.rackspace.com/managed-azure',
    
    # Professional Services
    'https://www.rackspace.com/professional-services',
    'https://www.rackspace.com/data',
    'https://www.rackspace.com/applications',
    
    # Specific blogs (if you had URLs)
    'https://www.rackspace.com/blog/strengthening-healthcare-operations-through-cyber-resilience',
]


def extract_clean_content(html: str, url: str) -> Dict:
    """Extract ONLY main content, filter out navigation"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove noise
    for element in soup(['script', 'style', 'nav', 'footer', 'header',
                        'aside', 'iframe', 'form', 'button']):
        element.decompose()
    
    # Remove navigation classes
    for nav_class in soup.find_all(class_=re.compile('nav|menu|sidebar|footer|header', re.I)):
        nav_class.decompose()
    
    # Find main content
    main = (soup.find('main') or 
            soup.find('article') or
            soup.find('div', class_=re.compile('content|article', re.I)) or
            soup.body)
    
    if not main:
        return None
    
    # Extract title
    h1 = soup.find('h1')
    title = h1.get_text(strip=True) if h1 else soup.find('title').get_text(strip=True) if soup.find('title') else url
    
    # Extract ONLY paragraphs and headings (real content)
    content_parts = []
    for elem in main.find_all(['p', 'h2', 'h3', 'li']):
        text = elem.get_text(strip=True)
        text = re.sub(r'\s+', ' ', text)
        
        # Skip short fragments and navigation text
        if len(text) > 30 and not any(skip in text.lower() for skip in ['click here', 'learn more', 'view all', 'home']):
            content_parts.append(text)
    
    if len(content_parts) < 3:  # Need at least 3 substantial paragraphs
        return None
    
    content = '\n\n'.join(content_parts)
    word_count = len(content.split())
    
    if word_count < 100:  # Too short
        return None
    
    return {
        'url': url,
        'title': title,
        'content': content,
        'word_count': word_count,
        'crawled_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }


def crawl_urls(urls: List[str]) -> List[Dict]:
    """Crawl URLs and extract clean content"""
    print("\n📡 STEP 1: CRAWLING HIGH-VALUE URLS")
    print("-" * 80)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    data = []
    for i, url in enumerate(urls, 1):
        try:
            print(f"[{i}/{len(urls)}] Crawling: {url}")
            response = session.get(url, timeout=10)
            response.raise_for_status()
            
            content_data = extract_clean_content(response.text, url)
            
            if content_data:
                data.append(content_data)
                print(f"   ✅ Extracted {content_data['word_count']} words")
            else:
                print(f"   ❌ No quality content found")
            
            time.sleep(0.5)  # Be nice
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            continue
    
    print(f"\n✅ Successfully crawled {len(data)} pages with quality content")
    return data


def save_data(data: List[Dict], filename: str = 'rackspace_knowledge_clean.json'):
    """Save crawled data"""
    output_path = DATA_DIR / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    total_words = sum(d['word_count'] for d in data)
    print(f"\n💾 Saved to: {output_path}")
    print(f"   Documents: {len(data)}")
    print(f"   Total words: {total_words:,}")
    print(f"   Avg words/doc: {total_words // len(data) if data else 0}")
    
    return output_path


def create_proper_chunks(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    """Create overlapping chunks from text"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if len(chunk.split()) >= 50:  # Minimum 50 words per chunk
            chunks.append(chunk)
    
    return chunks


def build_vector_db(data: List[Dict]):
    """Build proper vector database with clean embeddings"""
    print("\n🔧 STEP 2: BUILDING VECTOR DATABASE")
    print("-" * 80)
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(
        path=str(VECTOR_DB_DIR),
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Delete old collection
    try:
        client.delete_collection("rackspace_knowledge")
        print("🗑️  Deleted old collection")
    except:
        pass
    
    # Create new collection
    collection = client.create_collection(
        name="rackspace_knowledge",
        metadata={"description": "Clean Rackspace knowledge - main content only"}
    )
    
    # Load embedding model
    print("📦 Loading embedding model...")
    embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    # Process documents into chunks
    print("✂️  Creating chunks...")
    all_chunks = []
    all_metadatas = []
    all_ids = []
    
    chunk_id = 0
    for doc in data:
        # Create chunks from content
        chunks = create_proper_chunks(doc['content'])
        
        for chunk in chunks:
            all_chunks.append(chunk)
            all_metadatas.append({
                'url': doc['url'],
                'title': doc['title'],
                'source': 'document'
            })
            all_ids.append(f"chunk_{chunk_id}")
            chunk_id += 1
    
    print(f"   Created {len(all_chunks)} chunks from {len(data)} documents")
    
    # Generate embeddings
    print("🧮 Generating embeddings...")
    embeddings = embedding_model.encode(
        all_chunks,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    
    # Add to ChromaDB
    print("💾 Adding to vector database...")
    collection.add(
        embeddings=embeddings.tolist(),
        documents=all_chunks,
        metadatas=all_metadatas,
        ids=all_ids
    )
    
    print(f"\n✅ Vector DB built successfully!")
    print(f"   Total chunks indexed: {len(all_chunks)}")
    print(f"   Database location: {VECTOR_DB_DIR}")


def test_retrieval():
    """Test vector DB retrieval"""
    print("\n🧪 STEP 3: TESTING RETRIEVAL")
    print("-" * 80)
    
    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    collection = client.get_collection("rackspace_knowledge")
    embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    test_queries = [
        "cloud migration services",
        "AWS managed services",
        "healthcare cyber resilience"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        query_embedding = embedding_model.encode([query])[0]
        
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=3
        )
        
        for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
            print(f"\n   Result {i}:")
            print(f"   URL: {meta['url']}")
            print(f"   Content: {doc[:150]}...")


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("STARTING RAG SYSTEM REBUILD")
    print("="*80)
    
    # Step 1: Crawl clean data
    data = crawl_urls(HIGH_VALUE_URLS)
    
    if not data:
        print("\n❌ No data collected! Please check URLs and network connection.")
        return
    
    # Save data
    save_data(data)
    
    # Step 2: Build vector DB
    build_vector_db(data)
    
    # Step 3: Test retrieval
    test_retrieval()
    
    print("\n" + "="*80)
    print("✅ RAG SYSTEM REBUILD COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("1. Restart Streamlit: streamlit run streamlit_app.py")
    print("2. Test with queries about cloud migration and healthcare")
    print("3. Verify responses use actual content (no more hallucinations!)")


if __name__ == "__main__":
    main()
