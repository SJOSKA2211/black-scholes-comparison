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
    mock_page.locator = MagicMock()
    mock_page.url = "https://finance.yahoo.com/quote/SPY/options"
    
    # Mock locator chain
    mock_cell = AsyncMock()
    mock_cell.inner_text = AsyncMock(return_value="NSE NEXT (KCB)")
    
    mock_price_cell = AsyncMock()
    mock_price_cell.inner_text = AsyncMock(return_value="4,500.00")
    
    mock_row = AsyncMock()
    mock_row.locator = MagicMock()
    mock_row.locator.return_value.all = AsyncMock(return_value=[
        mock_cell, MagicMock(), MagicMock(), mock_price_cell, MagicMock(), mock_price_cell
    ])
    
    mock_locator = MagicMock()
    mock_locator.all = AsyncMock(return_value=[mock_row])
    mock_page.locator.return_value = mock_locator
    
    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()
    
    mock_p = MagicMock()
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
    return mock_p

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_run_success() -> None:
    """Verify SpyScraper successfully runs with mocked yfinance."""
    scraper = SpyScraper()
    
    mock_ticker = MagicMock()
    mock_ticker.options = ["2025-12-31"]
    mock_ticker.fast_info = {"last_price": 500.0}
    
    mock_chain = MagicMock()
    mock_chain.calls = MagicMock()
    mock_chain.calls.iterrows.return_value = iter([(0, {"strike": 500.0, "bid": 10.0, "ask": 11.0})])
    mock_chain.puts = MagicMock()
    mock_chain.puts.iterrows.return_value = iter([])
    mock_ticker.option_chain.return_value = mock_chain

    with patch("src.scrapers.spy_scraper.yf.Ticker", return_value=mock_ticker):
        result = await scraper.run(date.today())
        assert result.status == "success"
        assert result.market == "spy"
        assert len(result.quotes) > 0

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
async def test_spy_scraper_exception_handling() -> None:
    """Verify SpyScraper handles exceptions during scraping."""
    scraper = SpyScraper()
    with patch("src.scrapers.spy_scraper.yf.Ticker", side_effect=Exception("API Error")):
        with pytest.raises(Exception, match="API Error"):
            await scraper.run(date.today())
