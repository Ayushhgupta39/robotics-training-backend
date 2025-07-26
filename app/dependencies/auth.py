from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.clerk_auth import clerk_auth
from typing import Optional

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Extract and validate user ID from Clerk JWT token
    """
    try:
        token = credentials.credentials
        user_id = clerk_auth.get_user_id(token)
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[str]:
    """
    Extract user ID from token if present, return None if not authenticated
    Useful for endpoints that can work with or without authentication
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        user_id = clerk_auth.get_user_id(token)
        return user_id
    except:
        return None
