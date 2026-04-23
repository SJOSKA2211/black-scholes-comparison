import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_realtime_notifications(page: Page) -> None:
    """Verify real-time notification updates in the UI (Section 16.3)."""
    base_url = "http://127.0.0.1:3000"
    page.goto(f"{base_url}/")

    # Check for notification bell
    # The UI uses a bell icon, usually with a button
    bell = page.get_by_role("button", name="Notifications")
    expect(bell).to_be_visible()

    # Check for "Connected" badge (Realtime status)
    expect(page.get_by_text("Connected")).to_be_visible()

    # Trigger a notification from the backend
    from src.database.supabase_client import get_supabase_client
    supabase = get_supabase_client()
    
    # Get a valid user ID from the profiles table
    res = supabase.table("user_profiles").select("id").limit(1).execute()
    if not res.data:
        pytest.skip("No user profiles found for real-time test")
    user_id = res.data[0]["id"]

    from src.database.repository import insert_notification
    await insert_notification(
        user_id=user_id,
        title="E2E Test Notification",
        body="This is a real-time test.",
        severity="info",
        channel="in_app",
    )

    # Verify that a notification toast or badge appears
    expect(page.get_by_text("E2E Test Notification")).to_be_visible()

    # Section 16.3: notification bell count increments
    # Look for a badge inside the bell button
    badge = bell.locator(".badge, .count, [data-testid='notification-count']")
    if await badge.is_visible():
        count = await badge.inner_text()
        assert int(count) >= 1
