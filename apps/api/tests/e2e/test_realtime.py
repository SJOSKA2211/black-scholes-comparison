import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_realtime_notifications(page: Page) -> None:
    """Verify real-time notification updates in the UI (Section 16.3)."""
    base_url = "http://localhost:3000"
    page.goto(f"{base_url}/")
    
    # Check for notification bell
    # The UI uses a bell icon, usually with a button
    bell = page.get_by_role("button", name="Notifications")
    expect(bell).to_be_visible()
    
    # Check for "Connected" badge (Realtime status)
    # The RealtimeBadge component shows "Connected" in green
    expect(page.get_by_text("Connected")).to_be_visible()
    
    # Trigger a notification from the backend
    from src.database.repository import insert_notification
    # Use a known test user ID or fetch from context
    user_id = "de34e0d4-ad52-4ffe-9f75-1d41c83a4fb2" 
    
    await insert_notification(
        user_id=user_id,
        title="E2E Test Notification",
        body="This is a real-time test.",
        severity="info",
        channel="notifications"
    )
    
    # Verify that a notification toast or badge appears
    # Toast usually has the title
    expect(page.get_by_text("E2E Test Notification")).to_be_visible()
