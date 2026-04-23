import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_login_page_ui(page: Page) -> None:
    """Verify login page elements and animations (Section 16.3)."""
    # Use BASE_URL from env if available, default to localhost:3000
    base_url = "http://127.0.0.1:3000"
    page.goto(f"{base_url}/login")

    # Check title and buttons
    expect(page.get_by_role("heading", name="Research Platform")).to_be_visible()
    expect(page.get_by_text("Numerical methods for option pricing")).to_be_visible()
    expect(page.get_by_role("button", name="GitHub")).to_be_visible()
    expect(page.get_by_role("button", name="Google")).to_be_visible()
    expect(page.get_by_placeholder("Enter your email")).to_be_visible()

    # Test OAuth navigation
    # Note: We don't complete the login as it requires real credentials
    page.get_by_role("button", name="GitHub").click()
    page.wait_for_url("**/github.com/**", timeout=10000)
    assert "github.com" in page.url
