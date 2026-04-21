import resend
from src.config import get_settings
from src.notifications.hierarchy import Notification
import structlog

logger = structlog.get_logger(__name__)

TEMPLATES = {
    "info":    {"from": "research@black-scholes.example.com", "subject_prefix": "[Info]"},
    "warning": {"from": "research@black-scholes.example.com", "subject_prefix": "[Warning]"},
    "error":   {"from": "research@black-scholes.example.com", "subject_prefix": "[Action Required]"},
    "critical":{"from": "research@black-scholes.example.com", "subject_prefix": "[CRITICAL]"},
}

async def send_email(notification: Notification) -> None:
    """Send transactional email via Resend."""
    settings = get_settings()
    if not settings.resend_api_key:
        logger.warning("email_skip", reason="RESEND_API_KEY not set")
        return

    resend.api_key = settings.resend_api_key
    template = TEMPLATES.get(notification.severity, TEMPLATES["info"])
    
    # In a real app, we'd fetch the user's email from user_profiles
    user_email = "joseph@example.com" # Placeholder
    
    try:
        resend.Emails.send({
            "from": template["from"],
            "to": [user_email],
            "subject": f"{template['subject_prefix']} {notification.title}",
            "html": f"<p>{notification.body}</p>" +
                    (f'<p><a href="{notification.action_url}">View details</a></p>'
                     if notification.action_url else ""),
        })
    except Exception as e:
        logger.error("email_failed", error=str(e), user_id=notification.user_id)
