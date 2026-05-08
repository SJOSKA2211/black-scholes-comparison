"""Unit tests for the data pipeline."""
from __future__ import annotations
from datetime import date
from unittest.mock import AsyncMock, patch
import pytest
from src.data.pipeline import DataPipeline, get_pipeline
from src.scrapers.base_scraper import ScraperResult, RawQuote

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_run():
    """Test standard pipeline execution."""
    mock_scraper_inst = AsyncMock()
    mock_quote = RawQuote(
        underlying_symbol="SPY",
        strike_price=100.0,
        maturity_date=date(2025, 12, 31),
        option_type="call",
        bid_price=5.0,
        ask_price=5.5,
        underlying_price=100.0,
        data_source="spy",
    )
    mock_scraper_inst.run.return_value = ScraperResult(
        market="spy", 
        execution_seconds=0.1,
        status="success",
        quotes=[mock_quote]
    )
    
    with patch("src.scrapers.spy_scraper.SpyScraper", return_value=mock_scraper_inst):
        pipeline = get_pipeline("spy")
        result = await pipeline.run(date(2025, 1, 1))
        
        assert result.market == "spy"
        assert result.rows_scraped == 1
        assert result.rows_validated == 1
        mock_scraper_inst.run.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_run_nse():
    """Test pipeline execution for NSE."""
    mock_scraper_inst = AsyncMock()
    mock_scraper_inst.run.return_value = ScraperResult(
        market="nse", 
        execution_seconds=0.1,
        status="success",
        quotes=[]
    )
    
    with patch("src.scrapers.nse_scraper.NseScraper", return_value=mock_scraper_inst):
        pipeline = get_pipeline("nse")
        result = await pipeline.run(date(2025, 1, 1))
        
        assert result.market == "nse"
        assert result.rows_scraped == 0
        mock_scraper_inst.run.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_invalid_market():
    """Test pipeline with invalid market."""
    with pytest.raises(ValueError, match="Unsupported market"):
        get_pipeline("invalid")
