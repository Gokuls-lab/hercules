import os
from supabase import create_client, Client

# TODO: Load these from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# supabase: Client | None = None
# if SUPABASE_URL and SUPABASE_KEY:
#     supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# else:
#     print("Warning: Supabase URL or Key not found. Supabase client not initialized.")

def get_supabase_client() -> Client | None:
    # This function can be enhanced to handle initialization better,
    # especially in a FastAPI dependency context.
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Warning: Supabase URL or Key not found. Supabase client cannot be created.")
    return None

# Example usage (will be moved to respective service modules)
async def get_user_by_token(token: str):
    # client = get_supabase_client()
    # if not client:
    #     raise Exception("Supabase client not initialized")
    # return client.auth.get_user(token)
    print(f"Placeholder: Would validate token and get user from Supabase for token: {token[:20]}...")
    return {"id": "mock_user_id", "email": "user@example.com"} # Mock response

async def store_room_metadata(metadata: dict):
    # client = get_supabase_client()
    # if not client:
    #     raise Exception("Supabase client not initialized")
    # data, error = client.table("rooms").insert(metadata).execute()
    # if error:
    #     raise Exception(f"Error storing room metadata: {error}")
    # return data
    print(f"Placeholder: Would store room metadata in Supabase: {metadata}")
    return {"id": "mock_db_id", **metadata} # Mock response
