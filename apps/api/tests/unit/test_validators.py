import pytest
from src.data.validators import (
    validate_underlying_price,
    validate_strike_price,
    validate_maturity,
    validate_volatility,
    validate_risk_free_rate,
    validate_quote,
    ValidationError
)

@pytest.mark.unit
class TestValidators:
    def test_validate_underlying(self):
        assert validate_underlying_price(100.0) == 100.0
        with pytest.raises(ValidationError, match="Underlying price must be positive"):
            validate_underlying_price(-1.0)
        with pytest.raises(ValidationError):
            validate_underlying_price(0.0)

    def test_validate_strike(self):
        assert validate_strike_price(105.0) == 105.0
        with pytest.raises(ValidationError, match="Strike price must be positive"):
            validate_strike_price(-10.0)

    def test_validate_maturity(self):
        assert validate_maturity(0.5) == 0.5
        with pytest.raises(ValidationError, match="Maturity must be positive"):
            validate_maturity(0.0)

    def test_validate_volatility(self):
        assert validate_volatility(0.25) == 0.25
        with pytest.raises(ValidationError, match="Volatility must be positive"):
            validate_volatility(-0.1)

    def test_validate_risk_free_rate(self):
        assert validate_risk_free_rate(0.05) == 0.05
        assert validate_risk_free_rate(0.0) == 0.0
        with pytest.raises(ValidationError, match="Risk-free rate cannot be negative"):
            validate_risk_free_rate(-0.01)

    def test_validate_quote_valid(self):
        quote = {"bid": 10.0, "ask": 10.5, "underlying": 100.0}
        assert validate_quote(quote) == quote

    def test_validate_quote_invalid_bid_ask(self):
        quote = {"bid": 11.0, "ask": 10.5, "underlying": 100.0}
        with pytest.raises(ValidationError, match="Bid cannot be greater than ask"):
            validate_quote(quote)

    def test_validate_quote_negative_ask(self):
        quote = {"bid": -1.0, "ask": 10.5, "underlying": 100.0}
        with pytest.raises(ValidationError):
            validate_quote(quote)

    def test_validate_quote_missing_keys(self):
        quote = {"bid": 10.0}
        with pytest.raises(ValidationError):
            validate_quote(quote)

    def test_validate_quote_edge_zero_bid(self):
        quote = {"bid": 0.0, "ask": 0.05, "underlying": 100.0}
        assert validate_quote(quote) == quote
