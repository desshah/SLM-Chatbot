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
            n_results=top_k
        )
        
        # Process results - ONLY real documents with URLs
        context_parts = []
        sources = []
        seen_content = set()
        
        for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
            # Skip duplicates
            doc_hash = hash(doc[:100])
            if doc_hash in seen_content:
                continue
            seen_content.add(doc_hash)
            
            # Add document chunk
            context_parts.append(doc)
            
            # Add source (ACTUAL URL!)
            sources.append({
                'url': metadata.get('url', 'N/A'),
                'title': metadata.get('title', 'N/A')
            })
        
        # Combine context
        context = '\n\n'.join(context_parts)
        
        return context, sources
    
    def build_prompt(self, query: str, context: str, history: List[Dict[str, str]]) -> str:
        """Build prompt for the model - Claude-like: concise, accurate, context-based"""
        
        prompt = f"""<|system|>
You are a Rackspace support assistant. Answer the question concisely using ONLY the context provided. Keep responses brief (2-3 sentences). If the context doesn't contain the answer, say "I don't have information about that."
<|user|>
Context:
{context}

Question: {query}
<|assistant|>
"""
        
        return prompt
    
    def generate_response(self, prompt: str) -> str:
        """Generate response from the model"""
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate - Claude-like: concise and accurate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=100,  # SHORT: Force concise answers (2-3 sentences)
                temperature=0.3,
                do_sample=True,
                top_p=0.85,
                repetition_penalty=1.2,
                no_repeat_ngram_size=3,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the assistant's response
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()
        
        # Remove system prompt leakage
        lines = response.split('\n')
        clean_lines = []
        skip_system = False
        
        for line in lines:
            line = line.strip()
            # Skip system prompt patterns
            if any(pattern in line.lower() for pattern in [
                'you are a', 'rackspace support assistant', 
                'answer the question', 'context:', 'question:'
            ]):
                skip_system = True
                continue
            if skip_system and not line:
                continue
            if line:
                skip_system = False
                clean_lines.append(line)
        
        response = ' '.join(clean_lines)
        
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
        """Format sources for display - Add 'Learn more' only if helpful"""
        if not sources:
            return ""
        
        source_text = "\n\n📚 **Sources:**\n"
        
        # Show unique URLs only
        seen_urls = set()
        count = 1
        first_url = None
        
        for source in sources:
            url = source.get('url', '')
            if url and url != 'N/A' and url not in seen_urls:
                if count == 1:
                    first_url = url
                seen_urls.add(url)
                source_text += f"{count}. {url}\n"
                count += 1
                if count > 3:  # Max 3 sources
                    break
        
        # Add "Learn more" ONLY if response seems complete and informative
        # (Not for "I don't have information" responses)
        if first_url and response and len(response) > 50:
            if "don't have" not in response.lower() and "no information" not in response.lower():
                source_text += f"\n💡 **Learn more:** {first_url}\n"
        
        return source_text
    
    def chat(self, user_message: str) -> str:
        """Main chat interface - Claude-like: accurate, concise, context-based"""
        # Retrieve relevant context
        context, sources = self.retrieve_context(user_message)
        
        # Build prompt with context
        prompt = self.build_prompt(user_message, context, self.conversation_history)
        
        # Generate response
        response = self.generate_response(prompt)
        
        # Add sources with conditional "Learn more"
        response_with_sources = response + self.format_sources(sources, response)
        
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
