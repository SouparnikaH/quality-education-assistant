#!/usr/bin/env python3
"""
Test script to debug the chat API error
"""
import requests
import json

def test_chat_api():
    """Test the chat API with multiple messages to simulate conversation"""
    url = "http://127.0.0.1:8003/chat"
    headers = {"Content-Type": "application/json"}

    # Test conversation flow
    messages = [
        ("hi", "greeting"),
        ("John", "name"),
        ("20", "age"),
        ("Engineering", "interest"),
        ("What skills do I need?", "query")
    ]

    session_id = None

    for message, stage in messages:
        payload = {
            "message": message,
            "session_id": session_id
        }

        try:
            print(f"\n=== Testing {stage}: '{message}' ===")
            print(f"Session ID: {session_id}")

            response = requests.post(url, json=payload, headers=headers, timeout=10)

            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                response_data = response.json()
                session_id = response_data.get('session_id')
                bot_response = response_data.get('response', '')[:100] + "..." if len(response_data.get('response', '')) > 100 else response_data.get('response', '')

                print(f"Bot: {bot_response}")
                print(f"Category: {response_data.get('category')}")
            else:
                print(f"Error: {response.text}")

        except Exception as e:
            print(f"Request failed: {e}")
            break

if __name__ == "__main__":
    test_chat_api()
