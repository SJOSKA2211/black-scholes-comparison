import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_dashboard_navigation(authenticated_page: Page, base_url: str) -> None:
    """Verify dashboard layout and navigation (Section 16.3)."""
    page = authenticated_page
    # Assuming we can skip auth for testing UI or use a mock session
    page.goto(f"{base_url}/")

    # Check sidebar/nav items and click them
    nav_items = ["Live Pricer", "Experiments", "Validation", "Scrapers", "Methods"]
    for item in nav_items:
        link = page.get_by_role("link", name=item)
        expect(link).to_be_visible()
        link.click()
        # Verify URL path contains the lower-cased item name
        path = item.lower().replace(" ", "")
        if path == "livepricer": path = "pricer"
        page.wait_for_url(f"**/{path}*")


@pytest.mark.e2e
def test_live_pricer_interactivity(authenticated_page: Page, base_url: str) -> None:
    """Verify Live Pricer inputs and chart rendering."""
    page = authenticated_page
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

    # Check for chart container
    # Recharts uses .recharts-surface for the SVG
    expect(page.locator(".recharts-surface").first).to_be_visible(timeout=10000)

    # Section 16.3: all 12 method bars in chart
    bars = page.locator(".recharts-bar-rectangle")
    # Wait for computation and animation
    page.wait_for_timeout(2000)
    expect(bars).to_have_count(12, timeout=10000)
