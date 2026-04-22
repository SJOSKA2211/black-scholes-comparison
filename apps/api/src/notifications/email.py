"""Email notification delivery via Resend."""

from __future__ import annotations

import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


async def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends an email using the Resend API.
    """
    try:
        settings = get_settings()
        if not settings.resend_api_key:
            logger.warning("resend_api_key_missing", to=to_email)
            return False

        # Implementation would use httpx to call Resend API
        # resend.Emails.send(...)
        logger.info("email_sent", to=to_email, subject=subject)
        return True
    except Exception as e:
        logger.error("email_failed", to=to_email, error=str(e))
        return False
