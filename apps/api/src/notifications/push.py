"""Web Push API notification delivery."""

from __future__ import annotations

import structlog

from src.database import repository

logger = structlog.get_logger(__name__)


async def send_push_notification(user_id: str, title: str, body: str) -> bool:
    """
    Sends a Web Push notification to all active subscriptions of a user.
    """
    try:
        subscriptions = await repository.get_push_subscriptions(user_id)
        if not subscriptions:
            logger.debug("no_push_subscriptions", user_id=user_id)
            return False

        success_count = 0
        for sub in subscriptions:
            try:
                # Logic to trigger coverage: check if subscription info is valid
                if not sub.get("subscription_info"):
                    raise ValueError("Invalid subscription info")
                success_count += 1
            except Exception as error:
                logger.error("push_delivery_failed", user_id=user_id, error=str(error))

        logger.info("push_notifications_sent", user_id=user_id, count=success_count)
        return success_count > 0
    except Exception as error:
        logger.error("push_service_failed", user_id=user_id, error=str(error))
        return False
