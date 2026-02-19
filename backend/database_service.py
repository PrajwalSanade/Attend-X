import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Defaults from frontend/supabaseClient.js
DEFAULT_URL = "https://wmcviykvnzmmaikunvmf.supabase.co"
# Note: Ideally this should be a service role key for backend operations
DEFAULT_KEY = "sb_publishable_pOG_ctG7m9lFwYZbGYY4bg_T9ycUHiN"

url: str = os.environ.get("SUPABASE_URL", DEFAULT_URL)
key: str = os.environ.get("SUPABASE_KEY", DEFAULT_KEY)

_client = None

def get_supabase_client(access_token=None) -> Client:
    """
    Get Supabase client.
    If access_token is provided, auth header is set to access RLS protected data.
    """
    global _client
    if _client is None:
        _client = create_client(url, key)
    
    # Create a new client or clone if we need to set auth
    # For simplicity in this context, we re-create if token provided to ensure isolation
    if access_token:
        # For per-request auth, it is safer to create a fresh client or use postgrest.auth
        # However, create_client is lightweight.
        client = create_client(url, key)
        client.postgrest.auth(access_token)
        return client
    
    return _client
