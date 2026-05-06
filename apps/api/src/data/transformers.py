"""Data transformers for market quotes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.methods.base import OptionParameters, OptionType

if TYPE_CHECKING:
    from src.scrapers.base_scraper import RawQuote

logger = structlog.get_logger(__name__)


def calculate_mid_price(quote: RawQuote) -> float:
    """Calculate the mid-price from bid and ask."""
    return (quote.bid_price + quote.ask_price) / 2


def transform_to_option_parameters(quote: RawQuote, risk_free_rate: float) -> OptionParameters:
    """Convert a raw quote to OptionParameters."""
    # Maturity years calculation (dummy logic for now)
    maturity_years = 1.0  # Placeholder

    return OptionParameters(
        underlying_price=quote.underlying_price,
        strike_price=quote.strike_price,
        maturity_years=maturity_years,
        volatility=0.2,  # Placeholder, will be updated by IV inversion
        risk_free_rate=risk_free_rate,
        option_type=OptionType(quote.option_type),
        is_american=False,
    )
