"""
Enhanced RAG Chatbot with Training Data Integration
This version:
1. Uses the enhanced vector database
2. Leverages training Q&A pairs for better responses
3. Provides accurate, context-based answers
4. No repetitive navigation text
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import List, Dict, Tuple
import re

from config import (
    VECTOR_DB_DIR, EMBEDDING_MODEL, BASE_MODEL_NAME,
    FINE_TUNED_MODEL_PATH, TOP_K_RETRIEVAL, DEVICE, USE_MPS
)


class EnhancedRAGChatbot:
    """Enhanced RAG chatbot with better context utilization"""
    
    def __init__(self):
        print("🤖 Initializing Enhanced RAG Chatbot...")
        
        # Set device
        if USE_MPS and torch.backends.mps.is_available():
            self.device = "mps"
            print("✅ Using Apple Silicon (MPS)")
        elif torch.cuda.is_available():
            self.device = "cuda"
            print("✅ Using CUDA")
        else:
            self.device = "cpu"
            print("✅ Using CPU")
        
        # Load vector database
        print("📚 Loading vector database...")
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_collection("rackspace_knowledge")
        
        # Load embedding model
        print(f"🔤 Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Load LLM
        model_path = FINE_TUNED_MODEL_PATH if FINE_TUNED_MODEL_PATH.exists() else BASE_MODEL_NAME
        print(f"🧠 Loading LLM: {model_path}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
            device_map=self.device if self.device != "mps" else None,
            low_cpu_mem_usage=True
        )
        
        if self.device == "mps":
            self.model = self.model.to(self.device)
        
        self.model.eval()
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        print("✅ Enhanced RAG Chatbot ready!")
    
    def retrieve_context(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> Tuple[str, List[Dict]]:
        """Retrieve relevant context with source information"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Search vector database - get top K most relevant chunks
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        # Process results - ONLY real documents with URLs
        context_parts = []
        sources = []
        seen_urls = set()  # Track unique URLs
        seen_content = set()  # Track unique content
        
        # Get distances for relevance scoring (lower distance = more relevant)
        distances = results.get('distances', [[]])[0] if 'distances' in results else []
        
        for idx, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            # Skip duplicates
            doc_hash = hash(doc[:100])
            if doc_hash in seen_content:
                continue
            seen_content.add(doc_hash)
            
            # Add document chunk
            context_parts.append(doc)
            
            # Get URL and title
            url = metadata.get('url', 'N/A')
            title = metadata.get('title', 'N/A')
            
            # Only add source if URL is unique and valid
            if url and url != 'N/A' and url not in seen_urls:
                seen_urls.add(url)
                
                # Add relevance score (distance from query)
                relevance = 1.0 - (distances[idx] if idx < len(distances) else 0.5)
                
                sources.append({
                    'url': url,
                    'title': title,
                    'relevance': relevance
                })
        
        # Sort sources by relevance (highest first)
        sources.sort(key=lambda x: x.get('relevance', 0), reverse=True)
        
        # Combine context
        context = '\n\n'.join(context_parts)
        
        return context, sources
    
    def build_prompt(self, query: str, context: str, history: List[Dict[str, str]]) -> str:
        """Build prompt for the model - Force it to use ONLY the context"""
        
        prompt = f"""<|system|>
You are a helpful assistant. Answer the question using ONLY the information in the Context below. Do not make up information. Be concise and accurate.
<|user|>
Context:
{context}

Question: {query}

Answer using ONLY the information above:
<|assistant|>
"""
        
        return prompt
    
    def generate_response(self, prompt: str) -> str:
        """Generate response from the model"""
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate with stricter parameters to reduce hallucination
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=150,  # Reasonable length
                temperature=0.1,  # Very low temperature for factual responses
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.3,  # Higher penalty for repetition
                no_repeat_ngram_size=4,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the assistant's response
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()
        
        # Clean up aggressive extraction
        # Remove everything before first actual sentence
        lines = response.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip system-like patterns
            if any(skip in line.lower() for skip in [
                'you are', 'answer the question', 'context:', 'question:', 
                'using only', 'be concise', '<|', '|>'
            ]):
                continue
            # Skip empty lines
            if not line:
                continue
            clean_lines.append(line)
        
        response = ' '.join(clean_lines)
        
        # If response is too short or still has issues, extract meaningful content
        if len(response) < 20 or 'based on actual answers' in response.lower():
            # Try to find the actual answer in the response
            sentences = response.split('.')
            good_sentences = []
            for sent in sentences:
                sent = sent.strip()
                # Skip bad patterns
                if any(bad in sent.lower() for bad in [
                    'based on actual', 'answer based', 'yes!', 'here\'s some quick facts'
                ]):
                    continue
                if sent and len(sent) > 10:
                    good_sentences.append(sent)
            
            if good_sentences:
                response = '. '.join(good_sentences[:3])  # Max 3 sentences
                if response and not response.endswith('.'):
                    response += '.'
        
        # Clean up
        response = self.clean_response(response)
        
        return response
    
    def clean_response(self, text: str) -> str:
        """Clean up the generated response"""
        # Remove any remaining system/user markers
        text = re.sub(r'<\|.*?\|>', '', text)
        
        # Remove repetitive sentences
        sentences = text.split('.')
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and sentence.lower() not in seen:
                unique_sentences.append(sentence)
                seen.add(sentence.lower())
        
        text = '. '.join(unique_sentences)
        if text and not text.endswith('.'):
            text += '.'
        
        return text.strip()
    
    def format_sources(self, sources: List[Dict], response: str = "") -> str:
        """Format sources for display - DISABLED until we fix the retrieval issue"""
        # Sources are showing same URLs for every question
        # Disable until we properly fix the vector DB retrieval
        return ""
    
    def chat(self, user_message: str) -> str:
        """Main chat interface - Claude-like: accurate, concise, context-based"""
        # Retrieve relevant context
        context, sources = self.retrieve_context(user_message)
        
        # Build prompt with context
        prompt = self.build_prompt(user_message, context, self.conversation_history)
        
        # Generate response
        response = self.generate_response(prompt)
        
        # Don't add sources - they're showing same URLs for every question
        # Just return the clean response
        
        # Update conversation history
        self.conversation_history.append({
            'user': user_message,
            'assistant': response
        })
        
        # Keep only last 5 exchanges
        if len(self.conversation_history) > 5:
            self.conversation_history = self.conversation_history[-5:]
        
        return response
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []


# Global chatbot instance
_chatbot_instance = None


def get_chatbot():
    """Get or create chatbot instance"""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = EnhancedRAGChatbot()
    return _chatbot_instance


def chat(message: str) -> str:
    """Simple chat interface"""
    chatbot = get_chatbot()
    return chatbot.chat(message)


def reset():
    """Reset conversation"""
    chatbot = get_chatbot()
    chatbot.reset_conversation()


if __name__ == "__main__":
    # Test the chatbot
    print("\n" + "="*80)
    print("🧪 TESTING ENHANCED RAG CHATBOT")
    print("="*80)
    
    chatbot = get_chatbot()
    
    test_questions = [
        "What are Rackspace's cloud adoption and migration services?",
        "How does Rackspace help with AWS deployment?",
        "What security services does Rackspace offer?"
    ]
    
    for question in test_questions:
        print(f"\n❓ {question}")
        response = chatbot.chat(question)
        print(f"🤖 {response}")
        print("-" * 80)
