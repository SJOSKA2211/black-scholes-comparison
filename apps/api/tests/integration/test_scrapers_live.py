"""Integration tests for live scrapers (SPY and NSE)."""
from __future__ import annotations
from datetime import date
import pytest
from src.scrapers.spy_scraper import SpyScraper
from src.scrapers.nse_next_scraper import NseScraper

@pytest.mark.integration
@pytest.mark.asyncio
async def test_spy_scraper_live() -> None:
    """Verify SpyScraper can fetch real data from Yahoo Finance."""
    scraper = SpyScraper()
    # Use today's date or a recent one
    result = await scraper.run(date.today())
    
    assert result.status == "success"
    assert result.market == "spy"
    # Ensure we actually got some data
    assert len(result.quotes) > 0
    assert result.quotes[0].underlying_symbol == "SPY"
    assert result.quotes[0].data_source == "spy"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_nse_scraper_live() -> None:
    """Verify NseScraper can fetch real data from NSE Kenya."""
    scraper = NseScraper()
    result = await scraper.run(date.today())
    
    # NSE might be empty on weekends, but we check if the scraper ran successfully
    assert result.status in ["success", "partial"]
    assert result.market == "nse"
    if result.status == "success":
        assert len(result.quotes) > 0
