"""Pytest configuration and fixtures."""

import asyncio

import pytest

from src.cache.redis_client import get_redis
from src.config import get_settings
from src.database.supabase_client import get_supabase
from src.main import app
from fastapi.testclient import TestClient


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


@pytest.fixture
def sample_option_params() -> dict:
    """Standard option parameters for testing."""
    return {
        "underlying_price": 100.0,
        "strike_price": 100.0,
        "maturity_years": 1.0,
        "volatility": 0.2,
        "risk_free_rate": 0.05,
        "option_type": "call",
        "is_american": False,
    }


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Session-scoped FastAPI test client."""
    return TestClient(app)
