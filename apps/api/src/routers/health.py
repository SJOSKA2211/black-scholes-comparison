"""Health check router for API and infrastructure status."""

from __future__ import annotations

import structlog
from fastapi import APIRouter

from src.cache.redis_client import get_redis
from src.database.supabase_client import get_supabase

router = APIRouter(tags=["ops"])
logger = structlog.get_logger(__name__)


@router.get("/health")
async def health_check() -> dict:
    """Check connectivity to all backend services."""
    status = {"status": "ok", "services": {}}

    # 1. Database
    try:
        get_supabase().table("option_parameters").select("id", count="exact").limit(1).execute()
        status["services"]["supabase"] = "connected"
    except Exception as e:
        status["status"] = "error"
        status["services"]["supabase"] = f"error: {e!s}"

    # 2. Redis
    try:
        redis = get_redis()
        await redis.ping()
        status["services"]["redis"] = "connected"
    except Exception as e:
        status["status"] = "error"
        status["services"]["redis"] = f"error: {e!s}"

    logger.info("health_check_performed", status=status["status"])
    return status
