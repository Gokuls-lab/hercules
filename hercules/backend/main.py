from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_active_user
# Import the new room manager function
from app.room_manager import create_task_room 
from app.supabase_client import get_supabase_client # Keep for consistency, though not used directly in this change

app = FastAPI(title="Hercules Backend")

# --- Models ---
class UserRegistration(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TaskCreate(BaseModel):
    prompt: str

class RoomResponse(BaseModel):
    room_id: str
    message: str
    details: dict # For returning more info like user_id and prompt

# --- Health Check ---
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Healthy"}

# --- Auth Endpoints (Placeholders) ---
@app.post("/auth/register", summary="Register a new user (Placeholder)")
async def register_user(user_data: UserRegistration):
    print(f"Placeholder: Registering user {user_data.email}")
    # Actual Supabase registration logic would go here
    return {"message": "User registration placeholder", "user_id": "mock_user_id", "email": user_data.email}

@app.post("/auth/login", summary="Login a user (Placeholder)")
async def login_user(form_data: UserLogin):
    print(f"Placeholder: Logging in user {form_data.email}")
    # Actual Supabase login logic would go here
    if form_data.email == "user@example.com" and form_data.password == "string": # Matches example from supabase_client
         return {"access_token": "mock_jwt_token_for_testing", "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials (mock)")
    
# --- API Routes ---
@app.post("/api/tasks", response_model=RoomResponse, summary="Create a new task room (Protected)")
async def create_task_endpoint(
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_active_user) # Protects this endpoint
):
    user_id = current_user.get("id")
    if not user_id: # Should not happen if get_current_active_user works correctly
        raise HTTPException(status_code=500, detail="User ID not found in token")

    print(f"Task creation request received from user: {user_id} for prompt: '{task_data.prompt}'")
    
    try:
        room_id = await create_task_room(user_id=user_id, task_prompt=task_data.prompt)
        return {
            "room_id": room_id, 
            "message": "Task room created successfully.",
            "details": {
                "user_id": user_id,
                "prompt_submitted": task_data.prompt,
                "status": "pending"
            }
        }
    except Exception as e:
        # Log the exception e for debugging
        print(f"Error during task room creation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task room: {str(e)}")

@app.get("/users/me", summary="Get current user details (Protected)")
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return current_user
    
@app.get("/api/public_info")
async def public_info():
    return {"message": "This endpoint is public."}

# Ensure the BASE_ROOMS_PATH directory exists on startup for local dev
# This is a convenience for local development. In production, this should be handled by deployment scripts.
@app.on_event("startup")
async def startup_event():
    from app.room_manager import BASE_ROOMS_PATH
    BASE_ROOMS_PATH.mkdir(parents=True, exist_ok=True)
    print(f"Ensured base room directory exists: {BASE_ROOMS_PATH}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
