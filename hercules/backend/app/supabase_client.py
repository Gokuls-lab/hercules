# hercules/backend/app/supabase_client.py
import os
from supabase import create_client, Client, SupabaseClientError, PostgrestAPIError
from dotenv import load_dotenv

# Load .env file if it exists (for local development)
load_dotenv() 

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") # Use service key for backend operations

supabase_admin_client: Client | None = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase_admin_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Successfully initialized Supabase admin client.")
    except Exception as e:
        print(f"Error initializing Supabase admin client: {e}")
        supabase_admin_client = None
else:
    print("Warning: SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables not set. Supabase admin client not initialized.")

def get_supabase_admin_client() -> Client:
    if supabase_admin_client is None:
        raise ConnectionError("Supabase admin client is not initialized. Check environment variables (SUPABASE_URL, SUPABASE_SERVICE_KEY).")
    return supabase_admin_client

async def get_user_by_token(token: str) -> dict | None:
    client = get_supabase_admin_client()
    try:
        response = client.auth.get_user(token)
        if response.user:
            # Return user data as a dict
            return response.user.dict() 
        return None
    except SupabaseClientError as e:
        print(f"Supabase client error getting user by token: {e}")
        # Distinguish between client errors and actual "not found" or "invalid token"
        # For simplicity, returning None here, but more specific error handling might be needed.
        return None 
    except Exception as e:
        print(f"Unexpected error getting user by token: {e}")
        return None

async def register_user_in_supabase(email: str, password: str) -> tuple[dict | None, dict | None]:
    client = get_supabase_admin_client()
    try:
        response = client.auth.sign_up({"email": email, "password": password})
        if response.user and response.session:
            return response.user.dict(), response.session.dict()
        # Handle cases like user already exists (though Supabase might return an error that's caught below)
        # Supabase sign_up might return a user object even if email confirmation is required and no session.
        if response.user and not response.session: # User exists, or email confirmation pending
             return response.user.dict(), None # No active session yet
        return None, None # Should not happen if no error
    except SupabaseClientError as e:
        print(f"Supabase client error during user registration: {e}")
        # Example: e.message might be "User already registered"
        # Convert Supabase error to a dict for consistent error handling
        return None, {"message": str(e), "status_code": e.status_code if hasattr(e, 'status_code') else 500}
    except Exception as e:
        print(f"Unexpected error during user registration: {e}")
        return None, {"message": "An unexpected error occurred.", "status_code": 500}

async def login_user_in_supabase(email: str, password: str) -> tuple[dict | None, dict | None, dict | None]:
    client = get_supabase_admin_client()
    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        if response.user and response.session:
            return response.user.dict(), response.session.dict(), None
        return None, None, {"message": "Login failed, user or session not returned."} # Should be caught by SupabaseClientError mostly
    except SupabaseClientError as e:
        print(f"Supabase client error during login: {e}")
        return None, None, {"message": str(e), "status_code": e.status_code if hasattr(e, 'status_code') else 400}
    except Exception as e:
        print(f"Unexpected error during login: {e}")
        return None, None, {"message": "An unexpected error occurred.", "status_code": 500}

async def store_room_metadata_in_supabase(room_data: dict) -> tuple[dict | None, dict | None]:
    client = get_supabase_admin_client()
    try:
        # Ensure user_id is a string (UUID) if it's coming from auth.get_user()
        if 'user_id' in room_data and hasattr(room_data['user_id'], 'id'):
            room_data['user_id'] = str(room_data['user_id'].id)

        data, count = client.table("rooms").insert(room_data).execute()
        # INSERT response format: data = [{'id': 1, 'col1': 'val1', ...}], count = None or 1
        if data and len(data[1]) > 0: # data[0] is the command, data[1] is the list of dicts
            return data[1][0], None 
        return None, {"message": "Failed to insert room metadata or no data returned."}
    except PostgrestAPIError as e: # Specific error for database operations
        print(f"Supabase Postgrest API error storing room metadata: {e}")
        return None, {"message": e.message, "details": e.details, "code": e.code, "status_code": e.status_code if hasattr(e, 'status_code') else 500}
    except SupabaseClientError as e:
        print(f"Supabase client error storing room metadata: {e}")
        return None, {"message": str(e), "status_code": e.status_code if hasattr(e, 'status_code') else 500}
    except Exception as e:
        print(f"Unexpected error storing room metadata: {e}")
        return None, {"message": "An unexpected error occurred.", "status_code": 500}

async def get_room_details_from_supabase(room_id: str, user_id: str) -> tuple[dict | None, dict | None]:
    """
    Fetches details for a specific room from Supabase, ensuring user ownership.
    Returns (room_details_dict, error_dict).
    """
    client = get_supabase_admin_client() # Raises ConnectionError if not initialized
    try:
        # Fetch room where room_id matches and user_id matches (for ownership)
        # response = client.table("rooms").select("*").eq("room_id", room_id).eq("user_id", user_id).maybe_single().execute()
        # The above line would be for RLS or if user_id in rooms table is auth.users.id
        # If user_id in rooms table is a string representation already, then:
        response = client.table("rooms").select("*").eq("room_id", room_id).eq("user_id", str(user_id)).maybe_single().execute()


        if response.data:
            return response.data, None
        else:
            # Could be room not found OR not owned by this user. 
            # For security, often better to return "not found" for both.
            # Check if room exists at all (without user_id filter) to give more specific error if needed,
            # but this might leak info that a room_id is valid.
            # For now, simple "not found or not authorized".
            return None, {"message": "Room not found or you do not have permission to view it.", "status_code": 404} 
            
    except PostgrestAPIError as e:
        print(f"Supabase Postgrest API error fetching room details for room {room_id}: {e}")
        return None, {"message": e.message, "details": e.details, "code": e.code, "status_code": e.status_code if hasattr(e, 'status_code') else 500}
    except SupabaseClientError as e: # Broader client errors
        print(f"Supabase client error fetching room details for room {room_id}: {e}")
        return None, {"message": str(e), "status_code": e.status_code if hasattr(e, 'status_code') else 500}
    except Exception as e:
        print(f"Unexpected error fetching room details for room {room_id}: {e}")
        return None, {"message": "An unexpected error occurred while fetching room details.", "status_code": 500}

async def store_ai_message_in_supabase(message_data: dict) -> tuple[dict | None, dict | None]:
    """
    Stores a single AI agent message in the 'ai_messages' table in Supabase.
    `message_data` should conform to the schema of 'ai_messages'.
    Required fields in message_data: room_id, agent_name, content
    Optional: response (if it's a prompt/response pair), model_used, tool_calls, token_count
    Returns (stored_message_dict, error_dict).
    """
    client = get_supabase_admin_client() # Raises ConnectionError if not initialized
    
    # Basic validation for required fields
    required_fields = ["room_id", "agent_name", "content"]
    for field in required_fields:
        if field not in message_data or not message_data[field]:
            return None, {"message": f"Missing required field for AI message: {field}", "status_code": 400}

    # Ensure room_id is a string if it's passed as UUID object from elsewhere
    if hasattr(message_data.get("room_id"), "hex"): # Check if it's a UUID object
         message_data["room_id"] = str(message_data["room_id"])


    # 'timestamp' is set by default in DB (now()), but can be overridden if provided.
    # If not provided, Supabase will use its default.
    # if 'timestamp' not in message_data:
    #    message_data['timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()


    try:
        # Supabase `insert` expects a list of dicts.
        response = client.table("ai_messages").insert(message_data).execute()
        
        # INSERT response format: data = [{'id': 1, 'col1': 'val1', ...}], count = None or 1
        # In Supabase-py v1, response.data is the list of dicts directly.
        # In Supabase-py v2 (gotrue v2 based), response.data might be an object with a 'data' attribute.
        # Let's assume response.data is the list of records for now, as per common usage.
        # Check if data attribute exists in response, otherwise use response itself
        
        # The actual data is in response.data, which is a list.
        # For an insert, it's usually a list containing one dictionary (the inserted row).
        if response.data and len(response.data) > 0:
            return response.data[0], None 
        else:
            # This case might indicate an issue not caught by an exception (e.g. RLS preventing readback)
            print(f"AI message insert for room {message_data.get('room_id')} seemed to succeed but returned no data.")
            return None, {"message": "AI message stored but no confirmation data returned.", "status_code": 200} # Or 204 if that's more appropriate
            
    except PostgrestAPIError as e:
        print(f"Supabase Postgrest API error storing AI message for room {message_data.get('room_id')}: {e}")
        return None, {"message": e.message, "details": e.details, "code": e.code, "status_code": e.status_code if hasattr(e, 'status_code') else 500}
    except SupabaseClientError as e:
        print(f"Supabase client error storing AI message for room {message_data.get('room_id')}: {e}")
        return None, {"message": str(e), "status_code": e.status_code if hasattr(e, 'status_code') else 500}
    except Exception as e:
        print(f"Unexpected error storing AI message for room {message_data.get('room_id')}: {e}")
        return None, {"message": "An unexpected error occurred while storing AI message.", "status_code": 500}

async def get_ai_messages_for_room_from_supabase(room_id: str, user_id: str) -> tuple[list[dict] | None, dict | None]:
    """
    Fetches all AI messages for a specific room from Supabase, 
    after verifying user ownership of the room.
    Returns (list_of_message_dicts, error_dict).
    """
    client = get_supabase_admin_client() # Raises ConnectionError if not initialized
    
    try:
        # First, verify the user owns the room to prevent unauthorized access to messages.
        # This reuses the logic from get_room_details_from_supabase for the ownership check part.
        room_check_response = client.table("rooms").select("id, user_id").eq("room_id", room_id).eq("user_id", str(user_id)).maybe_single().execute()

        if not room_check_response.data:
            return None, {"message": "Room not found or you do not have permission to view its messages.", "status_code": 404}

        # If room ownership is confirmed, fetch the messages for that room_id.
        # Note: The 'ai_messages' table's 'room_id' field should store the same string 'room_id'
        # that is used in the 'rooms' table, not the integer PK 'id' from 'rooms' table,
        # unless schema was designed differently. Assuming 'room_id' (string hash) is the FK.
        # If 'ai_messages.room_id' is actually a FK to 'rooms.id' (integer), this query needs adjustment.
        # Based on schema.md, `ai_messages.room_id` is FK to `rooms.id` (UUID PK).
        # Let's assume `room_check_response.data['id']` gives the UUID PK of the room.
        
        # The schema discussion mentioned `ai_messages.room_id` as FK to `rooms.id` (UUID).
        # And `rooms.room_id` is the textual hash.
        # So, we need the UUID `id` from `rooms` table to filter `ai_messages`.
        
        room_pk_id = room_check_response.data.get("id") # This should be the UUID PK of the room.
        if not room_pk_id:
             return None, {"message": "Internal error: Room primary key not found after ownership check.", "status_code": 500}


        messages_response = client.table("ai_messages").select("*").eq("room_id", str(room_pk_id)).order("timestamp", desc=False).execute()
        
        if messages_response.data:
            return messages_response.data, None
        else:
            # It's valid for a room to have no messages yet.
            return [], None 
            
    except PostgrestAPIError as e:
        print(f"Supabase Postgrest API error fetching AI messages for room {room_id}: {e}")
        return None, {"message": e.message, "details": e.details, "code": e.code, "status_code": e.status_code if hasattr(e, 'status_code') else 500}
    except SupabaseClientError as e:
        print(f"Supabase client error fetching AI messages for room {room_id}: {e}")
        return None, {"message": str(e), "status_code": e.status_code if hasattr(e, 'status_code') else 500}
    except Exception as e:
        print(f"Unexpected error fetching AI messages for room {room_id}: {e}")
        return None, {"message": "An unexpected error occurred while fetching AI messages.", "status_code": 500}
