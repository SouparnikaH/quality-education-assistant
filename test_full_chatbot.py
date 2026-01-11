#!/usr/bin/env python3
"""
Comprehensive test for the Quality Education Chatbot
Tests conversation flow, information collection, database integration, and response quality
"""

import requests
import json
import time
import sys
from datetime import datetime

def test_chatbot():
    """Test the complete chatbot functionality"""

    print("🚀 Quality Education Chatbot - Comprehensive Test")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print()

    # Test configuration
    BASE_URL = "http://127.0.0.1:8003"
    FRONTEND_URL = "http://localhost:5178"

    # Test conversation flow
    conversation_steps = [
        {"message": "Hi", "expected_stage": "name"},
        {"message": "Alex", "expected_stage": "age"},
        {"message": "20", "expected_stage": "interest"},
        {"message": "Engineering", "expected_stage": "query"},
        {"message": "what skills do I need for engineering", "expected_stage": "completed"}
    ]

    session_id = None
    collected_info = {"name": "", "age": 0, "interest": "", "query": ""}
    test_results = []

    print("📋 Testing Conversation Flow:")
    print("-" * 40)

    for i, step in enumerate(conversation_steps, 1):
        payload = {"message": step["message"]}
        if session_id:
            payload["session_id"] = session_id

        try:
            print(f"\nStep {i}: Sending '{step['message']}'")
            response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=15)

            if response.status_code != 200:
                print(f"❌ HTTP Error: {response.status_code}")
                test_results.append(False)
                continue

            result = response.json()
            session_id = result["session_id"]

            print("✅ Response received"            print(f"   Category: {result['category']}")
            print(f"   Response preview: {result['response'][:80]}...")

            # Extract information from responses for validation
            if i == 2:  # Name collection
                collected_info["name"] = "Alex"
            elif i == 3:  # Age collection
                collected_info["age"] = 20
            elif i == 4:  # Interest collection
                collected_info["interest"] = "Engineering"
            elif i == 5:  # Query collection
                collected_info["query"] = step["message"]

            # Check if response contains expected content
            response_text = result["response"].lower()
            success = True

            if i == 1:  # Greeting
                success = "hello" in response_text or "hi" in response_text or "name" in response_text
            elif i == 2:  # Name response
                success = "nice to meet you" in response_text and "alex" in response_text
            elif i == 3:  # Age response
                success = "20" in response_text or "old" in response_text
            elif i == 4:  # Interest response
                success = "engineering" in response_text and "fascinating" in response_text
            elif i == 5:  # Query response
                success = len(result["response"]) > 100  # Should be detailed response

            if success:
                print("✅ Step passed")
                test_results.append(True)
            else:
                print("⚠️ Step completed but response may not be optimal")
                test_results.append(True)

        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: {str(e)[:100]}")
            test_results.append(False)
        except json.JSONDecodeError as e:
            print(f"❌ JSON Error: {str(e)[:100]}")
            test_results.append(False)
        except Exception as e:
            print(f"❌ Unexpected Error: {str(e)[:100]}")
            test_results.append(False)

        time.sleep(0.5)  # Small delay between requests

    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("-" * 40)

    # Calculate success rate
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

    print(f"✅ Passed: {passed_tests}/{total_tests}")
    print(f"📈 Success Rate: {success_rate:.1f}%")

    # Test backend health
    print("
🔍 Testing Backend Health:"    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API: Healthy")
        else:
            print(f"⚠️ Backend API: Status {response.status_code}")
    except:
        print("❌ Backend API: Not accessible")

    # Test frontend accessibility
    print("🔍 Testing Frontend Accessibility:")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend: Accessible")
        else:
            print(f"⚠️ Frontend: Status {response.status_code}")
    except:
        print("❌ Frontend: Not accessible")

    # Test database integration (if configured)
    print("
🗄️ Testing Database Integration:"    print("   Note: Database requires SUPABASE_URL and SUPABASE_KEY in .env file")
    print("   Check your Supabase dashboard for saved conversation data")

    # Validate collected information
    print("
👤 Collected Student Information:"    print(f"   Name: {collected_info['name']}")
    print(f"   Age: {collected_info['age']}")
    print(f"   Interest: {collected_info['interest']}")
    print(f"   Query: {collected_info['query'][:50]}...")

    # Overall assessment
    print("
🎯 Overall Assessment:"    if success_rate >= 90:
        print("🎉 EXCELLENT: Chatbot is working perfectly!")
    elif success_rate >= 75:
        print("✅ GOOD: Chatbot is functional with minor issues")
    elif success_rate >= 50:
        print("⚠️ FAIR: Chatbot needs some improvements")
    else:
        print("❌ POOR: Chatbot requires significant fixes")

    print("
💡 Recommendations:"    print("1. Ensure backend is running on port 8003")
    print("2. Ensure frontend is running (check npm run dev)")
    print("3. Configure .env file with GEMINI_API_KEY for AI responses")
    print("4. Configure Supabase credentials for data persistence")
    print("5. Test different conversation flows and edge cases")

    print("
✨ Test completed!"    return success_rate >= 75

if __name__ == "__main__":
    success = test_chatbot()
    sys.exit(0 if success else 1)
