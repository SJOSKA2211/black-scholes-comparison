"""Integration tests for Scrapers — zero-mock policy.
Hits live market sources (Yahoo Finance) to verify extraction logic still works.
"""

import pytest
from datetime import date
from src.scrapers.spy_scraper import SPYScraper

@pytest.mark.integration
@pytest.mark.asyncio
async def test_spy_scraper_live_fetch() -> None:
    """Verifies that SPYScraper can actually reach Yahoo and parse some data."""
    scraper = SPYScraper(run_id="test-live-spy")
    
    # We only fetch a small batch or just check connectivity
    data = await scraper.scrape(trade_date=date.today())
    
    # Validation
    assert isinstance(data, list)
    if len(data) > 0:
        row = data[0]
        assert "underlying_price" in row
        assert "strike_price" in row
        assert "bid_price" in row
        assert "ask_price" in row
        assert row["market_source"] == "spy"
        assert row["underlying_price"] > 0
    else:
        # If Yahoo is blocking or UI changed, this will fail, 
        # which is exactly what we want to know in integration tests.
        pytest.fail("Scraper returned zero rows from live source.")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_scraper_base_interface() -> None:
    """Verifies the base scraper interface methods."""
    scraper = SPYScraper(run_id="interface-test")
    assert scraper.run_id == "interface-test"
    assert hasattr(scraper, "scrape")
    assert hasattr(scraper, "run")
