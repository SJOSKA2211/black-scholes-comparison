"""Notification hierarchy and delivery orchestration."""

from __future__ import annotations

import json

import structlog

from src.cache.redis_client import get_redis
from src.database.repository import insert_notification
from src.metrics import NOTIFICATIONS_SENT_TOTAL
from src.notifications.email import send_email
from src.notifications.push import send_push_notification

logger = structlog.get_logger(__name__)


async def notify_user(
    user_id: str,
    title: str,
    body: str,
    severity: str = "info",
    channel: str = "in_app",
    action_url: str | None = None,
) -> None:
    """
    Orchestrates notification delivery across multiple tiers.
    """
    try:
        # 1. In-app notification (DB) - Always persistent
        await insert_notification(
            user_id=user_id,
            title=title,
            body=body,
            severity=severity,
            channel=channel,
            action_url=action_url,
        )

        # 2. WebSocket Push (Pub/Sub) - Always real-time
        redis = get_redis()
        await redis.publish(
            "ws:notifications",
            json.dumps(
                {"user_id": str(user_id), "title": title, "body": body, "severity": severity}
            ),
        )

        # 3. Channel specific delivery
        if channel == "email" or severity in ["error", "critical"]:
            # Assume user has email if we are to send email
            # In a real app, we'd fetch user email from DB/Auth
            # For this prototype, we'll assume a placeholder if not provided
            await send_email("placeholder@example.com", title, body)
            NOTIFICATIONS_SENT_TOTAL.labels(channel="email", severity=severity).inc()

        if channel == "push":
            await send_push_notification(str(user_id), title, body)
            NOTIFICATIONS_SENT_TOTAL.labels(channel="push", severity=severity).inc()

        NOTIFICATIONS_SENT_TOTAL.labels(channel="in_app", severity=severity).inc()
        logger.info("notification_dispatched", user_id=user_id, severity=severity, channel=channel)

    except Exception as e:
        logger.error("notification_dispatch_failed", error=str(e), user_id=user_id)
        raise  # Raise so caller knows it failed
