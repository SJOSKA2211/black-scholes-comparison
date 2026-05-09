"""Unit tests for notifications module."""
from __future__ import annotations
import pytest
from src.notifications.hierarchy import NotificationSeverity, NotificationChannel
from src.notifications.email import send_email_notification
from src.notifications.push import send_push_notification
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.unit
def test_notification_enums() -> None:
    """Verify notification enums."""
    assert NotificationSeverity.INFO == "info"
    assert NotificationChannel.EMAIL == "email"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_email_mock() -> None:
    """Verify email sending logic with mocks."""
    with patch("src.notifications.email.get_settings") as mock_settings:
        mock_settings.return_value.resend_api_key = "test_key"
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            mock_post.return_value.raise_for_status = MagicMock()
            await send_email_notification("test@example.com", "Subject", "Body")
            assert mock_post.called

@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_push_mock() -> None:
    """Verify push notification logic with mocks."""
    # Placeholder push logic verification
    await send_push_notification("user-123", "Title", "Body")
    # Currently just logs, so we just ensure no crash
