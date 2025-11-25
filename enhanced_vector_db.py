"""
Enhanced Vector Database Builder
This script:
1. Uses the enhanced collected data (filtered content)
2. Incorporates training Q&A pairs for better retrieval
3. Creates a high-quality vector database
4. Adds metadata for better context
"""

import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import re

from config import (
    DATA_DIR, VECTOR_DB_DIR, EMBEDDING_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP
)


class EnhancedVectorDBManager:
    """Enhanced vector database with training data integration"""
    
    def __init__(self):
        print("🔧 Initializing Enhanced Vector Database Manager...")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        print(f"📦 Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Get or create collection
        try:
            self.client.delete_collection("rackspace_knowledge")
            print("🗑️  Deleted old collection")
        except:
            pass
        
        self.collection = self.client.create_collection(
            name="rackspace_knowledge",
            metadata={"description": "Enhanced Rackspace knowledge base with training data"}
        )
        
        print("✅ Vector database initialized")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)]', '', text)
        return text.strip()
    
    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk) > 100:  # Only keep substantial chunks
                chunks.append(chunk)
        
        return chunks
    
    def load_documents(self) -> List[Dict]:
        """Load enhanced crawled documents"""
        doc_file = DATA_DIR / 'rackspace_knowledge.json'
        
        if not doc_file.exists():
            print(f"❌ Document file not found: {doc_file}")
            print("⚠️  Please run enhanced_data_collection.py first!")
            return []
        
        with open(doc_file, 'r', encoding='utf-8') as f:
            documents = json.load(f)
        
        print(f"📄 Loaded {len(documents)} documents")
        return documents
    
    def load_training_data(self) -> List[Dict]:
        """Load training Q&A pairs"""
        qa_file = DATA_DIR / 'training_qa_pairs.json'
        
        if not qa_file.exists():
            print(f"⚠️  Training Q&A file not found: {qa_file}")
            return []
        
        with open(qa_file, 'r', encoding='utf-8') as f:
            qa_pairs = json.load(f)
        
        print(f"📚 Loaded {len(qa_pairs)} training Q&A pairs")
        return qa_pairs
    
    def build_database(self):
        """Build enhanced vector database with both documents and training data"""
        print("\n" + "="*80)
        print("🚀 BUILDING ENHANCED VECTOR DATABASE")
        print("="*80)
        
        # Load data
        documents = self.load_documents()
        qa_pairs = self.load_training_data()
        
        if not documents:
            print("❌ No documents to index!")
            return
        
        all_chunks = []
        all_metadatas = []
        all_ids = []
        chunk_id = 0
        
        # Phase 1: Index document chunks
        print("\n📍 Phase 1: Indexing document chunks...")
        for doc_idx, doc in enumerate(documents):
            content = doc.get('content', '')
            
            if not content or len(content) < 100:
                continue
            
            # Clean and chunk
            cleaned_content = self.clean_text(content)
            chunks = self.chunk_text(cleaned_content)
            
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadatas.append({
                    'source': 'document',
                    'url': doc.get('url', 'unknown'),
                    'title': doc.get('title', 'Untitled'),
                    'type': 'content'
                })
                all_ids.append(f"doc_{chunk_id}")
                chunk_id += 1
            
            if (doc_idx + 1) % 50 == 0:
                print(f"   Processed {doc_idx + 1}/{len(documents)} documents...")
        
        print(f"✅ Created {len(all_chunks)} chunks from documents")
        
        # Phase 2: Index training Q&A pairs
        print("\n📍 Phase 2: Indexing training Q&A pairs...")
        qa_added = 0
        
        for qa in qa_pairs:
            # Support both formats: 'question'/'answer' and 'instruction'/'output'
            question = qa.get('question', qa.get('instruction', ''))
            answer = qa.get('answer', qa.get('output', ''))
            context = qa.get('context', '')
            
            if not question or not answer:
                continue
            
            # Add Q&A pair as searchable content
            # Format: "Q: question\nA: answer"
            qa_text = f"Question: {question}\n\nAnswer: {answer}"
            
            # Clean
            qa_text = self.clean_text(qa_text)
            
            # Only add if substantial
            if len(qa_text) > 100:
                all_chunks.append(qa_text)
                all_metadatas.append({
                    'source': 'training_qa',
                    'question': question,
                    'type': 'qa_pair'
                })
                all_ids.append(f"qa_{qa_added}")
                qa_added += 1
            
            # Also add context if available and different
            if context and len(context) > 100:
                context_cleaned = self.clean_text(context)
                # Chunk context if too long
                context_chunks = self.chunk_text(context_cleaned)
                
                for ctx_chunk in context_chunks[:2]:  # Max 2 chunks per context
                    all_chunks.append(ctx_chunk)
                    all_metadatas.append({
                        'source': 'training_context',
                        'question': question,
                        'type': 'context'
                    })
                    all_ids.append(f"ctx_{chunk_id}")
                    chunk_id += 1
        
        print(f"✅ Added {qa_added} Q&A pairs to index")
        
        # Phase 3: Generate embeddings and add to ChromaDB
        print(f"\n📍 Phase 3: Generating embeddings for {len(all_chunks)} chunks...")
        
        # Add in batches to avoid memory issues
        batch_size = 100
        total_added = 0
        
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i:i + batch_size]
            batch_metadatas = all_metadatas[i:i + batch_size]
            batch_ids = all_ids[i:i + batch_size]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(
                batch_chunks,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=batch_chunks,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            
            total_added += len(batch_chunks)
            print(f"   Added {total_added}/{len(all_chunks)} chunks...")
        
        # Final statistics
        print("\n" + "="*80)
        print("✅ VECTOR DATABASE BUILD COMPLETE!")
        print("="*80)
        print(f"📊 Total chunks indexed: {len(all_chunks)}")
        print(f"   - Document chunks: {len([m for m in all_metadatas if m['source'] == 'document'])}")
        print(f"   - Q&A pairs: {len([m for m in all_metadatas if m['source'] == 'training_qa'])}")
        print(f"   - Training contexts: {len([m for m in all_metadatas if m['source'] == 'training_context'])}")
        print(f"💾 Database location: {VECTOR_DB_DIR}")
        print("="*80)
    
    def test_search(self, query: str, top_k: int = 5):
        """Test the vector database with a query"""
        print(f"\n🔍 Testing search: '{query}'")
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        print(f"\n📋 Top {top_k} results:")
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            print(f"\n{i+1}. Source: {metadata.get('source', 'unknown')}")
            print(f"   Type: {metadata.get('type', 'unknown')}")
            if 'url' in metadata:
                print(f"   URL: {metadata['url']}")
            if 'question' in metadata:
                print(f"   Question: {metadata['question']}")
            print(f"   Content: {doc[:200]}...")


def main():
    """Main execution"""
    manager = EnhancedVectorDBManager()
    manager.build_database()
    
    # Test with sample query
    print("\n" + "="*80)
    print("🧪 TESTING DATABASE")
    print("="*80)
    manager.test_search("What are Rackspace's cloud adoption and migration services?")
    manager.test_search("How do I deploy applications on AWS with Rackspace?")


if __name__ == "__main__":
    main()
