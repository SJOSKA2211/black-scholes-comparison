import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_dashboard_navigation(authenticated_page: Page, base_url: str) -> None:
    """Verify dashboard layout and navigation (Section 16.3)."""
    page = authenticated_page
    page.goto(f"{base_url}/")

    # Wait for page hydration
    page.wait_for_selector("aside", timeout=10000)

    # Check sidebar/nav items and click them
    nav_items = ["Live Pricer", "Experiments", "Validation", "Scrapers", "Methods"]
    for item in nav_items:
        link = page.get_by_role("link", name=item)
        expect(link).to_be_visible()
        link.click()
        # Verify URL path contains the lower-cased item name
        path = item.lower().replace(" ", "")
        if path == "livepricer":
            path = "pricer"
        page.wait_for_url(f"**/{path}*", timeout=10000)


@pytest.mark.e2e
def test_live_pricer_interactivity(authenticated_page: Page, base_url: str) -> None:
    """Verify Live Pricer inputs and chart rendering."""
    page = authenticated_page
    page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
    page.goto(f"{base_url}/pricer")

    # Wait for sidebar to confirm login success and hydration
    page.wait_for_selector("aside", timeout=10000)

    # Wait for the main content to be visible
    page.wait_for_selector("input", timeout=10000)

    # Check for inputs
    expect(page.get_by_label("Underlying Price")).to_be_visible()
    expect(page.get_by_label("Strike Price")).to_be_visible()

    # Interact with input
    page.get_by_label("Underlying Price").fill("150")
    page.get_by_label("Underlying Price").press("Enter")
    expect(page.get_by_label("Underlying Price")).to_have_value("150")

    # Check for chart container
    # Recharts uses an SVG container.
    page.wait_for_selector("svg", timeout=20000)
    expect(page.locator("svg").first).to_be_visible()

    # Wait for computation results to appear in the list
    page.wait_for_selector("p:text('analytical')", timeout=20000)

    # Verify chart bars
    bars = page.locator(".recharts-bar-rectangle")
    count = bars.count()
    print(f"Detected {count} bars in chart")
    assert count >= 10
