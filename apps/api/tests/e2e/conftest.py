import pytest
from playwright.sync_api import Page, BrowserContext

@pytest.fixture
def authenticated_page(page: Page, context: BrowserContext) -> Page:
    """Fixture to provide a page on the dashboard."""
    try:
        # Navigate and wait for the page to be ready (longer timeout for Next.js compilation)
        page.goto("http://localhost:3000/", wait_until="networkidle", timeout=30000)
        # Wait for sidebar
        page.wait_for_selector("aside", timeout=30000)
    except Exception as e:
        page.screenshot(path="dashboard_load_failure.png")
        pytest.fail(f"Dashboard failed to load: {str(e)}")
        
    return page
