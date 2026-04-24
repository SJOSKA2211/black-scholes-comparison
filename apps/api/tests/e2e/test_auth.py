import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_dashboard_accessibility(page: Page) -> None:
    """Verify that the dashboard is directly accessible (Auth Stripped)."""
    page.goto("http://localhost:3000/")
    
    # Check that we are on the dashboard (Sidebar and Header present)
    expect(page.locator("aside")).to_be_visible()
    expect(page.get_by_role("heading", name="Live Research Activity")).to_be_visible()
    
    # Verify the mock researcher user is displayed
    expect(page.get_by_text("Researcher")).to_be_visible()
