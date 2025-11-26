"""
RAG (Retrieval-Augmented Generation) pipeline with Groq API
Combines vector database retrieval with Groq LLM generation
"""
from groq import Groq
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
import logging
from pathlib import Path
from config import (
    VECTOR_DB_DIR,
    EMBEDDING_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    MAX_NEW_TOKENS,
    TEMPERATURE,
    TOP_P,
    MAX_HISTORY_LENGTH,
    TOP_K_RETRIEVAL
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationHistory:
    """Manages conversation history for context-aware responses"""
    
    def __init__(self, max_length: int = MAX_HISTORY_LENGTH):
        self.max_length = max_length
        self.history = []
    
    def add_turn(self, user_message: str, bot_response: str):
        """Add a conversation turn"""
        self.history.append({
            'user': user_message,
            'assistant': bot_response
        })
        
        # Keep only last N turns
        if len(self.history) > self.max_length:
            self.history = self.history[-self.max_length:]
    
    def get_history_text(self) -> str:
        """Get formatted history for context"""
        if not self.history:
            return ""
        
        history_text = "Previous conversation:\n"
        for i, turn in enumerate(self.history, 1):
            history_text += f"User: {turn['user']}\n"
            history_text += f"Assistant: {turn['assistant']}\n"
        
        return history_text
    
    def get_last_user_message(self, n: int = 1) -> List[str]:
        """Get last n user messages"""
        return [turn['user'] for turn in self.history[-n:]]
    
    def clear(self):
        """Clear conversation history"""
        self.history = []
    
    def to_dict(self) -> List[Dict]:
        """Convert to dictionary format"""
        return self.history.copy()


class RAGChatbot:
    """RAG-based chatbot with Groq API"""
    
    def __init__(self):
        logger.info("🤖 Initializing RAG Chatbot with Groq...")
        
        # Initialize Groq client
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found! Please set it in .env file")
        
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.groq_model = GROQ_MODEL
        logger.info(f"✅ Using Groq model: {self.groq_model}")
        
        # Load vector database
        logger.info("📚 Loading vector database...")
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_collection("rackspace_knowledge")
        
        # Load embedding model
        logger.info(f"🔤 Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Initialize conversation history
        self.conversation = ConversationHistory()
        
        logger.info("✅ RAG Chatbot ready!")
    
    def retrieve_context(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> str:
        """Retrieve relevant context from vector database"""
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Search vector database
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        if not results or not results['documents'][0]:
            return ""
        
        # Combine retrieved documents
        context_parts = []
        for i, doc in enumerate(results['documents'][0], 1):
            context_parts.append(f"[Source {i}]: {doc}")
        
        context = "\n\n".join(context_parts)
        return context
    
    def build_prompt(self, user_message: str, context: str) -> str:
        """Build optimized prompt with history and context for accurate responses"""
        # Get conversation history
        history_text = self.conversation.get_history_text()
        
        # Enhanced prompt engineering for accuracy and user-friendliness
        prompt = "<|system|>\n"
        prompt += "You are a Rackspace Technology expert. Answer questions using ONLY the information provided in the context below.\n\n"
        prompt += "CRITICAL RULES:\n"
        prompt += "1. Use ONLY facts from the CONTEXT section below - do not make up information\n"
        prompt += "2. If the context doesn't contain the answer, say 'I don't have specific information about that in my knowledge base'\n"
        prompt += "3. Be direct and concise - answer in 2-4 sentences maximum\n"
        prompt += "4. Do not repeat phrases or generate lists unless they are in the context\n"
        prompt += "5. Quote specific facts from the context when possible\n\n"
        
        if context:
            prompt += f"CONTEXT (Your ONLY source of information):\n{context}\n\n"
        else:
            prompt += "CONTEXT: No relevant information found.\n\n"
        
        if history_text:
            prompt += f"PREVIOUS CONVERSATION:\n{history_text}\n"
        
        prompt += f"USER QUESTION: {user_message}\n\n"
        prompt += "<|assistant|>\n"
        
        return prompt
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Groq API"""
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Rackspace Technology expert. Answer questions using ONLY the information provided in the context. Be direct and concise - answer in 2-4 sentences maximum."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.groq_model,
                temperature=0.1,
                max_tokens=MAX_NEW_TOKENS,
                top_p=TOP_P,
            )
            
            response = chat_completion.choices[0].message.content
            return response.strip()
            
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return "I'm having trouble generating a response right now. Please try again."
    
    def chat(self, user_message: str) -> str:
        """Main chat function with RAG and history"""
        # Check if user is asking about conversation history
        history_keywords = ['what did i ask', 'what was my question', 'previous question', 
                           'earlier question', 'first question', 'asked before']
        
        if any(keyword in user_message.lower() for keyword in history_keywords):
            # Return from history
            if self.conversation.history:
                last_messages = self.conversation.get_last_user_message(n=len(self.conversation.history))
                if 'first' in user_message.lower():
                    return f"Your first question was: {last_messages[0]}"
                else:
                    return f"Your previous question was: {last_messages[-1]}"
            else:
                return "We haven't had any previous conversation yet."
        
        # Retrieve relevant context
        logger.info(f"User: {user_message}")
        context = self.retrieve_context(user_message)
        
        # If no context found, return helpful message
        if not context or len(context.strip()) < 50:
            response = "I don't have specific information about that in my Rackspace knowledge base. Could you try rephrasing your question or ask about Rackspace's services, mission, or cloud platforms?"
            self.conversation.add_turn(user_message, response)
            logger.info(f"Assistant: {response}")
            return response
        
        # Extract key sentences from context (extractive approach)
        # This is more reliable than generative for base models
        sentences = []
        for line in context.split('\n'):
            line = line.strip()
            if line and len(line) > 30 and not line.startswith('[Source'):
                # Clean up the line
                if ':' in line:
                    line = line.split(':', 1)[1].strip()
                sentences.append(line)
        
        # Take first 2-3 most relevant sentences
        if sentences:
            response = ' '.join(sentences[:3])
            # Clean up
            if len(response) > 400:
                response = response[:400] + '...'
        else:
            # Fallback to generation if extraction fails
            prompt = self.build_prompt(user_message, context)
            response = self.generate_response(prompt)
        
        logger.info(f"Assistant: {response}")
        
        # Add to conversation history
        self.conversation.add_turn(user_message, response)
        
        return response
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation.clear()
        logger.info("Conversation history cleared")
    
    def get_conversation_history(self) -> List[Dict]:
        """Get current conversation history"""
        return self.conversation.to_dict()


def main():
    """Test the RAG chatbot"""
    # Initialize chatbot (will use base model if fine-tuned not available)
    chatbot = RAGChatbot(use_base_model=False)
    
    # Test conversation with history
    test_queries = [
        "What is Rackspace?",
        "What is their mission?",
        "What did I ask first?"
    ]
    
    print(f"\n{'='*80}")
    print("Testing RAG Chatbot with Conversation History")
    print(f"{'='*80}\n")
    
    for query in test_queries:
        print(f"User: {query}")
        response = chatbot.chat(query)
        print(f"Bot: {response}\n")
        print("-" * 80 + "\n")
    
    # Show conversation history
    print("\nConversation History:")
    print(f"{'='*80}")
    history = chatbot.get_conversation_history()
    for i, turn in enumerate(history, 1):
        print(f"\nTurn {i}:")
        print(f"  User: {turn['user']}")
        print(f"  Assistant: {turn['assistant']}")


if __name__ == "__main__":
    main()
