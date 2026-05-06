"""Unit tests for data pipeline."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import date
from src.data.pipeline import DataPipeline

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_run_success() -> None:
    """Test pipeline orchestration with mocks."""
    market = "spy"
    trade_date = date(2024, 1, 1)
    
    with patch("src.data.pipeline.get_scraper") as mock_get_scraper, \
         patch("src.data.pipeline.Repository") as mock_repo_class:
        
        mock_scraper = AsyncMock()
        mock_get_scraper.return_value = mock_scraper
        mock_scraper.scrape.return_value = [{"strike": 100}]
        
        pipeline = DataPipeline(market)
        await pipeline.run(trade_date)
        
        mock_scraper.scrape.assert_awaited_once_with(trade_date)
