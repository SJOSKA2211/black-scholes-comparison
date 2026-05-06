"""Data validation logic for market data and option parameters."""

from src.exceptions import ValidationError
from src.methods.base import OptionParams


def validate_parameters(params: OptionParams) -> None:
    """Validate option parameters according to business rules."""
    if params.underlying_price <= 0:
        raise ValidationError("Underlying price must be positive.")
    if params.strike_price <= 0:
        raise ValidationError("Strike price must be positive.")
    if params.maturity_years <= 0:
        raise ValidationError("Maturity years must be positive.")
    if params.volatility <= 0:
        raise ValidationError("Volatility must be positive.")
    if params.risk_free_rate < 0:
        raise ValidationError("Risk-free rate cannot be negative.")


def validate_quote(bid: float, ask: float) -> None:
    """Validate market bid/ask quotes."""
    if bid < 0 or ask < 0:
        raise ValidationError("Market prices cannot be negative.")
    if bid > ask and ask != 0:
        raise ValidationError("Bid price cannot be greater than ask price.")


def validate_market_source(source: str) -> None:
    """Validate the data source name."""
    allowed = ["spy", "nse", "synthetic"]
    if source.lower() not in allowed:
        raise ValidationError(f"Invalid market source: {source}. Allowed: {allowed}")
