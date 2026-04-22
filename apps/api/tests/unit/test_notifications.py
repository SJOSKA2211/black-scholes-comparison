import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.notifications.hierarchy import notify_user
from src.notifications.email import send_email
from src.notifications.push import send_push_notification
import uuid

@pytest.mark.unit
class TestNotifications:
    @pytest.mark.asyncio
    @patch("src.notifications.hierarchy.insert_notification")
    @patch("src.notifications.hierarchy.get_redis")
    @patch("src.notifications.hierarchy.send_email")
    @patch("src.notifications.hierarchy.send_push_notification")
    async def test_notify_user_hierarchy_success(self, mock_push, mock_email, mock_redis, mock_insert):
        mock_r = MagicMock()
        mock_r.publish = AsyncMock()
        mock_redis.return_value = mock_r
        
        user_id = str(uuid.uuid4())
        
        await notify_user(user_id, "Title", "Body", severity="error", channel="email")
        mock_insert.assert_called_once()
        mock_r.publish.assert_called_once()
        mock_email.assert_called_once()
            
        await notify_user(user_id, "Title", "Body", severity="info", channel="push")
        assert mock_push.call_count == 1

    @pytest.mark.asyncio
    @patch("src.notifications.hierarchy.insert_notification")
    async def test_notify_user_hierarchy_failure(self, mock_insert):
        mock_insert.side_effect = Exception("DB Fail")
        with pytest.raises(Exception, match="DB Fail"):
            await notify_user("user-123", "T", "B")

    @pytest.mark.asyncio
    @patch("src.notifications.email.get_settings")
    async def test_email_service_success(self, mock_settings):
        mock_settings.return_value.resend_api_key = "key-123"
        res = await send_email("test@example.com", "Subject", "Content")
        assert res is True

    @pytest.mark.asyncio
    @patch("src.notifications.email.get_settings")
    async def test_email_service_no_key(self, mock_settings):
        mock_settings.return_value.resend_api_key = None
        res = await send_email("test@example.com", "Subject", "Content")
        assert res is False

    @pytest.mark.asyncio
    @patch("src.notifications.email.get_settings")
    async def test_email_service_failure(self, mock_settings):
        mock_settings.side_effect = Exception("Config error")
        res = await send_email("test@example.com", "S", "B")
        assert res is False

    @pytest.mark.asyncio
    @patch("src.notifications.push.repository")
    async def test_push_service_success(self, mock_repo):
        mock_repo.get_push_subscriptions = AsyncMock(return_value=[{"id": 1, "subscription_info": {"endpoint": "..."}}])
        res = await send_push_notification("user-123", "Title", "Body")
        assert res is True

    @pytest.mark.asyncio
    @patch("src.notifications.push.repository")
    async def test_push_service_partial_failure(self, mock_repo):
        # One valid, one invalid subscription_info
        mock_repo.get_push_subscriptions = AsyncMock(return_value=[
            {"id": 1, "subscription_info": {"endpoint": "..."}},
            {"id": 2, "subscription_info": None}
        ])
        res = await send_push_notification("user-123", "Title", "Body")
        assert res is True # Still true because one succeeded

    @pytest.mark.asyncio
    @patch("src.notifications.push.repository")
    async def test_push_service_no_subs(self, mock_repo):
        mock_repo.get_push_subscriptions = AsyncMock(return_value=[])
        res = await send_push_notification("user-123", "Title", "Body")
        assert res is False
        
    @pytest.mark.asyncio
    @patch("src.notifications.push.repository")
    async def test_push_service_failure(self, mock_repo):
        mock_repo.get_push_subscriptions = AsyncMock(side_effect=Exception("Repo Fail"))
        res = await send_push_notification("user-123", "T", "B")
        assert res is False
