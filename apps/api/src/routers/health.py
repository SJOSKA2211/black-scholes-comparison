"""Health check router for API and infrastructure status."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter

from src.cache.redis_client import get_redis
from src.database.supabase_client import get_supabase

router = APIRouter(tags=["ops"])
logger = structlog.get_logger(__name__)


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Check connectivity to all backend services."""
    services: dict[str, str] = {}
    overall_status = "ok"

    # 1. Database
    try:
        # Pydantic/Supabase types might be tricky, we just want to know if it executes
        get_supabase().table("option_parameters").select("id").limit(1).execute()
        services["supabase"] = "connected"
    except Exception as e:
        overall_status = "error"
        services["supabase"] = f"error: {e!s}"

    # 2. Redis
    try:
        redis = get_redis()
        await redis.ping()
        services["redis"] = "connected"
    except Exception as e:
        overall_status = "error"
        services["redis"] = f"error: {e!s}"

    status = {"status": overall_status, "services": services}
    logger.info("health_check_performed", status=overall_status)
    return status
