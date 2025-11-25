"""
Gradio UI for Rackspace Knowledge Chatbot
User-friendly chat interface with conversation history
"""
import gradio as gr
from rag_chatbot import RAGChatbot
import logging
from pathlib import Path
from config import FINE_TUNED_MODEL_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global chatbot instance
chatbot = None


def initialize_chatbot():
    """Initialize the chatbot"""
    global chatbot
    try:
        logger.info("Initializing chatbot...")
        # Try to use fine-tuned model, fallback to base model if not available
        use_base = not FINE_TUNED_MODEL_PATH.exists()
        chatbot = RAGChatbot(use_base_model=use_base)
        logger.info("Chatbot initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing chatbot: {e}")
        return False


def chat_interface(message, history):
    """
    Chat interface function for Gradio
    
    Args:
        message: User's message
        history: Chat history in Gradio format [[user_msg, bot_msg], ...]
    
    Returns:
        Response text
    """
    global chatbot
    
    if chatbot is None:
        return "Error: Chatbot not initialized. Please restart the application."
    
    try:
        # Get response from chatbot
        response = chatbot.chat(message)
        return response
    
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return f"Sorry, I encountered an error: {str(e)}"


def clear_conversation():
    """Clear conversation history"""
    global chatbot
    if chatbot:
        chatbot.reset_conversation()
    return None  # Clear the chat in Gradio


def create_ui():
    """Create Gradio interface"""
    
    # Custom CSS for better appearance
    custom_css = """
    .container {
        max-width: 900px;
        margin: auto;
    }
    .header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .chatbot {
        height: 500px;
    }
    """
    
    with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
        # Header
        gr.HTML("""
            <div class="header">
                <h1>🚀 Rackspace Knowledge Chatbot</h1>
                <p>Ask me anything about Rackspace Technology!</p>
                <p style="font-size: 0.9em; margin-top: 10px;">
                    Powered by Fine-Tuned LLM + RAG System
                </p>
            </div>
        """)
        
        # Description
        with gr.Row():
            gr.Markdown("""
                ### Welcome! 👋
                
                I'm your Rackspace knowledge assistant. I can help you with:
                - 📖 Information about Rackspace Technology
                - 🎯 Rackspace's mission, vision, and services
                - 🌟 Fanatical Experience and customer support
                - ☁️ Cloud platforms and partnerships
                - 📜 Company history and background
                
                **I remember our conversation**, so you can ask follow-up questions or refer to previous topics!
                
                ---
            """)
        
        # Chat interface
        chatbot_ui = gr.ChatInterface(
            fn=chat_interface,
            title="",
            chatbot=gr.Chatbot(
                height=500,
                show_label=False,
                avatar_images=("👤", "🤖"),
                bubble_full_width=False
            ),
            textbox=gr.Textbox(
                placeholder="Type your question here... (e.g., 'What is Rackspace?')",
                container=False,
                scale=7
            ),
            examples=[
                "What is Rackspace?",
                "Tell me about Rackspace's mission",
                "What services does Rackspace offer?",
                "What is Fanatical Experience?",
                "When was Rackspace founded?",
                "Who are Rackspace's cloud partners?",
                "What did I ask first?"
            ],
            retry_btn=None,
            undo_btn="↩️ Undo",
            clear_btn="🗑️ Clear Conversation",
        )
        
        # Footer
        gr.Markdown("""
            ---
            <div style="text-align: center; color: #666; font-size: 0.9em;">
                <p>💡 <strong>Tip:</strong> You can ask about previous questions! Try: "What did I ask first?"</p>
                <p>🔧 Built with TinyLlama, ChromaDB, and Gradio | Optimized for Apple M3</p>
            </div>
        """)
    
    return demo


def main():
    """Main application entry point"""
    print("="*80)
    print("Rackspace Knowledge Chatbot")
    print("="*80)
    print("\nInitializing chatbot...")
    
    # Initialize chatbot
    if not initialize_chatbot():
        print("\n❌ Failed to initialize chatbot!")
        print("Please make sure:")
        print("1. Vector database is built (run: python vector_db.py)")
        print("2. Model is available (fine-tuned or base model)")
        return
    
    print("✅ Chatbot initialized successfully!")
    print("\n" + "="*80)
    print("Starting web interface...")
    print("="*80 + "\n")
    
    # Create and launch UI
    demo = create_ui()
    
    # Launch with public link optional
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Set to True to create public link
        show_error=True
    )


if __name__ == "__main__":
    main()
