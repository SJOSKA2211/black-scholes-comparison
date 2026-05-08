"""Data transformers for market quotes."""
from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING, Any
import structlog
from src.methods.base import OptionParameters, OptionType

if TYPE_CHECKING:
    from src.scrapers.base_scraper import RawQuote

logger = structlog.get_logger(__name__)

def calculate_maturity_years(maturity_date: date, trade_date: date | None = None) -> float:
    """Calculate maturity in years from today or trade_date."""
    if trade_date is None:
        trade_date = date.today()
    delta = maturity_date - trade_date
    return max(0.0001, delta.days / 365.25)

def transform_to_db_params(quote: RawQuote, trade_date: date) -> dict[str, Any]:
    """Transform RawQuote to dictionary for option_parameters table."""
    return {
        "underlying_price": quote.underlying_price,
        "strike_price": quote.strike_price,
        "maturity_years": calculate_maturity_years(quote.maturity_date, trade_date),
        "volatility": 0.2, # Initial guess, will be updated by IV calculator
        "risk_free_rate": 0.05, # Default, should come from a rate service
        "option_type": quote.option_type,
        "market_source": quote.data_source,
        "is_american": False
    }

def transform_to_db_market_data(quote: RawQuote, option_id: str, trade_date: date) -> dict[str, Any]:
    """Transform RawQuote to dictionary for market_data table."""
    return {
        "option_id": option_id,
        "trade_date": trade_date.isoformat(),
        "bid_price": quote.bid_price,
        "ask_price": quote.ask_price,
        "volume": 0, # yfinance doesn't always have it for all rows
        "open_interest": 0,
        "data_source": quote.data_source
    }
