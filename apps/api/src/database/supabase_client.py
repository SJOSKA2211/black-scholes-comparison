"""Supabase client singleton."""

from __future__ import annotations

from functools import lru_cache

import structlog
from supabase import Client, create_client

from src.config import get_settings

logger = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Return a cached Supabase client."""
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_key)
    logger.info("supabase_client_created", url=settings.supabase_url, step="init")
    return client
