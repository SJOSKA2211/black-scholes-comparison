import pytest
from datetime import date
from src.scrapers.nse_next_scraper import NSEScraper
from src.scrapers.spy_scraper import SPYScraper

@pytest.mark.integration
class TestScrapersExtended:
    @pytest.mark.asyncio
    async def test_nse_scraper_live(self):
        """Zero-mock: test NSE scraper naturally."""
        scraper = NSEScraper(run_id="test-live-nse")
        # NSE is often closed or has captchas, so we expect it might return []
        # but the code should run without crashing.
        data = await scraper.scrape(date.today())
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_spy_scraper_invalid_date(self):
        """Zero-mock: test with a date that might be problematic."""
        scraper = SPYScraper(run_id="test-date-spy")
        # Future date might return empty results naturally
        data = await scraper.scrape(date(2030, 1, 1))
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_scraper_run_direct(self):
        """Zero-mock: test the 'run' method which handles the full cycle."""
        scraper = SPYScraper(run_id="test-run-spy")
        # This will hit real DB to update status
        await scraper.run()
        # No crash means success in status handling
