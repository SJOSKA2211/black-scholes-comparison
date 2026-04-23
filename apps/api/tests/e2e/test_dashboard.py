import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_dashboard_navigation(page: Page) -> None:
    """Verify dashboard layout and navigation (Section 16.3)."""
    # Assuming we can skip auth for testing UI or use a mock session
    base_url = "http://localhost:3000"
    page.goto(f"{base_url}/")

    # Check sidebar/nav items
    expect(page.get_by_role("link", name="Pricer")).to_be_visible()
    expect(page.get_by_role("link", name="Experiments")).to_be_visible()
    expect(page.get_by_role("link", name="Validation")).to_be_visible()
    expect(page.get_by_role("link", name="Scrapers")).to_be_visible()
    expect(page.get_by_role("link", name="Methods")).to_be_visible()


@pytest.mark.e2e
def test_live_pricer_interactivity(page: Page) -> None:
    """Verify Live Pricer inputs and chart rendering."""
    base_url = "http://localhost:3000"
    # In a real E2E run, we'd need to handle auth or have a dev bypass
    page.goto(f"{base_url}/pricer")

    # Check for inputs
    expect(page.get_by_label("Underlying Price")).to_be_visible()
    expect(page.get_by_label("Strike Price")).to_be_visible()
    expect(page.get_by_label("Maturity (Years)")).to_be_visible()
    expect(page.get_by_label("Volatility (σ)")).to_be_visible()

    # Interact with input and verify update
    page.get_by_label("Underlying Price").fill("150")
    # Underlying Price input value should be updated
    expect(page.get_by_label("Underlying Price")).to_have_value("150")

    # Check for chart container (usually a div with a specific class or child canvas)
    # The frontend uses Recharts usually, which renders SVG
    expect(page.locator("svg.recharts-surface")).to_be_visible()
