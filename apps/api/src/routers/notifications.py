from fastapi import APIRouter, Depends
from typing import List
from src.database import repository
from src.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/notifications")
async def get_notifications(
    unread_only: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Returns notifications for current user."""
    # This would call repo.get_notifications_by_user
    return []

@router.patch("/notifications/{id}/read")
async def mark_notification_read(
    id: str,
    current_user: dict = Depends(get_current_user)
):
    """Marks a notification as read."""
    # This would call repo.mark_notification_read
    return {"status": "ok"}
