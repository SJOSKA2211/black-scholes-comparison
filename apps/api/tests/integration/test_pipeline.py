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
async def test_pipeline_run_nse() -> None:
    run_id = await create_scrape_run("nse")
    pipeline = get_pipeline("nse", run_id=run_id)

    mock_rows = [
        {
            "underlying_price": 24000.0,
            "strike_price": 24000.0,
            "maturity_years": 0.1,
            "volatility": 0.15,
            "risk_free_rate": 0.07,
            "option_type": "put",
            "bid_price": 200.0,
            "ask_price": 210.0,
        }
    ]

    with patch("src.scrapers.scraper_factory.ScraperFactory.get_scraper") as mock_factory:
        mock_scraper = AsyncMock()
        mock_scraper.scrape.return_value = mock_rows
        mock_factory.return_value = mock_scraper

        result = await pipeline.run(trade_date=date.today())

        assert result["status"] == "success"
        assert result["rows_inserted"] == 1


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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_no_market_data() -> None:
    run_id = await create_scrape_run("spy")
    pipeline = get_pipeline("spy", run_id=run_id)

    with patch("src.scrapers.scraper_factory.ScraperFactory.get_scraper") as mock_factory:
        mock_scraper = AsyncMock()
        mock_scraper.scrape.return_value = []
        mock_factory.return_value = mock_scraper

        result = await pipeline.run(trade_date=date.today())

        assert result["status"] == "success"
        assert result["rows_scraped"] == 0
        assert result["rows_inserted"] == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_error_handling() -> None:
    # 1. Missing market (line 92-93)
    run_id = await create_scrape_run("spy")
    pipeline = get_pipeline("spy", run_id=run_id)
    pipeline.market = None

    with pytest.raises(ValueError, match="Market must be specified"):
        await pipeline.run()

    # Restore market
    pipeline.market = "spy"

    # 2. Scraper Exception (line 134-139) and no trade_date (line 95-96)
    with patch("src.scrapers.scraper_factory.ScraperFactory.get_scraper") as mock_factory:
        mock_scraper = AsyncMock()
        mock_scraper.scrape.side_effect = Exception("Scrape failed")
        mock_factory.return_value = mock_scraper

        # Passing no trade_date hits line 95-96
        result = await pipeline.run()

        assert result["status"] == "failed"
        assert result["error"] == "Scrape failed"

    # 3. Row Processing Exception (line 77-79)
    # Validate quote throws ValueError but upsert_option_parameters can throw anything
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

        # Force upsert_option_parameters to throw to hit line 77-79
        with patch("src.data.pipeline.upsert_option_parameters", side_effect=Exception("DB Error")):
            result = await pipeline.run(trade_date=date.today())

            assert result["status"] == "success"
            assert result["rows_inserted"] == 0
