"""Unit tests for additional SPY scraper coverage."""

from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from src.scrapers.spy_scraper import SPYScraper


@pytest.mark.unit
class TestSPYScraperCoverage:
    @patch("src.scrapers.spy_scraper.async_playwright")
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

        # 1. Test price fallback and invalid values
        # Mock price_selectors loop: first sel fails, second has invalid text
        mock_el_price = AsyncMock()
        mock_el_price.inner_text.return_value = "invalid-price"
        mock_page.query_selector.side_effect = [
            None,  # sel 1 fails
            mock_el_price,  # sel 2 has invalid price
            None,  # sel 3 fails
            None,  # expiry_el missing
            [],  # row_all returns empty
        ]

        scraper = SPYScraper("test-run")
        data = await scraper.scrape(date(2026, 4, 22))
        assert data == []  # No rows extracted

        # Test expiry value not digit
        mock_el_expiry = AsyncMock()
        mock_el_expiry.get_attribute.return_value = "not-a-digit"
        mock_page.query_selector.side_effect = [
            None,
            None,
            None,  # price sels
            mock_el_expiry,  # expiry_el has non-digit val
        ]
        mock_page.query_selector_all.return_value = []
        data = await scraper.scrape(date(2026, 4, 22))
        assert data == []

        # Test rows with few columns
        mock_row_few = AsyncMock()
        mock_row_few.query_selector_all.return_value = [
            AsyncMock() for _ in range(5)
        ]  # only 5 cols
        mock_page.query_selector.side_effect = None
        mock_page.query_selector.return_value = None
        mock_page.query_selector_all.return_value = [mock_row_few]
        data = await scraper.scrape(date(2026, 4, 22))
        assert data == []

        # Test ask <= 0
        mock_row_free = AsyncMock()
        mock_cols = [AsyncMock() for _ in range(11)]
        mock_cols[2].inner_text.return_value = "100.0"  # strike
        mock_cols[4].inner_text.return_value = "1.0"  # bid
        mock_cols[5].inner_text.return_value = "0.0"  # ask (zero)
        mock_cols[10].inner_text.return_value = "20%"  # IV
        mock_row_free.query_selector_all.return_value = mock_cols
        mock_page.query_selector_all.return_value = [mock_row_free]
        data = await scraper.scrape(date(2026, 4, 22))
        assert data == []  # ask <= 0 excluded

        # 2. Test row extraction catch block
        mock_row = AsyncMock()
        mock_cols = [AsyncMock() for _ in range(11)]
        # Make one column extraction fail
        mock_cols[2].inner_text.side_effect = ValueError("Bad strike")
        mock_row.query_selector_all.return_value = mock_cols

        # Reset side effects for next run
        mock_page.query_selector.side_effect = None
        mock_page.query_selector.return_value = None  # price and expiry missing
        mock_page.query_selector_all.return_value = [mock_row]

        data = await scraper.scrape(date(2026, 4, 22))
        assert data == []  # Row failed, caught by exception block

    @patch("src.scrapers.spy_scraper.logger")
    async def test_run_method(self, mock_logger) -> None:
        """Test the run() method for coverage."""
        scraper = SPYScraper("test-run")
        await scraper.run()
        mock_logger.info.assert_called_with("scraper_run_called", market="spy", run_id="test-run")
