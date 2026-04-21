from supabase import create_client, Client
from src.config import get_settings
from functools import lru_cache

@lru_cache()
def get_supabase_client() -> Client:
    """Returns a singleton Supabase client using service_role key."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)
