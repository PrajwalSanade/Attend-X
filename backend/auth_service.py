from flask import request, jsonify
from functools import wraps
from database_service import get_supabase_client

def get_current_user():
    """
    Extract user from Authorization header.
    Returns: (user_object, error_message)
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        # Fallback: check if 'admin_id' is in body (less secure but helps if frontend fails auth header)
        # But for 'Security Improvements: Use JWT', we should enforce token.
        # However, for 'verify_face' called by student, they might not have admin token.
        # Students have their own token? Maybe.
        return None, "Missing Authorization header"

    try:
        token = auth_header.split(" ")[1]
        client = get_supabase_client()
        user = client.auth.get_user(token)
        
        if not user or not user.user:
            return None, "Invalid token"
            
        return user.user, None
    except Exception as e:
        return None, f"Auth error: {str(e)}"

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user, error = get_current_user()
        if error:
            return jsonify({"success": False, "message": error}), 401
        
        # Store user in request context for route to use
        request.user = user
        return f(*args, **kwargs)
    return decorated
