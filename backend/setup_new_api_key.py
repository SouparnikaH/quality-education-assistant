#!/usr/bin/env python3
"""
Setup script for new Gemini API key.
Replace YOUR_NEW_API_KEY_HERE with your actual key.
"""
import os

# 🔑 REPLACE THIS WITH YOUR NEW GEMINI API KEY
NEW_API_KEY = "YOUR_NEW_API_KEY_HERE"

def update_api_key():
    """Update the API key in .env file"""
    if NEW_API_KEY == "YOUR_NEW_API_KEY_HERE":
        print("ERROR: Please replace YOUR_NEW_API_KEY_HERE with your actual Gemini API key!")
        print()
        print("STEPS TO GET A NEW API KEY:")
        print("1. Go to: https://aistudio.google.com/")
        print("2. Sign in with your Google account")
        print("3. Click 'Get started' or 'Create API key'")
        print("4. Copy the API key (starts with 'AIzaSy...')")
        print("5. Replace YOUR_NEW_API_KEY_HERE in this file with your key")
        print("6. Run this script again")
        return False

    # Update .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')

    try:
        # Read current .env
        env_content = ""
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_content = f.read()

        # Update GEMINI_API_KEY
        lines = env_content.split('\n')
        key_found = False
        for i, line in enumerate(lines):
            if line.startswith('GEMINI_API_KEY='):
                lines[i] = f'GEMINI_API_KEY={NEW_API_KEY}'
                key_found = True
                break

        if not key_found:
            lines.append(f'GEMINI_API_KEY={NEW_API_KEY}')

        # Write back to .env
        with open(env_path, 'w') as f:
            f.write('\n'.join(lines))

        print("SUCCESS: API key updated in .env file")
        return True

    except Exception as e:
        print(f"ERROR: Failed to update .env file: {e}")
        return False

def test_api_key():
    """Test if the new API key works"""
    try:
        import google.generativeai as genai
        genai.configure(api_key=NEW_API_KEY)

        # Test with the best available model
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']

        for model_name in models_to_try:
            try:
                print(f"Testing model: {model_name}")
                llm = genai.GenerativeModel(model_name)
                response = llm.generate_content('Respond with exactly: API test successful')

                if response and response.text and 'successful' in response.text.lower():
                    print(f"SUCCESS: {model_name} is working!")
                    print(f"Response: {response.text.strip()}")

                    # Update main.py to use this model
                    update_model_in_main(model_name)
                    return True
                else:
                    print(f"Model {model_name} returned unexpected response")

            except Exception as e:
                print(f"Model {model_name} failed: {str(e)[:100]}...")

        print("ERROR: None of the models work with your API key")
        return False

    except Exception as e:
        print(f"ERROR: API key test failed: {str(e)}")
        return False

def update_model_in_main(model_name):
    """Update the model name in main.py"""
    main_py_path = os.path.join(os.path.dirname(__file__), 'main.py')

    try:
        with open(main_py_path, 'r') as f:
            content = f.read()

        # Replace the model list with the working model
        old_code = "models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro', 'gemini-2.0-flash']"
        new_code = f"models_to_try = ['{model_name}']  # Working model found"
        new_content = content.replace(old_code, new_code)

        with open(main_py_path, 'w') as f:
            f.write(new_content)

        print(f"SUCCESS: Updated main.py to use working model: {model_name}")

    except Exception as e:
        print(f"WARNING: Could not update main.py automatically: {e}")
        print("You can manually update the models_to_try list in main.py")

if __name__ == "__main__":
    print("Setting up new Gemini API key...")
    print("=" * 40)

    if update_api_key():
        print("\nTesting new API key...")
        if test_api_key():
            print("\n" + "=" * 40)
            print("SUCCESS! Your chatbot now has working AI responses!")
            print("Restart the backend server to use the new API key.")
        else:
            print("\n" + "=" * 40)
            print("API key was updated but testing failed.")
            print("Check your API key or try a different model.")
    else:
        print("API key setup failed. Please check the error messages above.")
