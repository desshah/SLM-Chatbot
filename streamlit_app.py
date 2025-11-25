"""
Streamlit UI for Rackspace Knowledge Chatbot
Beautiful, simple chat interface with conversation history
"""
import streamlit as st
# Use enhanced chatbot with better RAG and training data integration
try:
    from enhanced_rag_chatbot import get_chatbot
    USING_ENHANCED = True
except ImportError:
    from rag_chatbot import RAGChatbot
    USING_ENHANCED = False
    
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
        
        if USING_ENHANCED:
            # Use enhanced chatbot (simpler interface)
            logger.info("✅ Using Enhanced RAG Chatbot")
            chatbot = get_chatbot()
            return chatbot
        else:
            # Fallback to original
            logger.info("⚠️  Using original RAG Chatbot (enhanced not available)")
            use_base = not FINE_TUNED_MODEL_PATH.exists()
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
        page_title="Rackspace Knowledge Assistant",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for minimal, clean design
    st.markdown("""
        <style>
        /* Hide sidebar */
        [data-testid="stSidebar"] {
            display: none;
        }
        
        /* Main header styling */
        .main-header {
            text-align: center;
            padding: 1.5rem 0;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 2rem;
        }
        .main-header h1 {
            color: #1f1f1f;
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        /* Chat messages */
        .stChatMessage {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        /* User message */
        .stChatMessage[data-testid="user-message"] {
            background-color: #e3f2fd;
            border-color: #2196f3;
        }
        
        /* Assistant message */
        .stChatMessage[data-testid="assistant-message"] {
            background-color: #f5f5f5;
            border-color: #bdbdbd;
        }
        
        /* Text color */
        .stChatMessage p {
            color: #1f1f1f !important;
            line-height: 1.6;
        }
        
        /* Input box */
        .stChatInputContainer {
            border-top: 2px solid #e0e0e0;
            padding-top: 1rem;
        }
        
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Simple header
    st.markdown("""
        <div class="main-header">
            <h1>🤖 Rackspace Knowledge Assistant</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Load chatbot (cached)
    if st.session_state.chatbot is None:
        with st.spinner("🤖 Initializing chatbot..."):
            st.session_state.chatbot = load_chatbot()
    
    if st.session_state.chatbot is None:
        st.error("❌ Failed to load chatbot. Please check the logs.")
        st.stop()
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💼" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message..."):
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑‍💼"):
            st.markdown(prompt)
        
        # Get bot response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.chatbot.chat(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    main()
