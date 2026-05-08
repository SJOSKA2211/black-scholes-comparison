"""Unit tests for scrapers with high coverage and robust mocking."""
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

@pytest.fixture
def mock_playwright():
    """Mock playwright object with nested mocks."""
    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.url = "https://finance.yahoo.com/quote/SPY/options"
    
    # Mock locator chain
    mock_locator = MagicMock()
    mock_locator.first = MagicMock()
    mock_locator.first.inner_text = AsyncMock(return_value="500.00")
    mock_locator.first.wait_for = AsyncMock()
    mock_locator.all = AsyncMock(return_value=[])
    mock_page.locator.return_value = mock_locator
    mock_page.get_by_role.return_value.click = AsyncMock()
    
    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_browser.close = AsyncMock()
    
    mock_p = MagicMock()
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
    return mock_p

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_run_success(mock_playwright) -> None:
    """Verify SpyScraper successfully runs with mocked playwright."""
    scraper = SpyScraper()
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=MockAsyncContextManager(mock_playwright)):
        result = await scraper.run(date.today())
        assert result.status == "success"
        assert result.market == "spy"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_run_success(mock_playwright) -> None:
    """Verify NseScraper successfully runs with mocked playwright."""
    scraper = NseScraper()
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=MockAsyncContextManager(mock_playwright)):
        result = await scraper.run(date.today())
        assert result.status == "success"
        assert result.market == "nse"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_exception_handling(mock_playwright) -> None:
    """Verify SpyScraper handles exceptions during scraping."""
    scraper = SpyScraper()
    mock_playwright.chromium.launch.side_effect = Exception("Browser error")
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=MockAsyncContextManager(mock_playwright)):
        with pytest.raises(Exception, match="Browser error"):
            await scraper.run(date.today())
