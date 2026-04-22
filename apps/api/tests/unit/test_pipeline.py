import pytest
from unittest.mock import MagicMock, AsyncMock, patch, ANY
from datetime import date
import pandas as pd
from src.data.pipeline import DataPipeline

@pytest.mark.unit
class TestDataPipeline:
    @pytest.mark.asyncio
    @patch("src.data.pipeline.ScraperFactory")
    @patch("src.data.pipeline.upsert_option_parameters")
    @patch("src.data.pipeline.insert_market_data")
    @patch("src.data.pipeline.update_scrape_run")
    @patch("src.data.pipeline.create_audit_log")
    async def test_pipeline_run_success(self, mock_audit, mock_update_run, mock_insert, mock_upsert, mock_factory):
        # Setup mocks
        mock_scraper = MagicMock()
        mock_scraper.scrape = AsyncMock(return_value=pd.DataFrame([{
            "underlying_price": 100.0, "strike_price": 100.0, "maturity_years": 1.0,
            "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call",
            "is_american": False, "trade_date": date.today(),
            "bid_price": 10.0, "ask_price": 11.0, "volume": 100, "open_interest": 1000
        }]))
        mock_factory.get_scraper.return_value = mock_scraper
        mock_upsert.return_value = "opt-123"
        
        pipeline = DataPipeline(run_id="run-123", market="spy")
        # Test with trade_date=None to cover line 35-36
        result = await pipeline.run(None)
        
        assert result["status"] == "success"
        assert result["rows_inserted"] == 1

    @pytest.mark.asyncio
    async def test_pipeline_no_market(self):
        # Cover line 32-33
        pipeline = DataPipeline(run_id="run-123", market=None)
        with pytest.raises(ValueError, match="Market must be specified"):
            await pipeline.run()

    @pytest.mark.asyncio
    @patch("src.data.pipeline.ScraperFactory")
    @patch("src.data.pipeline.create_audit_log")
    @patch("src.data.pipeline.update_scrape_run")
    async def test_pipeline_run_failure(self, mock_update_run, mock_audit, mock_factory):
        mock_scraper = MagicMock()
        mock_scraper.scrape = AsyncMock(side_effect=Exception("Scrape failed"))
        mock_factory.get_scraper.return_value = mock_scraper
        
        pipeline = DataPipeline(run_id="run-fail", market="spy")
        result = await pipeline.run(date.today())
        
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    @patch("src.data.pipeline.ScraperFactory")
    @patch("src.data.pipeline.upsert_option_parameters")
    @patch("src.data.pipeline.insert_market_data")
    @patch("src.data.pipeline.update_scrape_run")
    @patch("src.data.pipeline.create_audit_log")
    async def test_pipeline_row_failure(self, mock_audit, mock_update_run, mock_insert, mock_upsert, mock_factory):
        # Setup mocks with one good row and one row that causes validation error or similar
        mock_scraper = MagicMock()
        mock_scraper.scrape = AsyncMock(return_value=pd.DataFrame([
            {
                "underlying_price": 100.0, "strike_price": 100.0, "maturity_years": 1.0,
                "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call",
                "bid_price": 10.0, "ask_price": 11.0
            },
            {
                "underlying_price": 110.0, 
                "strike_price": 100.0, "maturity_years": 1.0,
                "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call",
                "bid_price": 10.0, "ask_price": 11.0
            }
        ]))
        mock_factory.get_scraper.return_value = mock_scraper
        mock_upsert.side_effect = ["opt-good", Exception("Internal error")]
        
        pipeline = DataPipeline(run_id="run-mixed", market="spy")
        result = await pipeline.run(date.today())
        
        assert result["status"] == "success"
        assert result["rows_inserted"] == 1 
