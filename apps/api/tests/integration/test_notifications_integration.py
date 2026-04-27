import pytest
import uuid
from src.notifications.hierarchy import notify_user
from src.database.supabase_client import get_supabase_client
from src.cache.redis_client import get_redis

@pytest.mark.integration
class TestNotificationsIntegration:
    @pytest.mark.asyncio
    async def test_notify_user_real(self):
        """Zero-mock: test real notification flow."""
        user_id = "a24fb1a2-700a-4590-8d43-2930596a14f2"
        title = f"Integration Test {uuid.uuid4()}"
        body = "Testing zero-mock policy"
        
        # This will hit real Supabase (insert_notification) and real Redis (broadcast)
        # Note: If email/push are triggered, they will use real settings.
        # We use 'info' severity to avoid triggering external email APIs if possible,
        # or we accept that it might attempt to send (and fail gracefully if no API key).
        
        await notify_user(user_id, title, body, severity="info")
        
        # Verify in Supabase
        supabase = get_supabase_client()
        res = supabase.table("notifications").select("*").eq("user_id", user_id).execute()
        assert len(res.data) == 1
        assert res.data[0]["title"] == title

    @pytest.mark.asyncio
    async def test_notify_user_critical_graceful_fail(self):
        """Zero-mock: test critical severity which triggers email, ensuring it fails gracefully if no API key."""
        user_id = "a24fb1a2-700a-4590-8d43-2930596a14f2"
        # This will attempt to send email via Resend. 
        # If RESEND_API_KEY is missing, it returns False but shouldn't crash the whole flow
        # unless we specifically raise.
        await notify_user(user_id, "Critical", "Body", severity="critical")
        
        supabase = get_supabase_client()
        res = supabase.table("notifications").select("*").eq("user_id", user_id).execute()
        assert len(res.data) == 1

    @pytest.mark.asyncio
    async def test_push_notification_no_subs(self):
        """Zero-mock: test push notification with no subscriptions."""
        from src.notifications.push import send_push_notification
        user_id = str(uuid.uuid4())
        result = await send_push_notification(user_id, "T", "B")
        assert result is False
