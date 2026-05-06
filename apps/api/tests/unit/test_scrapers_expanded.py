"""Expanded unit tests for Scraper coverage."""
from __future__ import annotations
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.scrapers.spy_scraper import SpyScraper
from src.scrapers.base_scraper import RawQuote

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_row_parsing() -> None:
    """Verify that SpyScraper correctly parses option rows."""
    scraper = SpyScraper()
    
    # Mock cells
    def create_mock_cell(text):
        cell = MagicMock()
        cell.inner_text = AsyncMock(return_value=text)
        return cell
        
    # Cells: Strike is index 2, Bid is index 4, Ask is index 5
    mock_cells = [create_mock_cell("0") for _ in range(10)]
    mock_cells[2].inner_text = AsyncMock(return_value="100.00")
    mock_cells[4].inner_text = AsyncMock(return_value="2.00")
    mock_cells[5].inner_text = AsyncMock(return_value="2.20")
    
    # Mock row
    mock_row = MagicMock()
    mock_row_locator = MagicMock()
    mock_row_locator.all = AsyncMock(return_value=mock_cells)
    mock_row.locator.return_value = mock_row_locator
    
    # Mock page
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.close = AsyncMock()
    
    mock_underlying = MagicMock()
    mock_underlying.first = MagicMock()
    mock_underlying.first.inner_text = AsyncMock(return_value="105.00")
    
    mock_rows_locator = MagicMock()
    mock_rows_locator.all = AsyncMock(return_value=[mock_row])
    
    def page_locator_side_effect(selector):
        if "regularMarketPrice" in selector:
            return mock_underlying
        return mock_rows_locator
    mock_page.locator.side_effect = page_locator_side_effect
    
    # Mock browser
    mock_browser = MagicMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_browser.close = AsyncMock()
    
    # Mock playwright
    mock_playwright = MagicMock()
    mock_playwright.chromium = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    
    # Mock context manager
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_playwright)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=mock_cm):
        result = await scraper.run(date(2025, 1, 1))
        assert result.status == "success"
        assert len(result.quotes) == 1
        assert result.quotes[0].strike_price == 100.0
        assert result.quotes[0].bid_price == 2.0
        assert result.quotes[0].ask_price == 2.2
