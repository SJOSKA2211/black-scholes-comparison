"""Unit tests for data validators."""

import pytest
from src.data.validators import validate_parameters, validate_quote, validate_market_source
from src.methods.base import OptionParams, OptionType
from src.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError

@pytest.mark.unit
def test_validate_parameters_success(atm_call_params: OptionParams) -> None:
    """Should not raise for valid parameters."""
    validate_parameters(atm_call_params)

@pytest.mark.unit
def test_validate_parameters_pydantic_enforcement() -> None:
    """Pydantic should catch invalid parameters during object creation."""
    with pytest.raises(PydanticValidationError):
        OptionParams(
            underlying_price=-100.0,
            strike_price=100.0,
            maturity_years=1.0,
            volatility=0.2,
            risk_free_rate=0.05,
            option_type=OptionType.CALL
        )

@pytest.mark.unit
def test_validate_quote_success() -> None:
    """Should not raise for valid quote."""
    validate_quote(10.0, 10.5)

@pytest.mark.unit
def test_validate_quote_crossed() -> None:
    """Should raise if bid > ask."""
    with pytest.raises(ValidationError, match="Bid price cannot be greater than ask"):
        validate_quote(11.0, 10.5)

@pytest.mark.unit
def test_validate_market_source_success() -> None:
    """Should not raise for allowed source."""
    validate_market_source("SPY")
    validate_market_source("NSE")

@pytest.mark.unit
def test_validate_market_source_invalid() -> None:
    """Should raise for unknown source."""
    with pytest.raises(ValidationError, match="Invalid market source"):
        validate_market_source("NYSE")
