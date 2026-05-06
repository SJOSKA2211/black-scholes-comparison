"""Unit tests for scrapers using robust Playwright mocking."""
from __future__ import annotations
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.scrapers.spy_scraper import SpyScraper
from src.scrapers.nse_next_scraper import NseScraper

class MockAsyncContextManager:
    def __init__(self, return_value):
        self.return_value = return_value
    async def __aenter__(self):
        return self.return_value
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_run() -> None:
    """Verify SpyScraper run logic with mocked playwright."""
    scraper = SpyScraper()
    
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.url = "https://finance.yahoo.com/quote/SPY/options"
    mock_page.locator.return_value.first.inner_text = AsyncMock(return_value="500.00")
    mock_page.locator.return_value.all = AsyncMock(return_value=[])
    
    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()
    
    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=MockAsyncContextManager(mock_playwright)):
        result = await scraper.run(date.today())
        assert result.status == "success"
        assert result.market == "spy"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_run() -> None:
    """Verify NseScraper run logic with mocked playwright."""
    scraper = NseScraper()
    
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.locator.return_value.all = AsyncMock(return_value=[])
    
    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()
    
    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=MockAsyncContextManager(mock_playwright)):
        result = await scraper.run(date.today())
        assert result.status == "success"
        assert result.market == "nse"
