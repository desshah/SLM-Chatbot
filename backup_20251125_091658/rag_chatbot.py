"""
RAG (Retrieval-Augmented Generation) pipeline with conversation history
Combines vector database retrieval with fine-tuned model generation
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Tuple, Dict
import logging
from pathlib import Path
from vector_db import VectorDBManager
from config import (
    FINE_TUNED_MODEL_PATH,
    BASE_MODEL_NAME,
    MAX_NEW_TOKENS,
    TEMPERATURE,
    TOP_P,
    DO_SAMPLE,
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
    """RAG-based chatbot with conversation history"""
    
    def __init__(self, model_path: Path = FINE_TUNED_MODEL_PATH, use_base_model: bool = False):
        self.device = self._setup_device()
        logger.info(f"Using device: {self.device}")
        
        # Load model and tokenizer
        if use_base_model or not model_path.exists():
            logger.warning(f"Fine-tuned model not found at {model_path}, using base model")
            model_path = BASE_MODEL_NAME
        
        self.load_model(model_path)
        
        # Initialize vector database
        logger.info("Initializing vector database...")
        self.vector_db = VectorDBManager()
        
        # Initialize conversation history
        self.conversation = ConversationHistory()
        
        logger.info("RAG Chatbot initialized successfully")
    
    def _setup_device(self):
        """Set up device for inference"""
        if torch.backends.mps.is_available():
            return torch.device("mps")
        elif torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")
    
    def load_model(self, model_path):
        """Load model and tokenizer"""
        logger.info(f"Loading model from {model_path}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if self.device.type != "cpu" else torch.float32,
            device_map=None,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        self.model = self.model.to(self.device)
        self.model.eval()
        
        logger.info("Model loaded successfully")
    
    def retrieve_context(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> str:
        """Retrieve relevant context from vector database"""
        results = self.vector_db.search(query, top_k=top_k)
        
        if not results:
            return ""
        
        # Combine retrieved documents
        context_parts = []
        for i, (doc, metadata, score) in enumerate(results, 1):
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
        """Generate response using the model"""
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=100,  # Shorter for more focused responses
                temperature=1.0,  # No temperature (deterministic)
                do_sample=False,  # Greedy decoding - most likely tokens
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                num_beams=1,  # No beam search
                repetition_penalty=1.2,  # Penalize repetition
                no_repeat_ngram_size=3  # Prevent repeating 3-grams
            )
        
        # Decode only the new tokens (response)
        response = self.tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        
        # Clean up response - remove repetitions
        response = response.strip()
        
        # Stop at first sentence if it's repeating
        sentences = response.split('.')
        if len(sentences) > 1:
            # Check if sentences are repeating
            seen = set()
            clean_sentences = []
            for sent in sentences:
                sent_clean = sent.strip().lower()
                if sent_clean and sent_clean not in seen and len(sent_clean) > 10:
                    seen.add(sent_clean)
                    clean_sentences.append(sent.strip())
            
            if clean_sentences:
                response = '. '.join(clean_sentences[:3])  # Max 3 sentences
                if not response.endswith('.'):
                    response += '.'
        
        return response.strip()
    
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
