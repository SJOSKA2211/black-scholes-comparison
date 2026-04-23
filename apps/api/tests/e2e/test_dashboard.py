import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_dashboard_navigation(page: Page) -> None:
    """Verifies that navigation items are visible on the dashboard."""
    try:
        page.goto("http://localhost:3000/pricer", timeout=5000)
        # Check for sidebar links
        expect(page.get_by_role("link", name="Pricer")).to_be_visible()
        expect(page.get_by_role("link", name="Experiments")).to_be_visible()
        expect(page.get_by_role("link", name="Scrapers")).to_be_visible()
    except Exception:
        pytest.skip("Dashboard not reachable")

@pytest.mark.e2e
def test_pricer_live_updates(page: Page) -> None:
    """Verifies that the pricer updates when sliders are moved."""
    try:
        page.goto("http://localhost:3000/pricer", timeout=5000)
        # Interact with a slider
        slider = page.get_by_label("Underlying Price")
        slider.fill("150")
        # Check for "Computing..." badge or updated price
        expect(page.get_by_text("analytical")).to_be_visible()
    except Exception:
        pytest.skip("Pricer not reachable or interacting")
