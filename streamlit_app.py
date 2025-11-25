"""
Streamlit UI for Rackspace Knowledge Chatbot
Beautiful, simple chat interface with conversation history
"""
import streamlit as st
from rag_chatbot import RAGChatbot
import logging
from pathlib import Path
from config import FINE_TUNED_MODEL_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@st.cache_resource
def load_chatbot():
    """Load chatbot once and cache it"""
    try:
        logger.info("Initializing chatbot...")
        # Try to use fine-tuned model, fallback to base model if not available
        use_base = not FINE_TUNED_MODEL_PATH.exists()
        if use_base:
            st.info("🤖 Using base TinyLlama model (fine-tuned model not found)")
        else:
            st.success("🎯 Using fine-tuned Rackspace model")
        
        chatbot = RAGChatbot(use_base_model=use_base)
        logger.info("Chatbot initialized successfully")
        return chatbot
    except Exception as e:
        logger.error(f"Error initializing chatbot: {e}")
        st.error(f"❌ Failed to initialize chatbot: {e}")
        return None


def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None


def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Rackspace Knowledge Chatbot",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .stChatMessage {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        /* Make all text black and readable */
        .stChatMessage p, .stChatMessage div {
            color: #000000 !important;
        }
        /* User message styling */
        .stChatMessage[data-testid="user-message"] {
            background-color: #e3f2fd !important;
        }
        .stChatMessage[data-testid="user-message"] p {
            color: #000000 !important;
            font-weight: 500;
        }
        /* Assistant message styling */
        .stChatMessage[data-testid="assistant-message"] {
            background-color: #f5f5f5 !important;
        }
        .stChatMessage[data-testid="assistant-message"] p {
            color: #000000 !important;
        }
        /* Ensure markdown text is black */
        .element-container p, .stMarkdown p {
            color: #000000 !important;
        }
        .example-card {
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 5px;
            color: #000000 !important;
        }
        /* Sidebar text */
        .css-1d391kg p {
            color: #000000 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>🚀 Rackspace Knowledge Chatbot</h1>
            <p>Ask me anything about Rackspace Technology!</p>
            <p style="font-size: 0.9em; margin-top: 10px;">
                Powered by Fine-Tuned LLM + RAG System | Built with YOUR OWN Model (No Agents!)
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📖 About")
        st.markdown("""
        ### Welcome! 👋
        
        I'm your Rackspace knowledge assistant. I can help you with:
        
        - 📖 Information about Rackspace Technology
        - 🎯 Mission, vision, and services
        - 🌟 Fanatical Experience
        - ☁️ Cloud platforms & partnerships
        - 📜 Company history
        
        **I remember our conversation!** Ask follow-up questions anytime.
        """)
        
        st.markdown("---")
        
        st.header("💡 Example Questions")
        examples = [
            "What is Rackspace?",
            "Tell me about Rackspace's mission",
            "What services does Rackspace offer?",
            "What is Fanatical Experience?",
            "When was Rackspace founded?",
            "Who are Rackspace's cloud partners?",
            "What did I ask first?"
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{example}", use_container_width=True):
                # Add example to chat
                st.session_state.messages.append({"role": "user", "content": example})
                st.rerun()
        
        st.markdown("---")
        
        # Clear conversation button
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            if st.session_state.chatbot:
                st.session_state.chatbot.reset_conversation()
            st.success("Conversation cleared!")
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("""
        ### 🔧 System Info
        - **Model**: TinyLlama-1.1B-Chat
        - **Vector DB**: ChromaDB
        - **Embeddings**: MiniLM-L6-v2
        - **Documents**: 429 pages
        - **Training Examples**: 4,107
        - **Device**: Apple M3 (MPS)
        """)
    
    # Load chatbot (cached)
    if st.session_state.chatbot is None:
        with st.spinner("🤖 Initializing chatbot... (first time may take 1-2 minutes)"):
            st.session_state.chatbot = load_chatbot()
    
    if st.session_state.chatbot is None:
        st.error("❌ Failed to load chatbot. Please check the logs.")
        st.stop()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your question here..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get bot response with loading indicator
        with st.chat_message("assistant"):
            # Show loading spinner with custom message
            with st.spinner("🤔 Searching knowledge base and generating response..."):
                try:
                    response = st.session_state.chatbot.chat(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.9em;">
            <p>💡 <strong>Tip:</strong> You can ask about previous questions! Try: "What did I ask first?"</p>
            <p>🔓 <strong>100% Open Source</strong> • NO AGENTS • YOUR MODEL • YOUR DATA</p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
