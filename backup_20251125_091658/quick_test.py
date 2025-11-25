"""
Quick test script to verify the chatbot works
"""
import sys
print("Loading modules...")

try:
    from rag_chatbot import RAGChatbot
    print("✓ Modules loaded")
    
    print("\n🚀 Initializing chatbot with base model...")
    print("⏳ This will take 2-3 minutes to download TinyLlama (1.1GB)...")
    print("Please be patient...\n")
    
    bot = RAGChatbot(use_base_model=True)
    print("\n✅ Chatbot initialized successfully!")
    
    print("\n" + "="*80)
    print("Testing chatbot with a question...")
    print("="*80)
    
    question = "What is Rackspace?"
    print(f"\nQ: {question}")
    response = bot.chat(question)
    print(f"\nA: {response}\n")
    
    print("="*80)
    print("✅ SUCCESS! The chatbot is working!")
    print("="*80)
    print("\nYou can now run: python app.py")
    print("to launch the web interface at http://localhost:7860\n")
    
except KeyboardInterrupt:
    print("\n\n⚠️  Process interrupted!")
    print("The model download takes time. Please let it complete.\n")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
