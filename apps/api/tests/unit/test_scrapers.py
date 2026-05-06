"""Unit tests for market data scrapers."""
from __future__ import annotations
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from src.scrapers.nse_next_scraper import NseScraper
from src.scrapers.spy_scraper import SpyScraper

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_run() -> None:
    """Verify NSE scraper execution logic."""
    scraper = NseScraper()
    
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.close = AsyncMock()
    
    mock_locator = MagicMock()
    mock_locator.all = AsyncMock(return_value=[])
    mock_page.locator = MagicMock(return_value=mock_locator)
    
    mock_browser = MagicMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_browser.close = AsyncMock()
    
    mock_playwright = MagicMock()
    mock_playwright.chromium = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    
    # Mock the async context manager
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_playwright)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=mock_cm):
        result = await scraper.run(date(2025, 1, 1))
        assert result.market == "nse"
        assert result.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_run() -> None:
    """Verify SPY scraper execution logic."""
    scraper = SpyScraper()
    
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.close = AsyncMock()
    
    mock_underlying_locator = MagicMock()
    mock_underlying_locator.first = MagicMock()
    mock_underlying_locator.first.inner_text = AsyncMock(return_value="500.00")
    
    mock_rows_locator = MagicMock()
    mock_rows_locator.all = AsyncMock(return_value=[])
    
    def side_effect(selector):
        if "regularMarketPrice" in selector:
            return mock_underlying_locator
        return mock_rows_locator
    mock_page.locator = MagicMock(side_effect=side_effect)
    
    mock_browser = MagicMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_browser.close = AsyncMock()
    
    mock_playwright = MagicMock()
    mock_playwright.chromium = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_playwright)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=mock_cm):
        result = await scraper.run(date(2025, 1, 1))
        assert result.market == "spy"
        assert result.status == "success"
