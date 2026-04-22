import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import date
from src.scrapers.spy_scraper import SPYScraper
from src.scrapers.nse_next_scraper import NSEScraper
from src.scrapers.scraper_factory import ScraperFactory
from src.scrapers.base_scraper import BaseScraper

@pytest.mark.unit
class TestScrapers:
    @pytest.mark.asyncio
    @patch("src.scrapers.spy_scraper.async_playwright")
    async def test_spy_scraper_success(self, mock_playwright):
        mock_p = mock_playwright.return_value.__aenter__.return_value
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        
        scraper = SPYScraper("run-123")
        res = await scraper.scrape(date.today())
        assert len(res) > 0

    @pytest.mark.asyncio
    @patch("src.scrapers.spy_scraper.async_playwright")
    async def test_spy_scraper_failure(self, mock_playwright):
        mock_p = mock_playwright.return_value.__aenter__.return_value
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value
        mock_page.goto = AsyncMock(side_effect=Exception("Network error"))
        
        scraper = SPYScraper("run-fail")
        with pytest.raises(Exception):
            await scraper.scrape(date.today())

    @pytest.mark.asyncio
    @patch("src.scrapers.nse_next_scraper.async_playwright")
    async def test_nse_scraper_success(self, mock_playwright):
        mock_p = mock_playwright.return_value.__aenter__.return_value
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        
        mock_underlying = MagicMock()
        mock_underlying.inner_text = AsyncMock(return_value="NIFTY 22,000.00")
        mock_page.query_selector = AsyncMock(return_value=mock_underlying)
        
        mock_row = MagicMock()
        cols = [MagicMock() for _ in range(20)]
        for i, c in enumerate(cols):
            if i == 11: c.inner_text = AsyncMock(return_value="22,000")
            elif i == 8: c.inner_text = AsyncMock(return_value="100")
            elif i == 9: c.inner_text = AsyncMock(return_value="110")
            else: c.inner_text = AsyncMock(return_value="-")
            
        mock_row.query_selector_all = AsyncMock(return_value=cols)
        mock_page.query_selector_all = AsyncMock(return_value=[mock_row])
        
        scraper = NSEScraper("run-123")
        res = await scraper.scrape(date.today())
        assert len(res) == 1

    @pytest.mark.asyncio
    @patch("src.scrapers.nse_next_scraper.async_playwright")
    async def test_nse_scraper_failure(self, mock_playwright):
        mock_p = mock_playwright.return_value.__aenter__.return_value
        # Mock failure at the very beginning of the 'async with' block context or launch
        mock_p.chromium.launch = AsyncMock(side_effect=Exception("NSE launch failed"))
        
        scraper = NSEScraper("run-fail")
        with pytest.raises(Exception, match="NSE launch failed"):
            await scraper.scrape(date.today())

    @pytest.mark.asyncio
    @patch("src.scrapers.nse_next_scraper.async_playwright")
    async def test_nse_scraper_row_failure(self, mock_playwright):
        mock_p = mock_playwright.return_value.__aenter__.return_value
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value
        mock_page.goto = AsyncMock()
        mock_page.wait_for_selector = AsyncMock()
        mock_page.query_selector = AsyncMock(return_value=None)
        
        mock_row_fail = MagicMock()
        mock_row_fail.query_selector_all = AsyncMock(return_value=[MagicMock()] * 5)
        
        mock_row_val_err = MagicMock()
        cols = [MagicMock() for _ in range(20)]
        for i, c in enumerate(cols):
            c.inner_text = AsyncMock(return_value="invalid" if i == 11 else "0")
        mock_row_val_err.query_selector_all = AsyncMock(return_value=cols)
        
        mock_page.query_selector_all = AsyncMock(return_value=[mock_row_fail, mock_row_val_err])
        
        scraper = NSEScraper("run-mixed")
        res = await scraper.scrape(date.today())
        assert len(res) == 0

    def test_scraper_factory(self):
        spy = ScraperFactory.get_scraper("spy", "run-123")
        assert isinstance(spy, SPYScraper)
        nse = ScraperFactory.get_scraper("nse", "run-123")
        assert isinstance(nse, NSEScraper)
        with pytest.raises(ValueError):
            ScraperFactory.get_scraper("unknown", "run-123")
            
    @pytest.mark.asyncio
    async def test_base_scraper_abstract(self):
        # Hit the abstract methods in base_scraper.py
        from src.scrapers.base_scraper import BaseScraper
        class Concrete(BaseScraper):
            async def scrape(self, trade_date: date): return await super().scrape(trade_date)
            async def run(self): return await super().run()
        
        c = Concrete("123")
        await c.scrape(date.today())
        await c.run()
        
        # Also hit pass in SPY/NSE run
        await SPYScraper("123").run()
        await NSEScraper("123").run()
