#!/usr/bin/env python3
"""
Test script to debug conversation flow and database saving issues
"""
import os
import sys
sys.path.append('backend')

from backend.app.main import extract_student_info, sessions
from backend.app.database import Database
import uuid

def test_name_extraction():
    """Test if name extraction works"""
    print("Testing Name Extraction:")

    test_cases = [
        "John",
        "My name is Sarah",
        "I'm Michael",
        "I am David",
        "Call me Emma",
        "Name is Robert",
        "This is Lisa"
    ]

    for test_input in test_cases:
        result = extract_student_info(test_input)
        print(f"  Input: '{test_input}' -> Name: '{result['name']}'")

def test_database_connection():
    """Test database connection"""
    print("\nTesting Database Connection:")

    db = Database()

    if db.client is None:
        print("  ERROR: Database not configured")
        print("  HINT: Please set SUPABASE_URL and SUPABASE_KEY in backend/.env")
        return False

    print("  SUCCESS: Database client initialized")

    # Test saving conversation data
    test_session_id = f"test_{uuid.uuid4().hex[:8]}"
    test_data = {
        "student_name": "Test User",
        "student_age": 20,
        "area_of_interest": "Engineering",
        "student_query": "What skills do I need?",
        "guidance_type": "career_guidance"
    }

    try:
        db.save_conversation_state(test_session_id, test_data)
        print("  SUCCESS: Test data saved successfully")
        return True
    except Exception as e:
        print(f"  ERROR: Database save failed: {e}")
        return False

def test_conversation_flow():
    """Test the conversation flow logic"""
    print("\nTesting Conversation Flow:")

    # Create a test session
    session_id = f"test_{uuid.uuid4().hex[:8]}"
    sessions[session_id] = {
        "student_info": {"name": "", "age": 0, "interest": "", "query": ""},
        "conversation_stage": "greeting",
        "messages": []
    }

    # Simulate conversation
    test_flow = [
        ("greeting", "Hi", "name"),
        ("name", "John", "age"),
        ("age", "20", "interest"),
        ("interest", "Engineering", "query"),
        ("query", "What skills do I need?", "completed")
    ]

    for stage, user_input, expected_next_stage in test_flow:
        session = sessions[session_id]

        if session["conversation_stage"] != stage:
            print(f"  ERROR: Expected stage '{stage}', got '{session['conversation_stage']}'")
            continue

        print(f"  Stage '{stage}': User says '{user_input}'")

        # Simulate the conversation logic from main.py
        if session["conversation_stage"] == "greeting":
            session["conversation_stage"] = "name"
            print("    -> Moved to 'name' stage")

        elif session["conversation_stage"] == "name":
            extracted_info = extract_student_info(user_input, session["student_info"])
            if extracted_info["name"]:
                session["student_info"]["name"] = extracted_info["name"]
                session["conversation_stage"] = "age"
                print(f"    -> Name extracted: '{extracted_info['name']}', moved to 'age' stage")
            else:
                print("    -> Name not extracted")

        elif session["conversation_stage"] == "age":
            extracted_info = extract_student_info(user_input, session["student_info"])
            if extracted_info["age"] > 0:
                session["student_info"]["age"] = extracted_info["age"]
                session["conversation_stage"] = "interest"
                print(f"    -> Age extracted: {extracted_info['age']}, moved to 'interest' stage")
            else:
                # Try direct age extraction
                import re
                age_match = re.search(r'\b(1[3-9]|[2-9][0-9])\b', user_input)
                if age_match:
                    age = int(age_match.group(1))
                    if 13 <= age <= 100:
                        session["student_info"]["age"] = age
                        session["conversation_stage"] = "interest"
                        print(f"    -> Age extracted (regex): {age}, moved to 'interest' stage")
                    else:
                        print("    -> Age out of range")
                else:
                    print("    -> Age not extracted")

        elif session["conversation_stage"] == "interest":
            extracted_info = extract_student_info(user_input, session["student_info"])
            if extracted_info["interest"]:
                session["student_info"]["interest"] = extracted_info["interest"]
                session["conversation_stage"] = "query"
                print(f"    -> Interest extracted: '{extracted_info['interest']}', moved to 'query' stage")
            else:
                # Check common interests
                interests = {
                    "engineering": ["engineering", "engineer", "tech", "technology", "computer"],
                    "medicine": ["medicine", "medical", "doctor", "healthcare"],
                    "arts": ["arts", "art", "design", "creative"],
                    "business": ["business", "commerce", "management", "finance"],
                    "science": ["science", "physics", "chemistry", "biology"],
                    "law": ["law", "legal", "lawyer", "attorney"]
                }

                found_interest = None
                input_lower = user_input.lower()
                for interest, keywords in interests.items():
                    if any(keyword in input_lower for keyword in keywords):
                        found_interest = interest.capitalize()
                        break

                if found_interest:
                    session["student_info"]["interest"] = found_interest
                    session["conversation_stage"] = "query"
                    print(f"    -> Interest found (keywords): '{found_interest}', moved to 'query' stage")
                else:
                    print("    -> Interest not extracted")

        elif session["conversation_stage"] == "query":
            session["student_info"]["query"] = user_input
            session["conversation_stage"] = "completed"
            print("    -> Query stored, moved to 'completed' stage")

        # Check if stage matches expected
        if session["conversation_stage"] != expected_next_stage:
            print(f"    ERROR: Expected next stage '{expected_next_stage}', got '{session['conversation_stage']}'")
        else:
            print(f"    SUCCESS: Correctly moved to '{expected_next_stage}' stage")

    # Print final session state
    print(f"\nFinal Session State:")
    print(f"  Name: {session['student_info']['name']}")
    print(f"  Age: {session['student_info']['age']}")
    print(f"  Interest: {session['student_info']['interest']}")
    print(f"  Query: {session['student_info']['query']}")
    print(f"  Stage: {session['conversation_stage']}")

    return session

def main():
    print("Quality Education Chatbot - Debug Test")
    print("=" * 50)

    # Test name extraction
    test_name_extraction()

    # Test database connection
    db_working = test_database_connection()

    # Test conversation flow
    final_session = test_conversation_flow()

    # Test database save if db is working
    if db_working and final_session["conversation_stage"] == "completed":
        print("\nTesting Database Save:")
        db = Database()
        db.save_conversation_state(session_id, {
            "student_name": final_session["student_info"]["name"],
            "student_age": final_session["student_info"]["age"],
            "area_of_interest": final_session["student_info"]["interest"],
            "student_query": final_session["student_info"]["query"],
            "guidance_type": "career_guidance"
        })
        print("  SUCCESS: Database save attempted")

    print("\nSummary:")
    print("  - Name extraction: Test above")
    print("  - Database connection: " + ("SUCCESS" if db_working else "ERROR: Not configured"))
    print("  - Conversation flow: Test above")
    print("\nIf issues found, check:")
    print("  1. backend/.env file has correct API keys")
    print("  2. Supabase tables are created (run supabase_setup.sql)")
    print("  3. Environment variables are loaded correctly")

if __name__ == "__main__":
    main()
