"""API router for notifications."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Depends
from src.auth.dependencies import get_current_user
from src.database.repository import get_notifications, mark_notification_read
import structlog

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])
logger = structlog.get_logger(__name__)

@router.get("/")
async def list_notifications(
    current_user: dict[str, Any] = Depends(get_current_user)
) -> list[dict[str, Any]]:
    """List notifications for the current user."""
    user_id = str(current_user.get("id", ""))
    if not user_id:
        return []
    return await get_notifications(user_id)

@router.patch("/{notification_id}/read")
async def read_notification(
    notification_id: str,
    current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, str]:
    """Mark a notification as read."""
    await mark_notification_read(notification_id)
    return {"status": "success"}
