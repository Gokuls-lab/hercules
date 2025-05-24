import hashlib
import time
import os
import json
from pathlib import Path

# Base directory for user rooms, ensure this path is configurable/correct for your environment
# Using data/rooms/ as discussed.
BASE_ROOMS_PATH = Path("data/rooms") 

async def create_task_room(user_id: str, task_prompt: str) -> str:
    """
    Creates a new task room for a user.
    - Generates a unique room ID.
    - Creates a directory for the room.
    - Stores initial metadata (for now, in a JSON file within the room).
    Returns the room_id.
    """
    timestamp = str(time.time())
    # Generate room_id: sha256(user_id + timestamp)
    raw_room_id_str = f"{user_id}{timestamp}"
    room_id = hashlib.sha256(raw_room_id_str.encode('utf-8')).hexdigest()

    room_path = BASE_ROOMS_PATH / room_id
    try:
        room_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory: {room_path}. Error: {e}")
        raise Exception(f"Could not create room directory: {e}")

    # Store input prompt
    try:
        with open(room_path / "input_prompt.txt", "w") as f:
            f.write(task_prompt)
    except IOError as e:
        print(f"Error writing input_prompt.txt for room {room_id}. Error: {e}")
        # Potentially clean up created directory or handle error appropriately
        raise Exception(f"Could not write initial prompt to room: {e}")

    # Store metadata (mocking DB call by writing to a JSON file in the room)
    # This will be replaced by a proper Supabase call later.
    room_metadata = {
        "room_id": room_id,
        "user_id": user_id,
        "task_prompt": task_prompt,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%Z", time.gmtime()), # ISO 8601 UTC
        "status": "pending", # Initial status
        "folder_path": str(room_path.resolve()), # Store absolute path
        # "llm_used": None, # Will be set later
        # "agents_used": None # Will be set later
    }
    try:
        with open(room_path / "room_metadata.json", "w") as f:
            json.dump(room_metadata, f, indent=4)
    except IOError as e:
        print(f"Error writing room_metadata.json for room {room_id}. Error: {e}")
        raise Exception(f"Could not write room metadata: {e}")
    
    print(f"Room {room_id} created for user {user_id} at {room_path}")
    return room_id
