# hercules/backend/app/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
# Use the actual get_user_by_token function
from .supabase_client import get_user_by_token, get_supabase_admin_client # Added get_supabase_admin_client for check

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") # Updated tokenUrl to actual planned login

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Check if Supabase client is initialized, though get_user_by_token will also raise error
        get_supabase_admin_client() 
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Supabase client not initialized: {str(e)}. Check server configuration.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_token(token)
    if not user or not user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials or user not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Ensure user object is returned, not a Supabase specific UserResponse object if any.
    # get_user_by_token in supabase_client.py should already return a dict.
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    # Add any active status checks if available in your user model from Supabase
    # For example, if Supabase adds an 'is_active' field or similar via custom claims or metadata.
    # if not current_user.get("is_active", True): # Assuming active if not specified
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user
