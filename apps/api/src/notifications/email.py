import resend
import structlog

from src.config import settings

logger = structlog.get_logger(__name__)

if settings.resend_api_key:
    resend.api_key = settings.resend_api_key


async def send_email(notification) -> bool:
    """
    Sends a transactional email via Resend.
    """
    if not settings.resend_api_key:
        logger.warning("email_skip_no_api_key", user_id=notification.user_id)
        return False

    try:
        # In a real app, we'd fetch the user's email from the profile
        # For this research platform, we assume it's available in the notification object
        # or we fetch it from Supabase here.

        # Simplified for demonstration:
        recipient = "researcher@example.com"  # Should be dynamic

        r = resend.Emails.send(
            {
                "from": "Black-Scholes Platform <notifications@black-scholes.example.com>",
                "to": [recipient],
                "subject": f"[{notification.severity.upper()}] {notification.title}",
                "html": f"<p>{notification.body}</p>",
            }
        )

        logger.info(
            "email_sent",
            user_id=notification.user_id,
            email_id=r["id"],
            severity=notification.severity,
        )
        return True

    except Exception as e:
        logger.error("email_failed", error=str(e), user_id=notification.user_id)
        return False
