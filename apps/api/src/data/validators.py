"""Pydantic validators for market data, scrapes, and operational tables."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import UUID4, BaseModel, Field


class ValidationError(Exception):
    """Raised when data validation fails."""


def validate_underlying_price(price: float) -> float:
    """Validate that the underlying price is strictly positive."""
    if price <= 0:
        raise ValidationError("Underlying price must be positive")
    return float(price)


def validate_strike_price(price: float) -> float:
    """Validate that the strike price is strictly positive."""
    if price <= 0:
        raise ValidationError("Strike price must be positive")
    return float(price)


def validate_maturity(years: float) -> float:
    """Validate that maturity is strictly positive."""
    if years <= 0:
        raise ValidationError("Maturity must be positive")
    return float(years)


def validate_volatility(vol: float) -> float:
    """Validate that volatility is strictly positive."""
    if vol <= 0:
        raise ValidationError("Volatility must be positive")
    return float(vol)


def validate_risk_free_rate(rate: float) -> float:
    """Validate that the risk-free rate is non-negative."""
    if rate < 0:
        raise ValidationError("Risk-free rate cannot be negative")
    return float(rate)


def validate_quote(quote: dict[str, Any]) -> dict[str, Any]:
    """
    Validate a market quote dictionary.
    Checks for required keys and logical price relationships (bid <= ask).
    """
    required = ["bid", "ask", "underlying"]
    errors = []
    for k in required:
        if k not in quote:
            errors.append(f"Missing required key: {k}")

    if errors:
        raise ValidationError("; ".join(errors))

    if quote["bid"] < 0:
        errors.append("Bid price cannot be negative")
    if quote["ask"] <= 0:
        errors.append("Ask price must be positive")
    if quote["bid"] > quote["ask"]:
        errors.append("Bid cannot be greater than ask")
    if quote["underlying"] <= 0:
        errors.append("Underlying price must be positive")

    if errors:
        raise ValidationError("; ".join(errors))

    return quote


class OptionParamsInput(BaseModel):
    """Input model for creating option parameters."""

    underlying_price: float = Field(gt=0)
    strike_price: float = Field(gt=0)
    maturity_years: float = Field(gt=0)
    volatility: float = Field(gt=0)
    risk_free_rate: float = Field(ge=0)
    option_type: Literal["call", "put"]
    is_american: bool = False
    market_source: Literal["synthetic", "spy", "nse"]


class MarketDataInput(BaseModel):
    """Input model for market price data."""

    option_id: UUID4
    trade_date: date
    bid_price: float = Field(ge=0)
    ask_price: float = Field(ge=0)
    volume: int = Field(default=0, ge=0)
    open_interest: int = Field(default=0, ge=0)
    implied_vol: float | None = None
    data_source: Literal["spy", "nse"]


class ScraperRunInput(BaseModel):
    """Operational model for tracking scraper execution runs."""

    market: str
    scraper_class: str
    status: Literal["running", "success", "partial", "failed"] = "running"
    triggered_by: UUID4 | None = None


class AuditLogInput(BaseModel):
    """Operational model for pipeline audit logging."""

    pipeline_run_id: UUID4
    step_name: str
    status: str
    rows_affected: int = 0
    message: str | None = None


class NotificationInput(BaseModel):
    """Operational model for system notifications."""

    user_id: UUID4
    title: str
    body: str
    severity: Literal["info", "warning", "error", "critical"] = "info"
    channel: Literal["in_app", "email", "push"] = "in_app"
    action_url: str | None = None
