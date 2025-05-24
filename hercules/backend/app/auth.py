from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
# Assuming supabase_client.py is in the same directory or adjust import
from .supabase_client import get_user_by_token # Placeholder function

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Placeholder tokenUrl

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # In a real scenario, you would validate the token with Supabase
    # and fetch the user details.
    # For now, we use our placeholder function.
    user = await get_user_by_token(token)
    if not user or not user.get("id"): # Check if user is None or id is missing
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    # If you have user activation status, you can check it here.
    # For now, just returns the user.
    # if not current_user.get("is_active"): # Example check
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
