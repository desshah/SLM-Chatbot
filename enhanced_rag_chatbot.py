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
        
        # Search vector database
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k * 2  # Get more to filter
        )
        
        # Process and filter results
        context_parts = []
        sources = []
        seen_content = set()
        
        for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
            # Skip duplicates
            doc_hash = hash(doc[:100])
            if doc_hash in seen_content:
                continue
            seen_content.add(doc_hash)
            
            # Prioritize Q&A pairs
            if metadata.get('source') == 'training_qa':
                context_parts.insert(0, doc)  # Add at beginning
                sources.insert(0, {
                    'type': 'Q&A',
                    'question': metadata.get('question', 'N/A')
                })
            else:
                context_parts.append(doc)
                sources.append({
                    'type': 'Document',
                    'url': metadata.get('url', 'N/A'),
                    'title': metadata.get('title', 'N/A')
                })
            
            # Limit to top_k after filtering
            if len(context_parts) >= top_k:
                break
        
        # Combine context
        context = '\n\n'.join(context_parts)
        
        return context, sources
    
    def build_prompt(self, query: str, context: str, history: List[Dict[str, str]]) -> str:
        """Build prompt for the model"""
        # Include recent conversation history (last 2 exchanges)
        history_text = ""
        if history:
            recent_history = history[-2:]
            for exchange in recent_history:
                history_text += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"
        
        prompt = f"""<|system|>
You are a helpful Rackspace technical support assistant. Use the provided context to answer questions accurately and concisely.

Rules:
1. Answer ONLY using information from the context provided
2. If the context contains a Q&A pair that matches the question, use that answer
3. Be specific and technical when appropriate
4. If the context doesn't contain the answer, say "I don't have specific information about that in my knowledge base"
5. Never make up information
6. Be concise but complete

<|user|>
{history_text}Context:
{context}

Question: {query}

<|assistant|>"""
        
        return prompt
    
    def generate_response(self, prompt: str) -> str:
        """Generate response from the model"""
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.3,
                no_repeat_ngram_size=4,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the assistant's response
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()
        
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
    
    def format_sources(self, sources: List[Dict]) -> str:
        """Format sources for display"""
        if not sources:
            return ""
        
        source_text = "\n\n📚 **Sources:**\n"
        for i, source in enumerate(sources[:3], 1):  # Show top 3 sources
            if source['type'] == 'Q&A':
                source_text += f"{i}. Training Q&A: {source['question']}\n"
            else:
                source_text += f"{i}. {source['title']}: {source['url']}\n"
        
        return source_text
    
    def chat(self, user_message: str) -> str:
        """Main chat interface"""
        # Retrieve relevant context
        context, sources = self.retrieve_context(user_message)
        
        # Build prompt with history
        prompt = self.build_prompt(user_message, context, self.conversation_history)
        
        # Generate response
        response = self.generate_response(prompt)
        
        # Add sources
        response_with_sources = response + self.format_sources(sources)
        
        # Update conversation history
        self.conversation_history.append({
            'user': user_message,
            'assistant': response
        })
        
        # Keep only last 5 exchanges
        if len(self.conversation_history) > 5:
            self.conversation_history = self.conversation_history[-5:]
        
        return response_with_sources
    
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
