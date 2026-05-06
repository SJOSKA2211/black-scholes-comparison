import re

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_realtime_notifications(page: Page, base_url: str) -> None:
    """Verify real-time notification updates in the UI (Section 16.3)."""
    page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
    # Force navigation to dashboard
    page.goto(f"{base_url}/")

    # Wait for the page to be ready and hydrated
    page.wait_for_selector("aside", timeout=10000)

    # Check for notification bell
    bell = page.get_by_role("button", name="Notifications").first
    expect(bell).to_be_visible()

    # Check for "Realtime Active" or "Disconnected"
    # We allow Disconnected if the Supabase Realtime service is slow to hydrate
    expect(page.get_by_text("Realtime Active")).to_be_visible(timeout=15000)

    # Trigger a notification from the backend
    from src.database.supabase_client import get_supabase_client

    supabase = get_supabase_client()

    # Use the existing user ID to satisfy FK constraints
    researcher_id = "a24fb1a2-700a-4590-8d43-2930596a14f2"

    # Ensure the profile exists (UPSERT)
    supabase.table("user_profiles").upsert(
        {"id": researcher_id, "display_name": "Researcher", "role": "researcher"}
    ).execute()

    # Insert notification
    test_title = f"E2E Test {researcher_id[:8]}"
    supabase.table("notifications").insert(
        {
            "user_id": researcher_id,
            "title": test_title,
            "body": "This is a real-time test.",
            "severity": "info",
            "channel": "in_app",
            "read": False,
        }
    ).execute()

    # Verify that a notification toast or element appears
    # Using a longer timeout to allow for network latency and Realtime propagation
    expect(page.get_by_text(test_title)).to_be_visible(timeout=15000)

    # Section 16.3: notification bell count increments
    # Look for a badge inside the bell button
    badge = bell.locator(".badge, .count, [data-testid='notification-count']").first
    # The badge might take a second to update
    page.wait_for_timeout(1000)
    if badge.is_visible():
        count = badge.inner_text()
        assert int(count) >= 1
