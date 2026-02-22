import logging
from typing import Optional

from fastapi import Header, HTTPException

from database_service import get_supabase_client

logger = logging.getLogger("AttendX.Auth")

async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Extract user from Authorization header.
    Returns user object or raises HTTPException.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        if not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Invalid Authorization header format")

        token = authorization.split(" ", 1)[1]
        client = get_supabase_client()
        user = client.auth.get_user(token)
        
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        return user.user
    except Exception as e:
        logger.warning("Authentication failed: %s", e)
        raise HTTPException(status_code=401, detail="Authentication failed")

async def require_auth(authorization: Optional[str] = Header(None)):
    """
    Dependency for routes that require authentication.
    Usage: user = Depends(require_auth)
    """
    return await get_current_user(authorization)
