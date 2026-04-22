from functools import lru_cache

from supabase import Client, create_client

from src.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    """Returns a singleton Supabase client using service_role key."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)
