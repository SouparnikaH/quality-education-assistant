from supabase import create_client, Client
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL", "").strip()
        supabase_key = os.getenv("SUPABASE_KEY", "").strip()

        if (not supabase_url or not supabase_key or
            "your_" in supabase_url.lower() or "your_" in supabase_key.lower() or
            supabase_url == "" or supabase_key == ""):
            print("WARNING: SUPABASE_URL and SUPABASE_KEY not configured. Database features will be disabled.")
            print("Please add these to your .env file to enable data persistence.")
            self.client = None
        else:
            try:
                self.client: Client = create_client(supabase_url, supabase_key)
                print("Supabase database connected successfully")
            except Exception as e:
                print(f"WARNING: Failed to initialize Supabase client: {e}")
                print("Database features will be disabled.")
                self.client = None

    def save_conversation_state(self, session_id: str, state: Dict[str, Any]):
        """Save conversation state to database"""
        if self.client is None:
            print("Database not configured - skipping save")
            return

        try:
            # Upsert conversation
            self.client.table("conversations").upsert({
                "session_id": session_id,
                "updated_at": "now()"
            }).execute()

            # Save data incrementally as information becomes available
            # At minimum, save name and session_id if available
            if state.get("student_name"):
                # Prepare data to save - only include fields that have values
                data_to_save = {
                    "session_id": session_id,
                    "student_name": state.get("student_name"),
                }

                # Add optional fields if they exist
                if state.get("student_age"):
                    data_to_save["student_age"] = state.get("student_age")
                if state.get("area_of_interest"):
                    data_to_save["area_of_interest"] = state.get("area_of_interest")
                if state.get("student_query"):
                    data_to_save["student_query"] = state.get("student_query")
                if state.get("guidance_type"):
                    data_to_save["guidance_type"] = state.get("guidance_type")

                # Use upsert to update existing records or insert new ones
                self.client.table("conversation_data").upsert(
                    data_to_save,
                    on_conflict="session_id"
                ).execute()
                print(f"Conversation data saved/updated for session: {session_id}")
            else:
                print(f"No student name collected yet for session: {session_id}")

        except Exception as e:
            print(f"Database error: {e}")
