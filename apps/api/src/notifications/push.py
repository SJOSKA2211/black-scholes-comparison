"""Push notification service."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


async def send_push_notification(user_id: str, title: str, body: str) -> None:
    """Send a web push notification."""
    # Placeholder for Web Push API implementation
    logger.info("push_notification_triggered", user_id=user_id, title=title)
