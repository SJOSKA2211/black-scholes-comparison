"""Unit tests for data pipeline."""
from __future__ import annotations
from datetime import date
from unittest.mock import AsyncMock, patch
import pytest
from src.data.pipeline import DataPipeline
from src.scrapers.base_scraper import ScraperResult

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_run_success() -> None:
    """Test pipeline orchestration with mocks."""
    market = "spy"
    trade_date = date(2024, 1, 1)

    with (
        patch("src.data.pipeline.SpyScraper.run") as mock_run,
        patch("src.data.pipeline.SCRAPE_ROWS_INSERTED") as mock_metrics,
    ):
        mock_result = ScraperResult(
            quotes=[],
            execution_seconds=0.1,
            market="spy",
            status="success"
        )
        mock_run.return_value = mock_result

        pipeline = DataPipeline(market)
        result = await pipeline.run(trade_date)

        assert result.market == "spy"
        assert result.rows_scraped == 0
        mock_run.assert_awaited_once_with(trade_date)
        mock_metrics.labels.assert_called_with(market="spy")
