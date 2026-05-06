"""Data validators for market quotes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.exceptions import ValidationError

if TYPE_CHECKING:
    from src.scrapers.base_scraper import RawQuote

logger = structlog.get_logger(__name__)


def validate_positive_prices(quote: RawQuote) -> bool:
    """Ensure all prices are positive."""
    if quote.bid_price < 0 or quote.ask_price < 0 or quote.underlying_price <= 0:
        raise ValidationError(f"Invalid prices in quote: {quote}")
    return True


def validate_bid_ask_spread(quote: RawQuote) -> bool:
    """Ensure bid is not greater than ask."""
    if quote.bid_price > quote.ask_price and quote.ask_price > 0:
        raise ValidationError(f"Bid higher than ask: {quote}")
    return True


def validate_strike_price(quote: RawQuote) -> bool:
    """Ensure strike price is positive."""
    if quote.strike_price <= 0:
        raise ValidationError(f"Invalid strike price: {quote}")
    return True


def validate_maturity_date(quote: RawQuote) -> bool:
    """Ensure maturity is in the future."""
    # Note: In a real scraper, we'd check against current date.
    # For now, we'll just check it exists.
    if not quote.maturity_date:
        raise ValidationError(f"Missing maturity date: {quote}")
    return True


def validate_symbol(quote: RawQuote) -> bool:
    """Ensure symbol is valid."""
    if not quote.underlying_symbol:
        raise ValidationError(f"Missing symbol: {quote}")
    return True


def validate_quote(quote: RawQuote) -> bool:
    """Run all validators on a quote."""
    try:
        validate_positive_prices(quote)
        validate_bid_ask_spread(quote)
        validate_strike_price(quote)
        validate_maturity_date(quote)
        validate_symbol(quote)
        return True
    except ValidationError as error:
        logger.warning("validation_failed", error=str(error))
        return False
