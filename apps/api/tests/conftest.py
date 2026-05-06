import asyncio
import os
from collections.abc import Generator
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from minio import Minio

# Load environment variables
load_dotenv()

def _patch_env_for_host() -> None:
    """If running on host (not in docker), map docker hostnames to localhost."""
    is_docker = os.path.exists("/.dockerenv")
    if not is_docker:
        # Redis
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        if "redis:6379" in redis_url:
            os.environ["REDIS_URL"] = redis_url.replace("redis:6379", "127.0.0.1:6379")
        # MinIO
        minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
        if minio_endpoint == "minio:9000":
            os.environ["MINIO_ENDPOINT"] = "127.0.0.1:9000"
        # RabbitMQ
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://rabbitmq_user:guest@rabbitmq:5672/")
        if "rabbitmq:5672" in rabbitmq_url:
            os.environ["RABBITMQ_URL"] = rabbitmq_url.replace("rabbitmq:5672", "127.0.0.1:5672")

_patch_env_for_host()

from src.cache.redis_client import get_redis, reset_redis
from src.config import get_settings
from src.database.supabase_client import get_supabase
from src.main import app
from src.storage.minio_client import get_minio
from src.queue.rabbitmq_client import get_rabbitmq_connection

@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.get_event_loop_policy()

@pytest.fixture(scope="session")
def client() -> TestClient:
    """Session-scoped test client."""
    return TestClient(app)

@pytest.fixture(scope="session")
def supabase():
    """Session-scoped Supabase client."""
    return get_supabase()

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
