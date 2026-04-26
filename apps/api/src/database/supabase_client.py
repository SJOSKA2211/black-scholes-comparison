from functools import lru_cache

from supabase import Client, create_client

from src.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    """Returns a singleton Supabase client using service_role key."""
    settings = get_settings()
    url = settings.supabase_url
    key = settings.supabase_key
    if not url or url == "None" or not key or key == "dummy_service_key":
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set.")
    return create_client(url, key)
