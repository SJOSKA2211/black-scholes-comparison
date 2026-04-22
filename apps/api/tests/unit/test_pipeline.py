import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import date
import pandas as pd
from src.data.pipeline import DataPipeline

@pytest.mark.unit
class TestDataPipeline:
    @pytest.mark.asyncio
    @patch("src.data.pipeline.ScraperFactory")
    @patch("src.data.pipeline.upsert_market_data")
    @patch("src.data.pipeline.update_scrape_run")
    @patch("src.data.pipeline.create_scrape_run")
    @patch("src.data.pipeline.create_audit_log")
    async def test_pipeline_run_success(self, mock_audit, mock_create_run, mock_update_run, mock_upsert, mock_factory):
        # Setup mocks
        mock_scraper = MagicMock()
        mock_scraper.scrape = AsyncMock(return_value=pd.DataFrame([{
            "underlying_price": 100.0, "strike_price": 100.0, "maturity_years": 1.0,
            "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call",
            "is_american": False, "trade_date": date.today(),
            "bid_price": 10.0, "ask_price": 11.0, "volume": 100, "open_interest": 1000
        }]))
        mock_factory.get_scraper.return_value = mock_scraper
        mock_create_run.return_value = "run-123"
        
        pipeline = DataPipeline(run_id="run-123", market="spy")
        result = await pipeline.run(date.today())
        
        assert result["status"] == "success"
        assert result["rows_inserted"] == 1
        mock_upsert.assert_called_once()
        mock_update_run.assert_called_with("run-123", status="success", finished_at=pytest.any, rows_scraped=1, rows_validated=1, rows_inserted=1, error_count=0)

    @pytest.mark.asyncio
    @patch("src.data.pipeline.ScraperFactory")
    @patch("src.data.pipeline.create_scrape_run")
    @patch("src.data.pipeline.update_scrape_run")
    @patch("src.data.pipeline.create_audit_log")
    async def test_pipeline_run_failure(self, mock_audit, mock_update_run, mock_create_run, mock_factory):
        mock_scraper = MagicMock()
        mock_scraper.scrape = AsyncMock(side_effect=Exception("Scrape failed"))
        mock_factory.get_scraper.return_value = mock_scraper
        mock_create_run.return_value = "run-fail"
        
        pipeline = DataPipeline(run_id="run-fail", market="spy")
        result = await pipeline.run(date.today())
        
        assert result["status"] == "failed"
        mock_update_run.assert_called_with("run-fail", status="failed", finished_at=pytest.any, error_count=1)
