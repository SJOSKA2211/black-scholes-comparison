import structlog
from dataclasses import dataclass
from typing import Literal, Optional
from src.database import repository
from src.notifications.email import send_email
from src.notifications.push import send_push
from datadog import statsd

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
    and the user's notification_preferences.
    """

    async def dispatch(self, notification: Notification) -> None:
        # In a real app, we'd fetch preferences from user_profiles table
        # prefs = await repository.get_user_preferences(notification.user_id)
        prefs = {"email": True, "push": True} 

        # Always persist to notifications table -> Supabase Realtime pushes it to the UI
        await repository.insert_notification(
            user_id=notification.user_id,
            title=notification.title,
            body=notification.body,
            severity=notification.severity,
            channel="in_app",
            action_url=notification.action_url,
        )

        # Route to external channels based on severity
        if notification.severity in ("warning", "error", "critical"):
            if prefs.get("email", True):
                await send_email(notification)

        if notification.severity in ("error", "critical"):
            if prefs.get("push", True):
                await send_push(notification)

        # Critical alerts go to Datadog as well
        if notification.severity == "critical":
            statsd.event(
                notification.title,
                notification.body,
                alert_type="error",
                tags=["env:production", f"severity:{notification.severity}"],
            )

        statsd.increment("black_scholes.notification_sent",
            tags=[f"channel:in_app", f"severity:{notification.severity}"])
        
        logger.info("notification_dispatched",
            user_id=notification.user_id, severity=notification.severity)
