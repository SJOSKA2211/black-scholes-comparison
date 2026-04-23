import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_dashboard_navigation(authenticated_page: Page) -> None:
    """Verify dashboard layout and navigation (Section 16.3)."""
    page = authenticated_page
    # Assuming we can skip auth for testing UI or use a mock session
    base_url = "http://localhost:3000"
    page.goto(f"{base_url}/")

    # Check sidebar/nav items
    expect(page.get_by_role("link", name="Live Pricer")).to_be_visible()
    expect(page.get_by_role("link", name="Experiments")).to_be_visible()
    expect(page.get_by_role("link", name="Validation")).to_be_visible()
    expect(page.get_by_role("link", name="Scrapers")).to_be_visible()
    expect(page.get_by_role("link", name="Methods")).to_be_visible()


@pytest.mark.e2e
def test_live_pricer_interactivity(authenticated_page: Page) -> None:
    """Verify Live Pricer inputs and chart rendering."""
    page = authenticated_page
    base_url = "http://localhost:3000"
    # In a real E2E run, we'd need to handle auth or have a dev bypass
    page.goto(f"{base_url}/pricer")
    
    # Reload to apply session
    page.reload()
    
    # Wait for sidebar to confirm login success
    page.wait_for_selector("aside", timeout=10000)

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

    # Section 16.3: all 12 method bars in chart
    # We can check for the number of rectangles (bars) in the chart
    # Or check for the legend/labels if available
    bars = page.locator("svg.recharts-surface .recharts-bar-rectangle")
    # Note: In initial load, there might be 0 until a calculation is run.
    # But the mandate says "after slider change... all 12 method bars in chart"
    # So we might need to wait for calculation.
    page.wait_for_timeout(2000)
    expect(bars).to_have_count(12)
