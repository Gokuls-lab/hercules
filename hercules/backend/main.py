# hercules/backend/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr # Use EmailStr for validation

from app.auth import get_current_active_user
from app.room_manager import create_task_room # Will be updated to use Supabase
# Import new Supabase functions for auth
from app.supabase_client import register_user_in_supabase, login_user_in_supabase, get_supabase_admin_client
from app.supabase_client import get_room_details_from_supabase # Add this import

app = FastAPI(title="Hercules Backend")

# --- Models ---
class UserRegistration(BaseModel):
    email: EmailStr # Use Pydantic's EmailStr for validation
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str # Assuming user ID is a string (UUID from Supabase)
    email: EmailStr

class TaskCreate(BaseModel):
    prompt: str

class RoomResponse(BaseModel): # For successful room creation
    room_id: str
    message: str
    details: dict # To return the stored metadata

class RoomDetailsResponse(BaseModel): # Or reuse an existing one if suitable
    room_id: str
    user_id: str
    task_prompt: str
    created_at: str # Consider datetime type if Pydantic handles it well for responses
    status: str
    folder_path: str | None = None # May or may not be exposed
    # Add any other fields from your 'rooms' table that you want to return
    # e.g., llm_used: str | None, agents_used: list | None


# --- Health Check ---
@app.get("/health", summary="Health check endpoint")
async def health_check():
    try:
        get_supabase_admin_client() # Check if Supabase client is accessible
        # Note: This doesn't mean Supabase is fully working, just that the client could be init'd if vars were there
        return {"status": "ok", "message": "Healthy, Supabase client library accessible."}
    except ConnectionError as e:
        # This means SUPABASE_URL/KEY are likely missing, and client could not be initialized.
        return {"status": "degraded", "message": f"Healthy, but Supabase client NOT INITIALIZED: {str(e)}"}


# --- Auth Endpoints ---
@app.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, summary="Register a new user")
async def register_user_endpoint(user_data: UserRegistration):
    try:
        user, session, error = await register_user_in_supabase(user_data.email, user_data.password)
        if error:
            error_status_code = error.get("status_code", status.HTTP_400_BAD_REQUEST)
            raise HTTPException(status_code=error_status_code, detail=error.get("message", "User registration failed"))
        if user and session: # Successful registration and immediate login
            return {
                "access_token": session["access_token"], 
                "token_type": "bearer",
                "user_id": str(user["id"]), # Ensure user_id is string
                "email": user["email"]
            }
        elif user and not session: # e.g. if email confirmation is required
             # For HERCULES, we might want to treat this as "pending" rather than raising 202 here,
             # depending on desired UX. For now, let's assume direct login or clear error.
             # If Supabase is set to require email confirmation, this path is important.
             # Let's assume for now that sign_up provides a session if successful.
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration completed but no session provided. Email confirmation might be pending.")
        else: 
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User registration failed, user or session not returned.")
    except ConnectionError as e: 
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Supabase connection error: {str(e)}")
    except HTTPException: 
        raise
    except Exception as e: 
        print(f"Unexpected error in /auth/register: {type(e).__name__} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during registration.")


@app.post("/auth/login", response_model=TokenResponse, summary="Login a user")
async def login_user_endpoint(form_data: UserLogin): 
    try:
        user, session, error = await login_user_in_supabase(form_data.email, form_data.password)
        if error:
            error_status_code = error.get("status_code", status.HTTP_401_UNAUTHORIZED)
            raise HTTPException(status_code=error_status_code, detail=error.get("message", "Login failed"))
        if user and session:
            return {
                "access_token": session["access_token"], 
                "token_type": "bearer",
                "user_id": str(user["id"]), # Ensure user_id is string
                "email": user["email"]
            }
        else: 
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password, or session not created.")
    except ConnectionError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Supabase connection error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in /auth/login: {type(e).__name__} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during login.")

# --- API Routes ---
@app.post("/api/tasks", response_model=RoomResponse, summary="Create a new task room (Protected)")
async def create_task_api_endpoint( 
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_active_user)
):
    user_id = current_user.get("id")
    # user_id from Supabase is typically a UUID object, convert to string if not already.
    user_id_str = str(user_id) 
    
    print(f"Task creation request from user: {user_id_str} for prompt: '{task_data.prompt}'")
    
    try:
        room_id, stored_metadata, error = await create_task_room(user_id=user_id_str, task_prompt=task_data.prompt)
        if error:
            error_status_code = error.get("status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
            raise HTTPException(status_code=error_status_code, detail=error.get("message", "Failed to create task room due to storage error"))
        
        if not room_id or not stored_metadata: # Should be caught by error above
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Task room creation failed to return necessary data.")

        return {
            "room_id": room_id, 
            "message": "Task room created and metadata stored successfully.",
            "details": stored_metadata 
        }
    except ConnectionError as e: 
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Supabase connection error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during task room creation endpoint: {type(e).__name__} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create task room: {str(e)}")


@app.get("/users/me", summary="Get current user details (Protected)")
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return current_user # current_user is already a dict from get_current_user
    
@app.get("/api/public_info", summary="Public information endpoint")
async def public_info():
    return {"message": "This endpoint is public."}

@app.on_event("startup")
async def startup_event():
    from app.room_manager import BASE_ROOMS_PATH
    BASE_ROOMS_PATH.mkdir(parents=True, exist_ok=True) 
    print(f"Ensured base room data directory exists: {BASE_ROOMS_PATH}")
    try:
        # This will attempt to initialize the client if env vars are present.
        # It doesn't raise an error here, but supabase_client.py prints warnings.
        get_supabase_admin_client() 
        print("Supabase admin client initialization attempted on startup.")
    except ConnectionError as e: # This will be caught if env vars are missing.
        print(f"Startup Warning: Supabase admin client not initialized. {e}")

@app.get("/api/rooms/{room_id}", response_model=RoomDetailsResponse, summary="Get details for a specific room (Protected)")
async def get_room_details_endpoint(
    room_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    user_id = current_user.get("id")
    if not user_id: # Should be caught by get_current_active_user, but defensive check
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User ID not found in token.")

    try:
        details, error = await get_room_details_from_supabase(room_id=room_id, user_id=str(user_id))
        
        if error:
            error_status_code = error.get("status_code", 500)
            raise HTTPException(status_code=error_status_code, detail=error.get("message", "Error fetching room details."))
        
        if not details: # Should ideally be covered by error above with 404
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found or access denied.")
            
        # Map Supabase response (details) to RoomDetailsResponse model
        # This assumes 'details' dict keys match RoomDetailsResponse fields.
        # If Supabase returns fields not in RoomDetailsResponse, they will be ignored by Pydantic.
        # If fields are missing, Pydantic will raise validation error unless they are Optional.
        return RoomDetailsResponse(**details)

    except ConnectionError as e: # If get_supabase_admin_client() in the called function fails
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Supabase connection error: {str(e)}")
    except HTTPException: # Re-raise HTTPExceptions from called functions or this one
        raise
    except Exception as e:
        print(f"Unexpected error in /api/rooms/{room_id}: {type(e).__name__} - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected server error occurred.")

# Removed __main__ block for uvicorn.run, as it's better handled by external process managers.
