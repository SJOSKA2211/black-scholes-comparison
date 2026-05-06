"""Unit tests for data transformers and pipeline."""
from __future__ import annotations
from datetime import date
from unittest.mock import AsyncMock, patch
import pytest
from src.data.transformers import transform_to_option_parameters, calculate_mid_price
from src.scrapers.base_scraper import RawQuote
from src.data.pipeline import DataPipeline

@pytest.mark.unit
def test_calculate_mid_price() -> None:
    """Verify mid-price calculation."""
    quote = RawQuote(
        underlying_symbol="SPY",
        strike_price=100.0,
        maturity_date=date(2025, 1, 1),
        option_type="call",
        bid_price=2.0,
        ask_price=2.2,
        underlying_price=100.0,
        data_source="spy"
    )
    assert calculate_mid_price(quote) == 2.1

@pytest.mark.unit
def test_transform_to_option_parameters() -> None:
    """Verify transformation to OptionParameters."""
    quote = RawQuote(
        underlying_symbol="SPY",
        strike_price=100.0,
        maturity_date=date(2025, 1, 1),
        option_type="call",
        bid_price=2.0,
        ask_price=2.2,
        underlying_price=105.0,
        data_source="spy"
    )
    params = transform_to_option_parameters(quote, 0.05)
    assert params.underlying_price == 105.0
    assert params.strike_price == 100.0
    assert params.risk_free_rate == 0.05

@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_run() -> None:
    """Verify pipeline orchestration."""
    pipeline = DataPipeline("spy")
    
    mock_scraper_result = AsyncMock()
    mock_scraper_result.quotes = [
        RawQuote(
            underlying_symbol="SPY",
            strike_price=100.0,
            maturity_date=date(2025, 1, 1),
            option_type="call",
            bid_price=2.0,
            ask_price=2.2,
            underlying_price=105.0,
            data_source="spy"
        )
    ]
    
    with patch("src.data.pipeline.SpyScraper") as mock_scraper_cls:
        mock_scraper = mock_scraper_cls.return_value
        mock_scraper.run = AsyncMock(return_value=mock_scraper_result)
        
        # Mock validator to pass
        with patch("src.data.pipeline.validate_quote", return_value=True):
            result = await pipeline.run(date(2025, 1, 1))
            
            assert result.market == "spy"
            assert result.rows_scraped == 1
            assert result.rows_validated == 1
            mock_scraper.run.assert_called_once()
