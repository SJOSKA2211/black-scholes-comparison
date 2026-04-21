from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user
from src.database import repository

router = APIRouter()


@router.get("/notifications")
async def get_notifications(
    unread_only: bool = True, current_user: dict = Depends(get_current_user)
):
    """Returns notifications for current user."""
    return await repository.get_notifications(
        current_user["id"], unread_only=unread_only
    )


@router.patch("/notifications/{id}/read")
async def mark_notification_read(
    id: str, current_user: dict = Depends(get_current_user)
):
    """Marks a notification as read."""
    await repository.mark_notification_read(id)
    return {"status": "ok"}


@router.delete("/notifications/read-all")
async def mark_all_notifications_read(current_user: dict = Depends(get_current_user)):
    """Marks all user notifications as read."""
    await repository.mark_all_notifications_read(current_user["id"])
    return {"status": "ok"}
