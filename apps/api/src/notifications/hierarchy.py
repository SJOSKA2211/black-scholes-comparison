from dataclasses import dataclass
from typing import Literal, Optional

import structlog

from src.database import repository
from src.metrics import NOTIFICATIONS_SENT_TOTAL
from src.notifications.email import send_email
from src.notifications.push import send_push

Severity = Literal["info", "warning", "error", "critical"]
logger = structlog.get_logger(__name__)


@dataclass
class Notification:
    user_id: str
    title: str
    body: str
    severity: Severity
    action_url: Optional[str] = None


class NotificationRouter:
    """
    Routes notifications to the correct channels based on severity
    and the user's notification_preferences. Persists every notification
    to the notifications table so in-app feed is always available.
    """

    async def dispatch(self, notification: Notification) -> None:
        # Get user preferences
        profile = await repository.get_user_profile(notification.user_id)
        prefs = profile.get("notification_preferences", {}) if profile else {}

        # Always persist to notifications table (In-App)
        # This triggers Supabase Realtime for the frontend
        await repository.insert_notification(
            user_id=notification.user_id,
            title=notification.title,
            body=notification.body,
            severity=notification.severity,
            channel="in_app",
            action_url=notification.action_url,
        )
        NOTIFICATIONS_SENT_TOTAL.labels(
            channel="in_app", severity=notification.severity
        ).inc()

        # Route to other channels based on severity
        if notification.severity in ("warning", "error", "critical"):
            if prefs.get("email", True):
                await send_email(notification)
                NOTIFICATIONS_SENT_TOTAL.labels(
                    channel="email", severity=notification.severity
                ).inc()

        if notification.severity in ("error", "critical"):
            if prefs.get("push", True):
                await send_push(notification)
                NOTIFICATIONS_SENT_TOTAL.labels(
                    channel="push", severity=notification.severity
                ).inc()

        logger.info(
            "notification_dispatched",
            user_id=notification.user_id,
            severity=notification.severity,
        )
