from datetime import date
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.scrapers.nse_next_scraper import NSEScraper
from src.scrapers.scraper_factory import ScraperFactory
from src.scrapers.spy_scraper import SPYScraper


@pytest.mark.unit
class TestScrapers:
    @patch("src.scrapers.spy_scraper.async_playwright")
    async def test_spy_scraper_success(self, mock_playwright: Any) -> None:
        mock_p = mock_playwright.return_value.__aenter__.return_value
        mock_browser = AsyncMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page

        # Mock price and expiry
        mock_price = AsyncMock()
        mock_price.inner_text.return_value = "500.00"
        mock_expiry = AsyncMock()
        mock_expiry.get_attribute.return_value = "1713824000"  # Some timestamp

        async def mock_qs(sel):
            if "regularMarketPrice" in sel:
                return mock_price
            if "select" in sel:
                return mock_expiry
            return None

        mock_page.query_selector.side_effect = mock_qs

        # Mock rows
        mock_row = AsyncMock()
        mock_cols = [AsyncMock() for _ in range(11)]
        for i, c in enumerate(mock_cols):
            c.inner_text.return_value = "100"
        mock_row.query_selector_all.return_value = mock_cols
        # evaluate for calls/puts
        mock_row.evaluate.return_value = "table-calls"

        mock_page.query_selector_all.return_value = [mock_row]

        scraper = SPYScraper("run-123")
        res = await scraper.scrape(date(2024, 1, 1))
        assert len(res) == 1
        assert res[0]["underlying_price"] == 500.0

    @patch("src.scrapers.spy_scraper.async_playwright")
    async def test_spy_scraper_failure(self, mock_playwright: Any) -> None:
        mock_p = mock_playwright.return_value.__aenter__.return_value
        mock_browser = AsyncMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page
        mock_page.goto.side_effect = Exception("Network error")

        scraper = SPYScraper("run-fail")
        with pytest.raises(Exception):
            await scraper.scrape(date.today())

    @patch("src.scrapers.nse_next_scraper.async_playwright")
    async def test_nse_scraper_success(self, mock_playwright: Any) -> None:
        mock_p = mock_playwright.return_value.__aenter__.return_value
        mock_browser = AsyncMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page

        mock_underlying = AsyncMock()
        mock_underlying.inner_text.return_value = "NIFTY 22,000.00"
        mock_expiry = AsyncMock()
        mock_expiry.get_attribute.return_value = "25-Apr-2024"

        async def mock_qs(sel):
            if sel == "#equity_underlyingVal":
                return mock_underlying
            if sel == "#expirySelect":
                return mock_expiry
            return None

        mock_page.query_selector.side_effect = mock_qs

        mock_row = AsyncMock()
        mock_cols = [AsyncMock() for _ in range(21)]
        for i, c in enumerate(mock_cols):
            if i == 11:
                c.inner_text.return_value = "22,000"
            elif i == 8:
                c.inner_text.return_value = "100"
            elif i == 9:
                c.inner_text.return_value = "110"
            else:
                c.inner_text.return_value = "10"

        mock_row.query_selector_all.return_value = mock_cols
        mock_page.query_selector_all.return_value = [mock_row]

        scraper = NSEScraper("run-123")
        res = await scraper.scrape(date(2024, 1, 1))
        assert len(res) >= 0

    def test_scraper_factory(self) -> None:
        spy = ScraperFactory.get_scraper("spy", "run-123")
        assert isinstance(spy, SPYScraper)
        nse = ScraperFactory.get_scraper("nse", "run-123")
        assert isinstance(nse, NSEScraper)
        with pytest.raises(ValueError):
            ScraperFactory.get_scraper("unknown", "run-123")
