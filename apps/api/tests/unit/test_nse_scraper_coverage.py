"""Unit tests for additional NSE scraper coverage."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.scrapers.nse_next_scraper import NSEScraper


@pytest.mark.unit
class TestNSEScraperCoverage:
    @patch("src.scrapers.nse_next_scraper.async_playwright")
    async def test_scrape_edge_cases(self, mock_playwright) -> None:
        """Test scraper branches: missing elements, invalid values, etc."""
        # Setup mocks
        mock_p = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value = mock_p
        mock_browser = AsyncMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_context = AsyncMock()
        mock_browser.new_context.return_value = mock_context
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page

        scraper = NSEScraper("test-run")

        # Test missing expiry value
        mock_el_expiry = AsyncMock()
        mock_el_expiry.get_attribute.return_value = None
        mock_page.query_selector.side_effect = [
            None,  # underlying
            mock_el_expiry,
        ]
        mock_page.query_selector_all.return_value = []
        data = await scraper.scrape(date(2026, 4, 22))
        assert data == []

        # Test rows with few columns
        mock_row_few = AsyncMock()
        mock_row_few.query_selector_all.return_value = [AsyncMock() for _ in range(5)]
        mock_page.query_selector.side_effect = None
        mock_page.query_selector.return_value = None
        mock_page.query_selector_all.return_value = [mock_row_few]
        data = await scraper.scrape(date(2026, 4, 22))
        assert data == []

        # Test zero asks
        mock_row_free = AsyncMock()
        mock_cols = [AsyncMock() for _ in range(21)]
        for c in mock_cols:
            c.inner_text.return_value = "0"
        mock_cols[11].inner_text.return_value = "100.0"  # strike
        mock_row_free.query_selector_all.return_value = mock_cols
        mock_page.query_selector_all.return_value = [mock_row_free]
        data = await scraper.scrape(date(2026, 4, 22))
        assert data == []

        # 2. Test row extraction catch block
        mock_row = AsyncMock()
        mock_cols = [AsyncMock() for _ in range(21)]
        # Make one column extraction fail
        mock_cols[11].inner_text.side_effect = ValueError("Bad strike")
        mock_row.query_selector_all.return_value = mock_cols

        mock_page.query_selector.side_effect = None
        mock_page.query_selector.return_value = None
        mock_page.query_selector_all.return_value = [mock_row]

        data = await scraper.scrape(date(2026, 4, 22))
        assert data == []

    @patch("src.scrapers.nse_next_scraper.logger")
    async def test_run_method(self, mock_logger) -> None:
        """Test the run() method for coverage."""
        scraper = NSEScraper("test-run")
        await scraper.run()
        mock_logger.info.assert_called_with("scraper_run_called", market="nse", run_id="test-run")
