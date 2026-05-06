"""Email notification service using Resend."""

from __future__ import annotations

import httpx
import structlog

from src.config import get_settings

logger = structlog.get_logger(__name__)


async def send_email_notification(recipient: str, subject: str, body: str) -> None:
    """Send an email using Resend API."""
    settings = get_settings()
    if not settings.resend_api_key:
        logger.warning("resend_api_key_not_set", recipient=recipient)
        return

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": "Black-Scholes Research <notifications@black-scholes.example.com>",
        "to": [recipient],
        "subject": subject,
        "html": body,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            logger.info("email_sent", recipient=recipient, subject=subject)
        except Exception as error:
            logger.error("email_send_failed", recipient=recipient, error=str(error))
            raise
