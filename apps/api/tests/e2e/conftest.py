import os

import pytest
from playwright.sync_api import BrowserContext, Page


@pytest.fixture
def base_url() -> str:
    return os.getenv("E2E_BASE_URL", "http://127.0.0.1:3000")


@pytest.fixture
def api_url() -> str:
    return os.getenv("E2E_API_URL", "http://127.0.0.1:8000")


@pytest.fixture
def authenticated_page(page: Page, context: BrowserContext, base_url: str) -> Page:
    """Fixture to provide a page on the dashboard."""
    try:
        # Navigate and wait for the page to be ready (longer timeout for Next.js compilation)
        page.goto(f"{base_url}/", wait_until="networkidle", timeout=30000)
        # Wait for sidebar
        page.wait_for_selector("aside", timeout=30000)
    except Exception as e:
        page.screenshot(path="dashboard_load_failure.png")
        pytest.fail(f"Dashboard failed to load at {base_url}: {str(e)}")

    return page
