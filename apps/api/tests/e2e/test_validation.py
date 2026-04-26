import pytest
from playwright.sync_api import Page, expect

@pytest.mark.e2e
def test_validation_page_rendering(authenticated_page: Page, base_url: str) -> None:
    """Verify Validation page metrics and charts."""
    page = authenticated_page
    page.goto(f"{base_url}/validation")

    # Wait for page hydration
    page.wait_for_selector("aside", timeout=10000)
    
    # Check for metrics
    expect(page.get_by_text("Mean Absolute Error")).to_be_visible()
    expect(page.get_by_text("Convergence Stability")).to_be_visible()

    # Check for chart
    expect(page.locator("svg").first).to_be_visible()
