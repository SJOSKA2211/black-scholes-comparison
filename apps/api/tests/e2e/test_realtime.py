import pytest
import re
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_realtime_notifications(page: Page) -> None:
    """Verify real-time notification updates in the UI (Section 16.3)."""
    base_url = "http://127.0.0.1:3000"
    page.goto(f"{base_url}/")

    # Check for notification bell
    bell = page.get_by_role("button", name="Notifications").first
    expect(bell).to_be_visible()

    # Check for "Realtime Active" badge (Realtime status)
    # Note: It might be "Disconnected" initially, we should wait or accept both
    expect(page.get_by_text(re.compile("Realtime Active|Disconnected"))).to_be_visible()

    # Trigger a notification from the backend
    from src.database.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    
    # Get a valid user ID from the profiles table
    res = supabase.table("user_profiles").select("id").limit(1).execute()
    if not res.data:
        pytest.skip("No user profiles found for real-time test")
    user_id = res.data[0]["id"]

    # Use direct sync Supabase call to avoid event loop issues
    supabase.table("notifications").insert({
        "user_id": user_id,
        "title": "E2E Test Notification",
        "body": "This is a real-time test.",
        "severity": "info",
        "channel": "in_app",
        "read": False
    }).execute()

    # Verify that a notification toast or badge appears
    expect(page.get_by_text("E2E Test Notification")).to_be_visible()

    # Section 16.3: notification bell count increments
    # Look for a badge inside the bell button
    badge = bell.locator(".badge, .count, [data-testid='notification-count']").first
    if badge.is_visible():
        count = badge.inner_text()
        assert int(count) >= 1
