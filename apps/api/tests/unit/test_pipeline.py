from datetime import date
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from src.data.pipeline import DataPipeline, get_pipeline


@pytest.mark.unit
def test_get_pipeline_factory() -> None:
    """Test the factory function for DataPipeline."""
    p1 = get_pipeline("spy", run_id="fixed-id")
    assert p1.market == "spy"
    assert p1.run_id == "fixed-id"

    p2 = get_pipeline("nse")
    assert p2.market == "nse"
    assert p2.run_id is not None  # Generated UUID


class TestDataPipeline:
    @patch("src.data.pipeline.ScraperFactory")
    @patch("src.data.pipeline.upsert_option_parameters", new_callable=AsyncMock)
    @patch("src.data.pipeline.insert_market_data", new_callable=AsyncMock)
    @patch("src.data.pipeline.update_scrape_run", new_callable=AsyncMock)
    @patch("src.data.pipeline.create_audit_log", new_callable=AsyncMock)
    async def test_pipeline_run_success(
        self,
        mock_audit: Any,
        mock_update_run: Any,
        mock_insert: Any,
        mock_upsert: Any,
        mock_factory: Any,
    ) -> None:
        mock_scraper = MagicMock()
        mock_scraper.scrape = AsyncMock(
            return_value=[
                {
                    "underlying_price": 100.0,
                    "strike_price": 100.0,
                    "maturity_years": 1.0,
                    "volatility": 0.2,
                    "risk_free_rate": 0.05,
                    "option_type": "call",
                    "is_american": False,
                    "trade_date": date.today(),
                    "bid_price": 10.0,
                    "ask_price": 11.0,
                    "volume": 100,
                    "open_interest": 1000,
                }
            ]
        )
        mock_factory.get_scraper.return_value = mock_scraper
        mock_upsert.return_value = "opt-123"

        pipeline = DataPipeline("run-123", market="spy")
        result = await pipeline.run(None)

        assert result["status"] == "success"
        assert result["rows_inserted"] == 1

    async def test_pipeline_no_market(self) -> None:
        with pytest.raises(ValueError, match="Market must be specified"):
            # run_id is positional, market is keyword
            await DataPipeline("run-123").run()

    @patch("src.data.pipeline.ScraperFactory")
    @patch("src.data.pipeline.create_audit_log", new_callable=AsyncMock)
    @patch("src.data.pipeline.update_scrape_run", new_callable=AsyncMock)
    async def test_pipeline_run_failure(
        self, mock_update_run: Any, mock_audit: Any, mock_factory: Any
    ) -> None:
        mock_scraper = MagicMock()
        mock_scraper.scrape = AsyncMock(side_effect=Exception("Scrape failed"))
        mock_factory.get_scraper.return_value = mock_scraper

        pipeline = DataPipeline("run-fail", market="spy")
        result = await pipeline.run(date.today())

        assert result["status"] == "failed"

    @patch("src.data.pipeline.ScraperFactory")
    @patch("src.data.pipeline.upsert_option_parameters", new_callable=AsyncMock)
    @patch("src.data.pipeline.insert_market_data", new_callable=AsyncMock)
    @patch("src.data.pipeline.update_scrape_run", new_callable=AsyncMock)
    @patch("src.data.pipeline.create_audit_log", new_callable=AsyncMock)
    async def test_pipeline_row_failure(
        self,
        mock_audit: Any,
        mock_update_run: Any,
        mock_insert: Any,
        mock_upsert: Any,
        mock_factory: Any,
    ) -> None:
        mock_scraper = MagicMock()
        mock_scraper.scrape = AsyncMock(
            return_value=[
                {
                    "underlying_price": 100.0,
                    "strike_price": 100.0,
                    "maturity_years": 1.0,
                    "volatility": 0.2,
                    "risk_free_rate": 0.05,
                    "option_type": "call",
                    "bid_price": 10.0,
                    "ask_price": 11.0,
                    "trade_date": date.today(),
                },
                {
                    "underlying_price": 110.0,
                    "strike_price": 100.0,
                    "maturity_years": 1.0,
                    "volatility": 0.2,
                    "risk_free_rate": 0.05,
                    "option_type": "call",
                    "bid_price": 10.0,
                    "ask_price": 11.0,
                    "trade_date": date.today(),
                },
            ]
        )
        mock_factory.get_scraper.return_value = mock_scraper
        mock_upsert.side_effect = ["opt-good", Exception("Internal error")]

        pipeline = DataPipeline("run-mixed", market="spy")
        result = await pipeline.run(date.today())

        assert result["status"] == "success"
        assert result["rows_inserted"] == 1
