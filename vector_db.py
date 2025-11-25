"""
Vector database manager for RAG system using ChromaDB
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import json
from typing import List, Dict, Tuple
import logging
from pathlib import Path
from config import (
    VECTOR_DB_DIR, 
    EMBEDDING_MODEL, 
    COLLECTION_NAME, 
    CHUNK_SIZE, 
    CHUNK_OVERLAP,
    TOP_K_RETRIEVAL
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorDBManager:
    """Manages vector database for RAG retrieval"""
    
    def __init__(self, db_path: Path = VECTOR_DB_DIR):
        self.db_path = db_path
        self.db_path.mkdir(exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Rackspace knowledge base"}
        )
        
        logger.info(f"Vector database initialized at {self.db_path}")
    
    def chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, 
                   overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk) > 50:  # Only add substantial chunks
                chunks.append(chunk)
        
        return chunks
    
    def add_documents(self, documents: List[Dict]):
        """Add documents to vector database"""
        logger.info(f"Adding {len(documents)} documents to vector database...")
        
        all_chunks = []
        all_metadatas = []
        all_ids = []
        
        doc_count = 0
        for doc in documents:
            # Chunk the document
            chunks = self.chunk_text(doc['content'])
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"doc_{doc_count}_chunk_{i}"
                all_chunks.append(chunk)
                all_metadatas.append({
                    'title': doc['title'],
                    'source': doc.get('source', 'unknown'),
                    'url': doc.get('url', 'N/A'),
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                })
                all_ids.append(chunk_id)
            
            doc_count += 1
        
        # Add to collection in batches
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i:i + batch_size]
            batch_metadata = all_metadatas[i:i + batch_size]
            batch_ids = all_ids[i:i + batch_size]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(
                batch_chunks, 
                show_progress_bar=False,
                convert_to_tensor=False
            ).tolist()
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=batch_chunks,
                metadatas=batch_metadata,
                ids=batch_ids
            )
            
            logger.info(f"Added batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")
        
        logger.info(f"Successfully added {len(all_chunks)} chunks to vector database")
    
    def search(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> List[Tuple[str, Dict, float]]:
        """Search for relevant documents"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode(
            query, 
            show_progress_bar=False,
            convert_to_tensor=False
        ).tolist()
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        
        # Format results
        retrieved_docs = []
        if results['documents']:
            for doc, metadata, distance in zip(
                results['documents'][0], 
                results['metadatas'][0], 
                results['distances'][0]
            ):
                # Convert distance to similarity score (lower distance = higher similarity)
                similarity = 1 / (1 + distance)
                retrieved_docs.append((doc, metadata, similarity))
        
        return retrieved_docs
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        count = self.collection.count()
        return {
            'total_chunks': count,
            'collection_name': COLLECTION_NAME,
            'embedding_model': EMBEDDING_MODEL
        }


def build_vector_db_from_json(json_path: Path):
    """Build vector database from collected JSON data"""
    logger.info(f"Building vector database from {json_path}")
    
    # Load data
    with open(json_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    logger.info(f"Loaded {len(documents)} documents")
    
    # Initialize vector DB
    db_manager = VectorDBManager()
    
    # Add documents
    db_manager.add_documents(documents)
    
    # Print stats
    stats = db_manager.get_stats()
    print(f"\n{'='*80}")
    print(f"Vector database built successfully!")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Embedding model: {stats['embedding_model']}")
    print(f"{'='*80}\n")
    
    return db_manager


def main():
    """Main workflow to build vector database"""
    from config import DATA_DIR
    
    json_path = DATA_DIR / "rackspace_knowledge.json"
    
    if not json_path.exists():
        logger.error(f"Data file not found: {json_path}")
        logger.error("Please run data_collection.py first!")
        return
    
    db_manager = build_vector_db_from_json(json_path)
    
    # Test retrieval
    print("\nTesting retrieval with sample query...")
    test_query = "What is Rackspace?"
    results = db_manager.search(test_query, top_k=3)
    
    print(f"\nQuery: {test_query}")
    print(f"Found {len(results)} relevant documents:\n")
    
    for i, (doc, metadata, score) in enumerate(results, 1):
        print(f"{i}. Title: {metadata['title']}")
        print(f"   Similarity: {score:.4f}")
        print(f"   Content preview: {doc[:200]}...")
        print()


if __name__ == "__main__":
    main()
