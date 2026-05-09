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
    
    with patch("src.scrapers.nse_next_scraper.NseScraper", return_value=mock_scraper_inst):
        pipeline = get_pipeline("nse")
        result = await pipeline.run(date(2025, 1, 1))
        
        assert result.market == "nse"
        assert result.rows_scraped == 0
        mock_scraper_inst.run.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_failed_scraper():
    """Test pipeline execution when scraper fails."""
    mock_scraper = AsyncMock()
    mock_scraper.run.side_effect = Exception("Scraper crash")
    
    pipeline = DataPipeline("spy", mock_scraper)
    result = await pipeline.run(date(2025, 1, 1))
    
    assert result.status == "failed"
    assert result.rows_scraped == 0

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_failed_persistence():
    """Test pipeline execution when persistence fails for some rows."""
    mock_scraper = AsyncMock()
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
    mock_scraper.run.return_value = ScraperResult(
        market="spy", execution_seconds=0.1, status="success", quotes=[mock_quote]
    )
    
    pipeline = DataPipeline("spy", mock_scraper)
    
    # Mock upsert_option_parameters to fail
    with patch("src.data.pipeline.upsert_option_parameters", side_effect=Exception("DB error")):
        result = await pipeline.run(date(2025, 1, 1))
        assert result.status == "success" # Pipeline continues for other rows
        assert result.rows_inserted == 0

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_invalid_market():
    """Test pipeline with invalid market."""
    with pytest.raises(ValueError, match="Unsupported market"):
        get_pipeline("invalid")
