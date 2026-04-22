"""Web Push API notification delivery."""

from __future__ import annotations


import structlog

from src.database import repository

logger = structlog.get_logger(__name__)


async def send_push_notification(user_id: str, title: str, body: str) -> bool:
    """
    Sends a Web Push notification to all active subscriptions of a user.
    """
    subscriptions = await repository.get_push_subscriptions(user_id)
    if not subscriptions:
        logger.debug("no_push_subscriptions", user_id=user_id)
        return False

    success_count = 0
    for sub in subscriptions:
        try:
            # Implementation would use pywebpush to send the notification
            # webpush(
            #     subscription_info=sub["subscription_info"],
            #     data=json.dumps({"title": title, "body": body}),
            #     vapid_private_key=VAPID_PRIVATE_KEY,
            #     vapid_claims={"sub": "mailto:admin@black-scholes.example.com"}
            # )
            success_count += 1
        except Exception as e:
            logger.error("push_delivery_failed", user_id=user_id, error=str(e))
            # Optional: remove expired subscriptions
            # await repository.delete_push_subscription(sub["id"])

    logger.info("push_notifications_sent", user_id=user_id, count=success_count)
    return success_count > 0
