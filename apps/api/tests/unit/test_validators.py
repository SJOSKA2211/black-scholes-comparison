"""Unit tests for market data validators."""

from datetime import date

import pytest

from src.data.validators import (
    validate_bid_ask_spread,
    validate_maturity_date,
    validate_positive_prices,
    validate_quote,
    validate_strike_price,
    validate_symbol,
)
from src.exceptions import ValidationError
from src.scrapers.base_scraper import RawQuote


@pytest.fixture
def valid_quote():
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
def test_validate_positive_prices(valid_quote):
    assert validate_positive_prices(valid_quote) is True
    valid_quote.bid_price = -1
    with pytest.raises(ValidationError):
        validate_positive_prices(valid_quote)


@pytest.mark.unit
def test_validate_bid_ask_spread(valid_quote):
    assert validate_bid_ask_spread(valid_quote) is True
    valid_quote.bid_price = 10
    valid_quote.ask_price = 5
    with pytest.raises(ValidationError):
        validate_bid_ask_spread(valid_quote)


@pytest.mark.unit
def test_validate_strike_price(valid_quote):
    assert validate_strike_price(valid_quote) is True
    valid_quote.strike_price = 0
    with pytest.raises(ValidationError):
        validate_strike_price(valid_quote)


@pytest.mark.unit
def test_validate_maturity_date(valid_quote):
    assert validate_maturity_date(valid_quote) is True


@pytest.mark.unit
def test_validate_symbol(valid_quote):
    assert validate_symbol(valid_quote) is True
    valid_quote.underlying_symbol = ""
    with pytest.raises(ValidationError):
        validate_symbol(valid_quote)


@pytest.mark.unit
def test_validate_quote_composite(valid_quote):
    assert validate_quote(valid_quote) is True
    valid_quote.bid_price = -1
    assert validate_quote(valid_quote) is False
