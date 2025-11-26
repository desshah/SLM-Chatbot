"""
Test script to verify Groq API integration
"""
import os
from groq import Groq

def test_groq_api():
    """Test basic Groq API functionality"""
    print("Testing Groq API connection...")
    
    # Check for API key
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY environment variable not set!")
        print("\nTo set it, run:")
        print("export GROQ_API_KEY='your_api_key_here'")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        # Initialize client
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized")
        
        # Test a simple completion
        print("\nTesting chat completion...")
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say 'Hello from Groq!' if you can hear me.",
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        
        response = chat_completion.choices[0].message.content
        print(f"✅ Response received: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_groq_api()
    if success:
        print("\n🎉 Groq API integration successful!")
        print("\nYou can now use the chatbot with:")
        print("  python enhanced_rag_chatbot.py")
        print("  or")
        print("  streamlit run streamlit_app.py")
    else:
        print("\n⚠️  Please fix the errors above and try again.")
