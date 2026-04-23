"""Email notification delivery via Resend."""

from __future__ import annotations

import resend
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

        resend.api_key = settings.resend_api_key

        # Note: Resend.Emails.send is synchronous in 0.8.0,
        # so we run it in a thread pool for production async safety
        import asyncio
        from functools import partial

        email_params = {
            "from": "Black-Scholes Platform <notifications@black-scholes.example.com>",
            "to": [to_email],
            "subject": subject,
            "html": body,
        }

        from typing import Any, cast

        loop = asyncio.get_event_loop()
        send_fn = partial(resend.Emails.send, cast("Any", email_params))
        response = await loop.run_in_executor(None, send_fn)

        logger.info(
            "email_sent",
            to=to_email,
            subject=subject,
            response_id=getattr(response, "id", "unknown"),
        )
        return True
    except Exception as error:
        logger.error("email_failed", to=to_email, error=str(error))
        return False
