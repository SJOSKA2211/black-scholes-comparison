import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_scrapers_interactivity(authenticated_page: Page, base_url: str) -> None:
    """Verify Scrapers page and job triggering (Section 16.3)."""
    page = authenticated_page
    page.goto(f"{base_url}/scrapers")

    # Wait for page hydration
    page.wait_for_selector("aside", timeout=10000)

    # Check for scraper cards
    expect(page.get_by_text("SPY Scraper")).to_be_visible()
    expect(page.get_by_text("NSE Scraper")).to_be_visible()

    # Trigger a scrape
    spy_card = page.locator("div:has-text('SPY Scraper')").first
    run_btn = spy_card.get_by_role("button", name="Run Now")
    expect(run_btn).to_be_visible()

    # Click run
    run_btn.click()

    # Verify status change to "Running" or a toast appearing
    # Based on the mandate, we should see a "Job queued" toast
    expect(page.get_by_text("Scrape job queued")).to_be_visible(timeout=10000)
