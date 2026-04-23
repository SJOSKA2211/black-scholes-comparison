import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.data.pipeline import DataPipeline


@pytest.mark.integration
async def test_spy_pipeline_run() -> None:
    """
    Test the SPY data pipeline end-to-end with mocked scraper.
    Verifies that audit logs and scrape runs are created.
    """
    market = "spy"
    run_id = "f4dd54e8-4fcd-412e-a3bb-098aaaeb4133"
    trade_date = datetime.date(2024, 1, 1)

    pipeline = DataPipeline(run_id, market)

    with patch("src.scrapers.scraper_factory.ScraperFactory.get_scraper") as mock_get:
        mock_scraper = AsyncMock()
        mock_scraper.scrape.return_value = AsyncMock()
        mock_scraper.scrape.return_value.to_dict.return_value = [
            {
                "underlying_price": 100,
                "strike_price": 105,
                "bid": 2.5,
                "ask": 2.6,
                "volatility": 0.2
            }
        ]
        mock_get.return_value = mock_scraper

        with patch("src.data.pipeline.create_audit_log", new_callable=AsyncMock) as mock_audit:
            with patch("src.data.pipeline.update_scrape_run", new_callable=AsyncMock) as mock_update:
                await pipeline.run(trade_date)

                assert mock_scraper.scrape.called
                assert mock_audit.called
                assert mock_update.called

@pytest.mark.integration
async def test_nse_pipeline_run() -> None:
    """
    Test the NSE data pipeline end-to-end with mocked scraper.
    """
    market = "nse"
    run_id = "a1b2c3d4-e5f6-4a5b-b6c7-d8e9f0a1b2c3"
    trade_date = datetime.date(2024, 1, 1)

    pipeline = DataPipeline(run_id, market)

    with patch("src.scrapers.scraper_factory.ScraperFactory.get_scraper") as mock_get:
        mock_scraper = AsyncMock()
        mock_scraper.scrape.return_value = AsyncMock()
        mock_scraper.scrape.return_value.to_dict.return_value = []
        mock_get.return_value = mock_scraper

        with patch("src.data.pipeline.create_audit_log", new_callable=AsyncMock):
            with patch("src.data.pipeline.update_scrape_run", new_callable=AsyncMock):
                await pipeline.run(trade_date)
                assert mock_scraper.scrape.called
