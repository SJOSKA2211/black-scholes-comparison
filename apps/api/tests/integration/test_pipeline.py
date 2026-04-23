from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from src.data.pipeline import get_pipeline
from src.database.repository import create_scrape_run


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_run_spy() -> None:
    # 1. Setup - Create a real scrape run row first
    run_id = await create_scrape_run("spy")
    pipeline = get_pipeline("spy", run_id=run_id)

    # 2. Mock Scraper
    mock_rows = [
        {
            "underlying_price": 100.0,
            "strike_price": 100.0,
            "maturity_years": 1.0,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call",
            "bid_price": 10.0,
            "ask_price": 11.0,
            "volume": 10,
            "open_interest": 5,
        }
    ]

    with patch("src.scrapers.scraper_factory.ScraperFactory.get_scraper") as mock_factory:
        mock_scraper = AsyncMock()
        mock_scraper.scrape.return_value = mock_rows
        mock_factory.return_value = mock_scraper

        # 3. Run Pipeline
        result = await pipeline.run(trade_date=date.today())

        # 4. Assertions
        assert result["status"] == "success"
        assert result["rows_scraped"] == 1
        assert result["rows_inserted"] == 1

        # Verify it actually went to the DB by checking scrape_runs
        from src.database.repository import get_supabase_client

        supabase = get_supabase_client()
        response = supabase.table("scrape_runs").select("*").eq("id", run_id).execute()
        assert len(response.data) > 0
        assert response.data[0]["status"] == "success"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_invalid_data() -> None:
    run_id = await create_scrape_run("spy")
    pipeline = get_pipeline("spy", run_id=run_id)

    # Invalid row (bid > ask)
    mock_rows = [{"bid_price": 20.0, "ask_price": 10.0, "underlying_price": 100.0}]

    with patch("src.scrapers.scraper_factory.ScraperFactory.get_scraper") as mock_factory:
        mock_scraper = AsyncMock()
        mock_scraper.scrape.return_value = mock_rows
        mock_factory.return_value = mock_scraper

        result = await pipeline.run(trade_date=date.today())

        # Should finish but rows_inserted should be 0 due to validation failure
        assert result["status"] == "success"
        assert result["rows_inserted"] == 0
