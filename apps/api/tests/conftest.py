"""Pytest configuration and fixtures."""

import asyncio

import pytest

from src.cache.redis_client import get_redis
from src.config import get_settings
from src.database.supabase_client import get_supabase


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def supabase_client():
    """Session-scoped Supabase client."""
    return get_supabase()


@pytest.fixture(scope="session")
async def redis_client():
    """Session-scoped Redis client."""
    client = get_redis()
    yield client
    await client.close()
