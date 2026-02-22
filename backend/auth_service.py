from fastapi import Header, HTTPException
from typing import Optional
from database_service import get_supabase_client

async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Extract user from Authorization header.
    Returns user object or raises HTTPException.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        token = authorization.split(" ")[1]
        client = get_supabase_client()
        user = client.auth.get_user(token)
        
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        return user.user
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Auth error: {str(e)}")

async def require_auth(authorization: Optional[str] = Header(None)):
    """
    Dependency for routes that require authentication.
    Usage: user = Depends(require_auth)
    """
    return await get_current_user(authorization)
