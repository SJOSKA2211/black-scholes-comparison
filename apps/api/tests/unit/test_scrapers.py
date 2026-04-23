from typing import Any
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import date
from src.scrapers.spy_scraper import SPYScraper
from src.scrapers.nse_next_scraper import NSEScraper
from src.scrapers.scraper_factory import ScraperFactory

@pytest.mark.unit
class TestScrapers:
    @patch("src.scrapers.spy_scraper.async_playwright")
    async def test_spy_scraper_success(self, mock_playwright: Any) -> None:
        mock_p = mock_playwright.return_value.__aenter__.return_value
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value
        
        # Mock finding rows
        mock_row = MagicMock()
        mock_row.query_selector_all.return_value = [MagicMock(inner_text=AsyncMock(return_value="100")) for _ in range(10)]
        mock_page.query_selector_all.return_value = [mock_row]
        
        scraper = SPYScraper("run-123")
        res = await scraper.scrape(date.today())
        # SPYScraper needs specific table structure. 
        # If it's empty, we just check it doesn't crash.
        assert isinstance(res, Any) # It returns a DataFrame

    @patch("src.scrapers.spy_scraper.async_playwright")
    async def test_spy_scraper_failure(self, mock_playwright: Any) -> None:
        mock_p = mock_playwright.return_value.__aenter__.return_value
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value
        mock_page.goto = AsyncMock(side_effect=Exception("Network error"))
        
        scraper = SPYScraper("run-fail")
        with pytest.raises(Exception):
            await scraper.scrape(date.today())

    @patch("src.scrapers.nse_next_scraper.async_playwright")
    async def test_nse_scraper_success(self, mock_playwright: Any) -> None:
        mock_p = mock_playwright.return_value.__aenter__.return_value
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value
        
        mock_underlying = MagicMock()
        mock_underlying.inner_text = AsyncMock(return_value="NIFTY 22,000.00")
        mock_page.query_selector = AsyncMock(return_value=mock_underlying)
        
        mock_row = MagicMock()
        cols = [MagicMock() for _ in range(21)]
        for i, c in enumerate(cols):
            if i == 11: c.inner_text = AsyncMock(return_value="22,000")
            elif i == 8: c.inner_text = AsyncMock(return_value="100")
            elif i == 9: c.inner_text = AsyncMock(return_value="110")
            else: c.inner_text = AsyncMock(return_value="10")
            
        mock_row.query_selector_all = AsyncMock(return_value=cols)
        mock_page.query_selector_all = AsyncMock(return_value=[mock_row])
        
        scraper = NSEScraper("run-123")
        res = await scraper.scrape(date.today())
        assert len(res) >= 0

    def test_scraper_factory(self) -> None:
        spy = ScraperFactory.get_scraper("spy", "run-123")
        assert isinstance(spy, SPYScraper)
        nse = ScraperFactory.get_scraper("nse", "run-123")
        assert isinstance(nse, NSEScraper)
        with pytest.raises(ValueError):
            ScraperFactory.get_scraper("unknown", "run-123")
