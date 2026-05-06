"""Debug router for inspecting environment and connectivity on cloud platforms."""

import os
import socket
from typing import Any

import structlog
from fastapi import APIRouter, Request

from src.config import get_settings

router = APIRouter(tags=["debug"])
logger = structlog.get_logger(__name__)


@router.get("/api/v1/debug/env")
async def debug_env(request: Request) -> dict[str, Any]:
    """Inspect allowed environment variables and request metadata."""
    settings = get_settings()

    # We only show keys, not values for sensitive ones,
    # but for debugging we might show some non-sensitive values.
    env_info = {
        "ENVIRONMENT": settings.environment,
        "RAILWAY_STATIC_URL": os.getenv("RAILWAY_STATIC_URL"),
        "RAILWAY_SERVICE_NAME": os.getenv("RAILWAY_SERVICE_NAME"),
        "PORT": os.getenv("PORT"),
        "HOSTNAME": socket.gethostname(),
    }

    headers = dict(request.headers)
    # Hide sensitive headers
    if "authorization" in headers:
        headers["authorization"] = "REDACTED"
    if "cookie" in headers:
        headers["cookie"] = "REDACTED"

    logger.info(
        "debug_env_accessed", client_host=request.client.host if request.client else "unknown"
    )

    return {
        "env": env_info,
        "headers": headers,
        "settings_summary": {
            "redis_enabled": settings.redis_enabled,
            "rabbitmq_enabled": settings.rabbitmq_enabled,
            "minio_enabled": settings.minio_enabled,
            "redis_host": settings.redis_host,
            "minio_endpoint": settings.minio_endpoint,
        },
    }


@router.get("/api/v1/debug/dns/{host}")
async def debug_dns(host: str) -> dict[str, Any]:
    """Debug DNS resolution for internal services."""
    try:
        ip_addr = socket.gethostbyname(host)
        return {"host": host, "status": "resolved", "ip": ip_addr}
    except Exception as e:
        logger.error("dns_resolution_failed", host=host, error=str(e))
        return {"host": host, "status": "failed", "error": str(e)}


@router.get("/api/v1/debug/health")
async def debug_health() -> dict[str, Any]:
    """Test all core infrastructure services and return detailed status."""
    results = {}

    # 1. Redis
    try:
        from src.cache.redis_client import get_redis

        redis = get_redis()
        if redis:
            await redis.ping()
            results["redis"] = "healthy"
        else:
            results["redis"] = "disabled"
    except Exception as e:
        logger.error("debug_health_redis_failed", error=str(e))
        results["redis"] = f"error: {str(e)}"

    # 2. RabbitMQ
    try:
        from src.task_queues.rabbitmq_client import get_rabbitmq_connection

        settings = get_settings()
        if settings.rabbitmq_enabled:
            conn = await get_rabbitmq_connection()
            if not conn.is_closed:
                results["rabbitmq"] = "healthy"
            else:
                results["rabbitmq"] = "closed"
        else:
            results["rabbitmq"] = "disabled"
    except Exception as e:
        logger.error("debug_health_rabbitmq_failed", error=str(e))
        results["rabbitmq"] = f"error: {str(e)}"

    # 3. MinIO
    try:
        from src.storage.minio_client import get_minio

        minio = get_minio()
        if minio:
            minio.list_buckets()
            results["minio"] = "healthy"
        else:
            results["minio"] = "disabled"
    except Exception as e:
        logger.error("debug_health_minio_failed", error=str(e))
        results["minio"] = f"error: {str(e)}"

    # 4. Supabase
    try:
        from src.database.supabase_client import get_supabase_client

        supabase = get_supabase_client()
        # Simple query
        supabase.table("option_parameters").select("id").limit(1).execute()
        results["supabase"] = "healthy"
    except Exception as e:
        logger.error("debug_health_supabase_failed", error=str(e))
        results["supabase"] = f"error: {str(e)}"

    return results
