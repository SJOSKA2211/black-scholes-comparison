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
    """Mock playwright object with nested mocks for both scrapers."""
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.click = AsyncMock()
    
    mock_item = MagicMock()
    mock_item.inner_text = AsyncMock(return_value="Contract Name")
    mock_item.locator = MagicMock()
    mock_item.locator.return_value.all = AsyncMock(return_value=[])
    
    mock_locator = MagicMock()
    mock_locator.all = AsyncMock(return_value=[mock_item])
    mock_locator.first = mock_item
    
    mock_page.locator.return_value = mock_locator
    
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    mock_browser = MagicMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()
    
    mock_p = MagicMock()
    mock_p.chromium.launch = AsyncMock(return_value=mock_browser)
    
    return mock_p

def create_mock_cell(text):
    cell = MagicMock()
    cell.inner_text = AsyncMock(return_value=text)
    return cell

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_run_success(mock_playwright) -> None:
    """Verify SpyScraper successfully runs with mocked Playwright."""
    scraper = SpyScraper()
    mock_item = mock_playwright.chromium.launch.return_value.new_context.return_value.new_page.return_value.locator.return_value.all.return_value[0]
    spy_cells = [
        create_mock_cell("SPY260511C00700000"),
        create_mock_cell("0.0"),
        create_mock_cell("700.00"),
        create_mock_cell("0.0"),
        create_mock_cell("10.00"),
        create_mock_cell("11.00"),
    ]
    mock_item.locator.return_value.all.return_value = spy_cells
    
    mock_price_item = MagicMock()
    mock_price_item.inner_text = AsyncMock(return_value="500.00")
    mock_playwright.chromium.launch.return_value.new_context.return_value.new_page.return_value.locator.return_value.first = mock_price_item
    
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=MockAsyncContextManager(mock_playwright)):
        result = await scraper.run(date.today())
        assert result.status == "success"
        assert len(result.quotes) > 0

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_run_success(mock_playwright) -> None:
    """Verify NseScraper successfully runs with mocked playwright."""
    scraper = NseScraper()
    mock_table = mock_playwright.chromium.launch.return_value.new_context.return_value.new_page.return_value.locator.return_value.all.return_value[0]
    mock_table.inner_text = AsyncMock(return_value="Contract Name")
    
    mock_row = MagicMock()
    mock_row.locator.return_value.all = AsyncMock()
    mock_table.locator.return_value.all.return_value = [mock_row]
    
    nse_cells = [
        create_mock_cell("NSE NEXT (KCB)"),
        create_mock_cell("0.0"),
        create_mock_cell("18-Jun-2026"),
        create_mock_cell("4500.00"),
        create_mock_cell("0.0"),
        create_mock_cell("4400.00"),
    ]
    mock_row.locator.return_value.all.return_value = nse_cells
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=MockAsyncContextManager(mock_playwright)):
        result = await scraper.run(date.today())
        assert result.status == "success"
        assert len(result.quotes) > 0

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_exception_handling() -> None:
    """Verify SpyScraper handles exceptions during scraping."""
    scraper = SpyScraper()
    # SpyScraper catches internal exceptions and returns collected quotes.
    # If async_playwright fails, it raises out to run() which re-raises.
    with patch("src.scrapers.spy_scraper.async_playwright", side_effect=Exception("Browser Error")):
        with pytest.raises(Exception, match="Browser Error"):
            await scraper.run(date.today())

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_no_table(mock_playwright) -> None:
    """Verify NseScraper handles missing target table."""
    scraper = NseScraper()
    mock_table = mock_playwright.chromium.launch.return_value.new_context.return_value.new_page.return_value.locator.return_value.all.return_value[0]
    mock_table.inner_text = AsyncMock(return_value="No match")
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=MockAsyncContextManager(mock_playwright)):
        result = await scraper.run(date.today())
        assert result.status == "success"
        assert len(result.quotes) == 0

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_parsing_error(mock_playwright) -> None:
    """Verify SpyScraper handles row parsing errors."""
    scraper = SpyScraper()
    mock_item = mock_playwright.chromium.launch.return_value.new_context.return_value.new_page.return_value.locator.return_value.all.return_value[0]
    # Invalid data row
    mock_item.locator.return_value.all.return_value = [create_mock_cell("invalid")] * 6
    
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=MockAsyncContextManager(mock_playwright)):
        result = await scraper.run(date.today())
        assert result.status == "success"
        assert len(result.quotes) == 0
