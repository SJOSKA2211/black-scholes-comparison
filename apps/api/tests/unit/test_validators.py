import pytest
from src.data.validators import (
    validate_underlying_price,
    validate_strike_price,
    validate_maturity,
    validate_volatility,
    validate_risk_free_rate,
    validate_quote,
    ValidationError,
)

@pytest.mark.unit
class TestValidators:
    def test_numeric_validators_success(self):
        assert validate_underlying_price(100.0) == 100.0
        assert validate_strike_price(100.0) == 100.0
        assert validate_maturity(1.0) == 1.0
        assert validate_volatility(0.2) == 0.2
        assert validate_risk_free_rate(0.05) == 0.05

    def test_numeric_validators_failure(self):
        with pytest.raises(ValidationError):
            validate_underlying_price(0)
        with pytest.raises(ValidationError):
            validate_strike_price(-1)
        with pytest.raises(ValidationError):
            validate_maturity(0)
        with pytest.raises(ValidationError):
            validate_volatility(-0.1)
        with pytest.raises(ValidationError):
            validate_risk_free_rate(-0.01)

    def test_validate_quote_success(self):
        quote = {"bid": 10.0, "ask": 11.0, "underlying": 100.0}
        assert validate_quote(quote) == quote

    def test_validate_quote_missing_keys(self):
        with pytest.raises(ValidationError, match="Missing required key"):
            validate_quote({"bid": 10.0})

    def test_validate_quote_invalid_values(self):
        # Bid negative
        with pytest.raises(ValidationError, match="Bid price cannot be negative"):
            validate_quote({"bid": -1.0, "ask": 10.0, "underlying": 100.0})
        # Ask zero
        with pytest.raises(ValidationError, match="Ask price must be positive"):
            validate_quote({"bid": 5.0, "ask": 0.0, "underlying": 100.0})
        # Bid > Ask
        with pytest.raises(ValidationError, match="Bid cannot be greater than ask"):
            validate_quote({"bid": 12.0, "ask": 11.0, "underlying": 100.0})
        # Underlying zero
        with pytest.raises(ValidationError, match="Underlying price must be positive"):
            validate_quote({"bid": 10.0, "ask": 11.0, "underlying": 0.0})
