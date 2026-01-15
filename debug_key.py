
import os
import google.generativeai as genai

# User provided key for testing
TEST_KEY = "AIzaSyCUQUOTieaMrSs0qklV-OKLSBBX9Rff53c"

def test_key():
    print(f"Testing key: {TEST_KEY[:10]}...")
    try:
        genai.configure(api_key=TEST_KEY)
        models = genai.list_models()
        print("Successfully connected to Gemini API.")
        
        available = []
        for m in models:
            if "generateContent" in m.supported_generation_methods:
                print(f" - Found model: {m.name}")
                available.append(m.name)
        
        if not available:
            print("No models found with generateContent capability.")
        else:
            print(f"Total available models: {len(available)}")
            
    except Exception as e:
        print(f"Error testing key: {e}")

if __name__ == "__main__":
    test_key()
