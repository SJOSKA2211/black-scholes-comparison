"""Unit tests for additional notifications router coverage."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


@pytest.mark.unit
class TestNotificationsRouterCoverage:
    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.notifications.get_notifications")
    def test_get_notifications_exception(self, mock_get, mock_get_supabase) -> None:
        """Test exception handling in get_user_notifications."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "researcher"}]
        )

        mock_get.side_effect = Exception("DB error")

        response = client.get("/api/v1/notifications/", headers={"Authorization": "Bearer token"})
        assert response.status_code == 500
        assert "Failed to fetch notifications" in response.json()["detail"]

    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.notifications.mark_notification_read")
    def test_acknowledge_notification_exception(self, mock_mark, mock_get_supabase) -> None:
        """Test exception handling in acknowledge_notification."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_user = MagicMock()
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "researcher"}]
        )

        mock_mark.side_effect = Exception("Update error")

        response = client.patch(
            "/api/v1/notifications/notif-1/read", headers={"Authorization": "Bearer token"}
        )
        assert response.status_code == 500
        assert "Failed to update notification" in response.json()["detail"]

    @patch("src.auth.dependencies.get_supabase_client")
    @patch("src.routers.notifications.mark_all_notifications_read")
    def test_acknowledge_all_notifications_exception(
        self, mock_mark_all, mock_get_supabase
    ) -> None:
        """Test exception handling in acknowledge_all_notifications."""
        mock_supabase = MagicMock()
        mock_get_supabase.return_value = mock_supabase
        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_supabase.auth.get_user.return_value = MagicMock(user=mock_user)
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"role": "researcher"}]
        )

        mock_mark_all.side_effect = Exception("Bulk update error")

        response = client.post(
            "/api/v1/notifications/read-all", headers={"Authorization": "Bearer token"}
        )
        assert response.status_code == 500
        assert "Failed to update all notifications" in response.json()["detail"]
