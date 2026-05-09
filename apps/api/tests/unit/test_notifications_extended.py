"""Unit tests for email notifications."""
from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.notifications.email import send_email_notification

@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_email_success():
    with patch("src.notifications.email.get_settings") as s, \
         patch("httpx.AsyncClient.post") as m:
        s().resend_api_key = "key"
        m.return_value = MagicMock(status_code=200)
        await send_email_notification("r", "s", "b")

@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_email_no_key():
    with patch("src.notifications.email.get_settings") as s:
        s().resend_api_key = None
        await send_email_notification("r", "s", "b")

@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_email_fail():
    with patch("src.notifications.email.get_settings") as s, \
         patch("httpx.AsyncClient.post") as m:
        s().resend_api_key = "key"
        m.side_effect = Exception("err")
        with pytest.raises(Exception):
            await send_email_notification("r", "s", "b")
