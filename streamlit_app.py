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
    if "mode" not in st.session_state:
        st.session_state.mode = "extract"  # Default to extraction mode


def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Rackspace Knowledge Assistant",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for professional, calm theme
    st.markdown("""
        <style>
        /* Overall app background - soft warm white */
        .stApp {
            background-color: #fafafa;
        }
        
        /* Main container background */
        .main {
            background-color: #fafafa;
        }
        
        /* Hide sidebar */
        [data-testid="stSidebar"] {
            display: none;
        }
        
        /* Main header styling - elegant navy */
        .main-header {
            text-align: center;
            padding: 1.5rem 0;
            border-bottom: 2px solid #e8e8e8;
            margin-bottom: 2rem;
            background-color: #ffffff;
        }
        .main-header h1 {
            color: #1a365d;
            font-size: 2rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }
        
        /* Section headers - professional navy */
        h3 {
            color: #2d3748 !important;
            font-weight: 600 !important;
        }
        
        /* Chat messages - crisp white cards */
        .stChatMessage {
            background-color: #ffffff;
            border: 1px solid #e8e8e8;
            border-radius: 10px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        /* User message - subtle blue accent */
        .stChatMessage[data-testid="user-message"] {
            background-color: #f7fafc;
            border-left: 4px solid #4299e1;
            border-right: 1px solid #e8e8e8;
            border-top: 1px solid #e8e8e8;
            border-bottom: 1px solid #e8e8e8;
        }
        
        /* Assistant message - clean white */
        .stChatMessage[data-testid="assistant-message"] {
            background-color: #ffffff;
            border: 1px solid #e8e8e8;
        }
        
        /* Text color - professional dark gray */
        .stChatMessage p {
            color: #2d3748 !important;
            line-height: 1.7;
            font-size: 0.95rem;
        }
        
        /* List items in chat messages */
        .stChatMessage ul, .stChatMessage ol {
            color: #2d3748 !important;
        }
        
        .stChatMessage li {
            color: #2d3748 !important;
            margin-bottom: 0.4rem;
        }
        
        /* Links in chat messages - professional blue */
        .stChatMessage a {
            color: #3182ce !important;
            text-decoration: none !important;
            border-bottom: 1px solid #bee3f8;
        }
        
        .stChatMessage a:hover {
            color: #2c5282 !important;
            border-bottom-color: #3182ce;
        }
        
        /* All text elements in chat */
        .stChatMessage * {
            color: #2d3748 !important;
        }
        
        /* Override for links */
        .stChatMessage a, .stChatMessage a * {
            color: #3182ce !important;
        }
        
        /* Input box - clean and professional */
        .stChatInputContainer {
            border-top: 2px solid #e8e8e8;
            padding-top: 1rem;
            background-color: #fafafa;
        }
        
        /* Input text color */
        .stChatInputContainer input {
            color: #2d3748 !important;
            background-color: #ffffff !important;
            border-color: #cbd5e0 !important;
        }
        
        .stChatInputContainer input:focus {
            border-color: #4299e1 !important;
            box-shadow: 0 0 0 1px #4299e1 !important;
        }
        
        /* Primary button (selected) - professional blue */
        button[kind="primary"] {
            background-color: #3182ce !important;
            color: #ffffff !important;
            border: 2px solid #3182ce !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }
        
        button[kind="primary"]:hover {
            background-color: #2c5282 !important;
            border-color: #2c5282 !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(49, 130, 206, 0.3) !important;
        }
        
        /* Secondary button (unselected) - subtle gray */
        button[kind="secondary"] {
            background-color: #ffffff !important;
            color: #4a5568 !important;
            border: 2px solid #e2e8f0 !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }
        
        button[kind="secondary"]:hover {
            background-color: #f7fafc !important;
            border-color: #cbd5e0 !important;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* All button text should be visible */
        button p {
            color: inherit !important;
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
    
    # Mode selection (above chat)
    st.markdown("### Answer Mode")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 Extraction Mode", 
                    type="primary" if st.session_state.mode == "extract" else "secondary",
                    use_container_width=True):
            st.session_state.mode = "extract"
            st.rerun()
    
    with col2:
        if st.button("📝 Summarization Mode", 
                    type="primary" if st.session_state.mode == "summarize" else "secondary",
                    use_container_width=True):
            st.session_state.mode = "summarize"
            st.rerun()
    
    st.markdown("---")
    
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
        
        # Get bot response with selected mode
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                try:
                    # Pass the mode parameter to the chat method
                    response = st.session_state.chatbot.chat(prompt, mode=st.session_state.mode)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    main()
