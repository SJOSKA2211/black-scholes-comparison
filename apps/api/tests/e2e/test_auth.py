import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_login_page_load(page: Page) -> None:
    # This requires the frontend to be running and reachable
    # In CI, we use a placeholder or local mock if needed, but mandate says
    # "Playwright browser tests against running stack"
    page.goto("http://localhost:3000/login")
    expect(page.get_by_text("Black-Scholes Research Platform")).to_be_visible()
    expect(page.get_by_role("button", name="GitHub")).to_be_visible()
    expect(page.get_by_role("button", name="Google")).to_be_visible()
