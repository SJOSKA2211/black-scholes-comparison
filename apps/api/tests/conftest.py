import asyncio
import os
from collections.abc import Generator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from minio import Minio

# Load environment variables (Section 1.2)
load_dotenv()

from src.cache.redis_client import get_redis
from src.database.supabase_client import get_supabase_client
from src.main import app
from src.storage.minio_client import get_minio
from src.task_queues.rabbitmq_client import get_rabbitmq_connection
from src.config import get_settings

def _patch_env_for_host() -> None:
    """If running on host (not in docker), map docker hostnames to localhost."""
    is_docker = os.path.exists("/.dockerenv")
    if not is_docker:
        # Import inside to avoid circular deps
        from src.config import get_settings
        from src.storage.minio_client import get_minio
        from src.cache.redis_client import get_redis
        
        settings = get_settings()
        # Redis
        if "redis:6379" in settings.redis_url:
            os.environ["REDIS_URL"] = settings.redis_url.replace("redis:6379", "127.0.0.1:6379")
        # MinIO
        if settings.minio_endpoint == "minio:9000":
            os.environ["MINIO_ENDPOINT"] = "127.0.0.1:9000"
        # RabbitMQ
        if "rabbitmq:5672" in settings.rabbitmq_url:
            os.environ["RABBITMQ_URL"] = settings.rabbitmq_url.replace("rabbitmq:5672", "127.0.0.1:5672")
        
        # Reload settings and clients if already cached
        get_settings.cache_clear()
        get_minio.cache_clear()
        get_redis.cache_clear()

_patch_env_for_host()


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Session-scoped test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture(scope="session")
def supabase():
    """Session-scoped Supabase client."""
    return get_supabase_client()


@pytest.fixture(scope="session")
def redis():
    """Session-scoped Redis client."""
    return get_redis()


@pytest_asyncio.fixture(scope="session")
async def rabbitmq():
    """Session-scoped RabbitMQ connection."""
    connection = await get_rabbitmq_connection()
    yield connection
    await connection.close()


@pytest.fixture(scope="session")
def minio_client() -> Minio:
    """Session-scoped MinIO client."""
    return get_minio()


@pytest.fixture
def auth_headers():
    """Default auth headers for authorized requests."""
    return {"Authorization": "Bearer fake-jwt-token"}


@pytest.fixture
def sample_option_params():
    """Standard option parameters for testing."""
    return {
        "underlying_price": 100.0,
        "strike_price": 100.0,
        "maturity_years": 1.0,
        "volatility": 0.2,
        "risk_free_rate": 0.05,
        "option_type": "call",
        "market_source": "synthetic",
        "is_american": False,
    }


@pytest.fixture(autouse=True)
def skip_if_no_infrastructure(request) -> None:
    """Skip integration and E2E tests if infrastructure is not available."""
    if "integration" in request.keywords or "e2e" in request.keywords:
        # Check for Supabase
        if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"):
            pytest.skip("SUPABASE_URL or SUPABASE_KEY not set")

        # Specific checks for Redis/RabbitMQ/MinIO if the test is marked with those
        # We check if we can actually connect or if the env is set
        if "redis" in request.keywords and not os.getenv("REDIS_URL"):
            # If not in env, check if it's default and we are on host
            if not os.path.exists("/.dockerenv"):
                pass # Already patched in _patch_env_for_host
            else:
                pytest.skip("REDIS_URL not set for redis-dependent test")

        if "minio" in request.keywords:
            endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
            if "minio" in endpoint and os.getenv("ENVIRONMENT") != "production":
                # Likely docker hostname, skip if not in docker
                import socket

                try:
                    socket.gethostbyname("minio")
                except socket.gaierror:
                    pytest.skip("MinIO host not resolvable")
