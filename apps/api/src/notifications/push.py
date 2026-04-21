import json

import structlog
from pywebpush import WebPushException, webpush

from src.config import settings
from src.database import repository

logger = structlog.get_logger(__name__)


async def send_push(notification) -> bool:
    """
    Dispatches a browser push notification via Web Push API.
    Fetches the user's active push subscriptions and sends the payload.
    """
    # Note: VAPID keys should be in .env. We fall back to a log warning if missing.
    vapid_private_key = getattr(settings, "vapid_private_key", None)
    vapid_claims = {"sub": "mailto:admin@black-scholes.example.com"}

    if not vapid_private_key:
        logger.warning("push_skip_no_vapid_key", user_id=notification.user_id)
        # We return True to not break the hierarchy dispatch, but log the skip.
        return True

    try:
        # Fetch subscriptions for this user
        subscriptions = await repository.get_push_subscriptions(notification.user_id)

        payload = {
            "title": notification.title,
            "body": notification.body,
            "url": notification.action_url or "/",
            "severity": notification.severity,
        }

        results = []
        for sub in subscriptions:
            try:
                webpush(
                    subscription_info=sub["subscription_info"],
                    data=json.dumps(payload),
                    vapid_private_key=vapid_private_key,
                    vapid_claims=vapid_claims,
                )
                results.append(True)
            except WebPushException as ex:
                # If subscription is expired/invalid, we should remove it
                if ex.response and ex.response.status_code in [404, 410]:
                    await repository.delete_push_subscription(sub["id"])
                results.append(False)

        logger.info(
            "push_dispatch_completed",
            user_id=notification.user_id,
            successful=results.count(True),
            failed=results.count(False),
        )
        return any(results)

    except Exception as e:
        logger.error("push_system_error", error=str(e), user_id=notification.user_id)
        return False
