import logging
from typing import Optional

from fastapi import Header, HTTPException

from database_service import get_supabase_client

logger = logging.getLogger("AttendX.Auth")


def _raise_auth(status_code: int, error_code: str, message: str):
    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "error_code": error_code, "message": message},
    )


async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Extract user from Authorization header.
    Returns user object or raises HTTPException.
    """
    if not authorization:
        _raise_auth(401, "AUTH_REQUIRED", "Authentication token required.")

    try:
        if not authorization.lower().startswith("bearer "):
            _raise_auth(401, "INVALID_TOKEN", "Invalid authentication token.")

        token = authorization.split(" ", 1)[1].strip()
        if not token:
            _raise_auth(401, "AUTH_REQUIRED", "Authentication token required.")

        client = get_supabase_client()
        user = client.auth.get_user(token)

        if not user or not user.user:
            if "expired" in token.lower():
                _raise_auth(401, "TOKEN_EXPIRED", "Session expired. Please login again.")
            _raise_auth(401, "INVALID_TOKEN", "Invalid authentication token.")

        return user.user
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Authentication failed: %s", exc)
        if "expired" in str(exc).lower():
            _raise_auth(401, "TOKEN_EXPIRED", "Session expired. Please login again.")
        _raise_auth(401, "INVALID_TOKEN", "Invalid authentication token.")

async def require_auth(authorization: Optional[str] = Header(None)):
    """
    Dependency for routes that require authentication.
    Usage: user = Depends(require_auth)
    """
    return await get_current_user(authorization)


async def require_admin(authorization: Optional[str] = Header(None)):
    current_user = await get_current_user(authorization)
    client = get_supabase_client()
    admin_res = client.table("admins").select("id").eq("user_id", current_user.id).limit(1).execute()
    if not admin_res.data:
        _raise_auth(403, "ACCESS_DENIED", "Unauthorized access.")
    return current_user
