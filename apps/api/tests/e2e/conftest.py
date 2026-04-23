import pytest
from playwright.sync_api import Page, BrowserContext

@pytest.fixture
def authenticated_page(page: Page, context: BrowserContext) -> Page:
    """Fixture to provide an authenticated page via dev bypass."""
    try:
        # Go to dashboard directly (bypassed via SKIP_AUTH=true in .env.local)
        page.goto("http://localhost:3000/")
        
        # Wait for sidebar
        page.wait_for_selector("aside", timeout=15000)
        
    except Exception as e:
        page.screenshot(path="auth_failure.png")
        pytest.fail(f"Auth fixture failed (bypass mode): {str(e)}")
        
    return page
