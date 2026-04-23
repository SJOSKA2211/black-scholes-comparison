"""Health check router with dependency validation."""

from __future__ import annotations

import time
from typing import Any, cast

import structlog
from fastapi import APIRouter

from src.cache.redis_client import get_redis
from src.database.supabase_client import get_supabase_client
from src.task_queues.rabbitmq_client import get_rabbitmq_connection
from src.storage.minio_client import get_minio

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

    # 1. Database
    try:
        get_supabase_client().table("option_parameters").select("id").limit(1).execute()
        health["services"]["database"] = "connected"
    except Exception as error:
        health["services"]["database"] = f"error: {error!s}"
        health["status"] = "error"

    # 2. Redis
    try:
        redis = get_redis()
        await cast("Any", redis.ping())
        health["services"]["redis"] = "connected"
    except Exception as error:
        health["services"]["redis"] = f"error: {error!s}"
        health["status"] = "error"

    # 3. RabbitMQ
    try:
        conn = await get_rabbitmq_connection()
        if not conn.is_closed:
            health["services"]["rabbitmq"] = "connected"
    except Exception as error:
        health["services"]["rabbitmq"] = f"error: {error!s}"
        health["status"] = "error"

    # 4. Storage (MinIO)
    try:
        get_minio().list_buckets()
        health["services"]["storage"] = "connected"
    except Exception as error:
        health["services"]["storage"] = f"error: {error!s}"
        health["status"] = "error"

    return health
