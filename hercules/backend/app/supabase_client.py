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
