from src.notifications.hierarchy import Notification
import structlog

logger = structlog.get_logger(__name__)

async def send_push(notification: Notification) -> None:
    """Send browser push notification via Web Push API."""
    # Placeholder for web-push implementation
    logger.info("push_sent_placeholder", 
                user_id=notification.user_id, 
                title=notification.title)
    pass
