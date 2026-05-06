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
    
    mock_browser = AsyncMock()
    mock_page = AsyncMock()
    
    # mock_page.locator("...").all() is async
    mock_locator = MagicMock()
    mock_locator.all = AsyncMock(return_value=[])
    mock_page.locator.return_value = mock_locator
    
    # Properly mock async context manager for playwright
    mock_pw_context = AsyncMock()
    mock_pw_context.__aenter__.return_value = AsyncMock()
    mock_pw_context.__aenter__.return_value.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=mock_pw_context):
        result = await scraper.run(date(2025, 1, 1))
        
        assert result.market == "nse"
        assert result.status == "success"
        mock_page.goto.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_run() -> None:
    """Verify SPY scraper execution logic."""
    scraper = SpyScraper()
    
    mock_browser = AsyncMock()
    mock_page = AsyncMock()
    
    # Mock underlying price locator
    mock_underlying_locator = AsyncMock()
    mock_underlying_locator.first.inner_text.return_value = "500.00"
    
    # Mock call rows locator
    mock_rows_locator = MagicMock()
    mock_rows_locator.all = AsyncMock(return_value=[])
    
    def side_effect(selector):
        if "regularMarketPrice" in selector:
            return mock_underlying_locator
        return mock_rows_locator
        
    mock_page.locator.side_effect = side_effect
    
    # Properly mock async context manager for playwright
    mock_pw_context = AsyncMock()
    mock_pw_context.__aenter__.return_value = AsyncMock()
    mock_pw_context.__aenter__.return_value.chromium.launch.return_value = mock_browser
    mock_browser.new_page.return_value = mock_page
    
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=mock_pw_context):
        result = await scraper.run(date(2025, 1, 1))
        
        assert result.market == "spy"
        assert result.status == "success"
        mock_page.goto.assert_called_once()
