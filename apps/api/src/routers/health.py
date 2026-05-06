"""API router for health checks."""

from __future__ import annotations

import structlog
from fastapi import APIRouter

from src.database.supabase_client import get_supabase

router = APIRouter(prefix="/api/v1/health", tags=["health"])
logger = structlog.get_logger(__name__)


@router.get("/")
async def health_check() -> dict[str, str]:
    """Check API and database health."""
    health_status = {"status": "ok", "db": "disconnected"}

    try:
        # Simple query to check DB connection
        get_supabase().table("option_parameters").select("id").limit(1).execute()
        health_status["db"] = "connected"
    except Exception as error:
        logger.error("health_check_failed", error=str(error))

    return health_status
