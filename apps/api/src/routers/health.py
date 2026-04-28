"""Health check router with dependency validation."""

from __future__ import annotations

import time
from typing import Any, cast

import structlog
from fastapi import APIRouter

from src.cache.redis_client import get_redis
from src.database.supabase_client import get_supabase_client
from src.storage.minio_client import get_minio
from src.task_queues.rabbitmq_client import get_rabbitmq_connection

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Returns the health status of the API and its distributed dependencies.
    Used by Docker healthchecks and monitoring.
    """
    health: dict[str, Any] = {
        "status": "ok",
        "timestamp": time.time(),
        "services": {
            "database": "unknown",
            "redis": "unknown",
            "rabbitmq": "unknown",
            "storage": "unknown",
        },
    }

    # 1. Database (Critical)
    try:
        get_supabase_client().table("option_parameters").select("id").limit(1).execute()
        health["services"]["database"] = "connected"
    except Exception as error:
        health["services"]["database"] = f"error: {error!s}"
        health["status"] = "error"

    # 2. Redis (Cache/PubSub)
    try:
        redis = get_redis()
        if redis:
            await cast("Any", redis.ping())
            health["services"]["redis"] = "connected"
        else:
            health["services"]["redis"] = "disabled"
    except Exception as error:
        health["services"]["redis"] = f"unreachable: {error!s}"
        # We don't fail the whole app for Redis if it's just a cache/pubsub
        # especially during initialization on platforms like Render

    # 3. RabbitMQ (Task Queue)
    try:
        from src.config import get_settings

        if get_settings().rabbitmq_url:
            conn = await get_rabbitmq_connection()
            if not conn.is_closed:
                health["services"]["rabbitmq"] = "connected"
        else:
            health["services"]["rabbitmq"] = "disabled"
    except Exception as error:
        health["services"]["rabbitmq"] = f"unreachable: {error!s}"

    # 4. Storage (MinIO)
    try:
        client = get_minio()
        if client:
            client.list_buckets()
            health["services"]["storage"] = "connected"
        else:
            health["services"]["storage"] = "disabled"
    except Exception as error:
        health["services"]["storage"] = f"unreachable: {error!s}"

    return health
