# hercules/backend/app/room_manager.py
import hashlib
import time
import os
# import json # No longer needed for room_metadata.json
from pathlib import Path
from .supabase_client import store_room_metadata_in_supabase, get_supabase_admin_client 
# Import status for HTTPException, though it's not directly used here, good for reference
from fastapi import status 

BASE_ROOMS_PATH = Path("data/rooms") # Local file storage for room artifacts

async def create_task_room(user_id: str, task_prompt: str) -> tuple[str | None, dict | None, dict | None]:
    """
    Creates a new task room for a user:
    - Generates a unique room ID.
    - Creates a local directory for the room's files.
    - Stores room metadata in Supabase.
    Returns (room_id, stored_metadata_dict, error_dict).
    """
    try:
        get_supabase_admin_client() # Check if Supabase client is available
    except ConnectionError as e:
        # Return the error in a way that main.py can process it into an HTTPException
        return None, None, {"message": str(e), "status_code": status.HTTP_503_SERVICE_UNAVAILABLE}

    timestamp_str = str(time.time())
    raw_room_id_str = f"{user_id}{timestamp_str}" # Ensure user_id is string
    room_id = hashlib.sha256(raw_room_id_str.encode('utf-8')).hexdigest()

    room_path = BASE_ROOMS_PATH / room_id
    try:
        room_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory: {room_path}. Error: {e}")
        return None, None, {"message": f"Could not create room directory: {e}", "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}

    try:
        with open(room_path / "input_prompt.txt", "w") as f:
            f.write(task_prompt)
    except IOError as e:
        print(f"Error writing input_prompt.txt for room {room_id}. Error: {e}")
        return None, None, {"message": f"Could not write initial prompt to room: {e}", "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}

    room_metadata_to_store = {
        "room_id": room_id,
        "user_id": user_id, # Should be UUID as string
        "task_prompt": task_prompt,
        "folder_path": str(room_path.resolve()),
        "status": "pending",
        # created_at will be set by Supabase default
        # llm_used, agents_used can be updated later
    }
    
    # The supabase_client.py's store_room_metadata_in_supabase already handles ConnectionError for its own operations.
    # It returns (data, error_dict)
    stored_data, error = await store_room_metadata_in_supabase(room_metadata_to_store)

    if error:
        print(f"Error storing room metadata in Supabase for room {room_id}: {error}")
        # Consider cleanup of room_path if Supabase storage fails.
        # For now, directory might remain, but task creation failed.
        # Ensure the error dict includes a status_code if possible, or main.py will default.
        if "status_code" not in error: # Default error status if not provided by Supabase client
            error["status_code"] = status.HTTP_500_INTERNAL_SERVER_ERROR
        return None, None, error 

    if not stored_data:
        # This case should ideally be covered by the 'error' from store_room_metadata_in_supabase
        print(f"No data returned from Supabase for room {room_id} despite no explicit error.")
        return None, None, {"message": "Failed to store metadata in Supabase, no data returned.", "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}
        
    print(f"Room {room_id} created, directory at {room_path}, metadata stored in Supabase: {stored_data}")
    return room_id, stored_data, None
