"""Router for managing user notifications."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query

from src.auth.dependencies import get_current_user
from src.database.repository import (
    get_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.get("/")
async def get_user_notifications(
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Retrieves notifications for the current user."""
    try:
        notifications = await get_notifications(
            user_id=current_user["id"], limit=limit, unread_only=unread_only
        )
        return notifications
    except Exception as e:
        logger.error(
            "notifications_fetch_failed", error=str(e), user_id=current_user["id"], step="router"
        )
        raise HTTPException(status_code=500, detail="Failed to fetch notifications") from e


@router.patch("/{notification_id}/read")
async def acknowledge_notification(
    notification_id: str, current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, str]:
    """Marks a notification as read."""
    try:
        await mark_notification_read(notification_id)
        return {"message": "Notification marked as read"}
    except Exception as e:
        logger.error("notification_update_failed", error=str(e), id=notification_id, step="router")
        raise HTTPException(status_code=500, detail="Failed to update notification") from e


@router.post("/read-all")
async def acknowledge_all_notifications(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    """Marks all notifications for the current user as read."""
    try:
        await mark_all_notifications_read(current_user["id"])
        return {"message": "All notifications marked as read"}
    except Exception as e:
        logger.error(
            "notifications_bulk_update_failed",
            error=str(e),
            user_id=current_user["id"],
            step="router",
        )
        raise HTTPException(status_code=500, detail="Failed to update all notifications") from e
