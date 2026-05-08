"""Unit tests for market data transformers."""
from datetime import date
import pytest
from src.data.transformers import calculate_mid_price, transform_to_option_parameters
from src.scrapers.base_scraper import RawQuote
from src.methods.base import OptionType

@pytest.fixture
def raw_quote():
    return RawQuote(
        underlying_symbol="SPY",
        strike_price=100.0,
        maturity_date=date(2025, 12, 31),
        option_type="call",
        bid_price=5.0,
        ask_price=5.5,
        underlying_price=100.0,
        data_source="spy",
    )

@pytest.mark.unit
def test_calculate_mid_price(raw_quote):
    assert calculate_mid_price(raw_quote) == 5.25

@pytest.mark.unit
def test_transform_to_option_parameters(raw_quote):
    params = transform_to_option_parameters(raw_quote, 0.05)
    assert params.underlying_price == 100.0
    assert params.strike_price == 100.0
    assert params.risk_free_rate == 0.05
    assert params.option_type == OptionType.CALL
