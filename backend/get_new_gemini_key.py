#!/usr/bin/env python3
"""
Script to help you get and test a new Gemini API key.
Run this after getting your new API key from Google AI Studio.
"""
import os
from dotenv import load_dotenv

def test_gemini_key():
    """Test a new Gemini API key"""
    print("Gemini API Key Testing Tool")
    print("=" * 40)

    # Load environment variables
    load_dotenv()

    # Get current API key
    current_key = os.getenv("GEMINI_API_KEY", "")
    print(f"Current API key: {'***' + current_key[-4:] if current_key else 'Not set'}")

    # Ask for new key
    new_key = input("\nEnter your new Gemini API key (or press Enter to keep current): ").strip()

    if new_key:
        # Update .env file
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        env_content = ""

        # Read current .env
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_content = f.read()

        # Update or add GEMINI_API_KEY
        lines = env_content.split('\n')
        key_found = False
        for i, line in enumerate(lines):
            if line.startswith('GEMINI_API_KEY='):
                lines[i] = f'GEMINI_API_KEY={new_key}'
                key_found = True
                break

        if not key_found:
            lines.append(f'GEMINI_API_KEY={new_key}')

        # Write back to .env
        with open(env_path, 'w') as f:
            f.write('\n'.join(lines))

        print("SUCCESS: API key updated in .env file")

        # Test the new key
        test_key(new_key)
    else:
        print("Testing current key...")
        test_key(current_key)

def test_key(api_key):
    """Test if the API key works"""
    if not api_key or api_key.startswith('your_'):
        print("ERROR: No valid API key configured")
        return

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Try different models in case gemini-2.0-flash is not available
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']

        for model_name in models_to_try:
            try:
                print(f"Testing model: {model_name}")
                llm = genai.GenerativeModel(model_name)
                response = llm.generate_content('Say "Hello, world!" in exactly 3 words.')

                if response and response.text:
                    print(f"SUCCESS: {model_name} works!")
                    print(f"Response: {response.text.strip()}")

                    # Update the main.py to use this working model
                    update_model_in_code(model_name)
                    return
                else:
                    print(f"ERROR: {model_name} returned empty response")

            except Exception as e:
                print(f"ERROR: {model_name} failed: {str(e)}")

        print("ERROR: None of the tested models work with your API key")
        print("HINT: Try getting a new API key from: https://aistudio.google.com/")

    except Exception as e:
        print(f"ERROR: Gemini initialization failed: {str(e)}")

def update_model_in_code(model_name):
    """Update the model name in main.py"""
    main_py_path = os.path.join(os.path.dirname(__file__), 'main.py')

    try:
        with open(main_py_path, 'r') as f:
            content = f.read()

        # Update the model name
        old_model = "gemini-2.0-flash"
        new_content = content.replace(f"genai.GenerativeModel('{old_model}')",
                                    f"genai.GenerativeModel('{model_name}')")

        with open(main_py_path, 'w') as f:
            f.write(new_content)

        print(f"SUCCESS: Updated main.py to use model: {model_name}")

    except Exception as e:
        print(f"ERROR: Failed to update main.py: {str(e)}")

if __name__ == "__main__":
    test_gemini_key()
