from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


class MarketDataInput(BaseModel):
    underlying_price: float = Field(gt=0)
    strike_price: float = Field(gt=0)
    maturity_years: float = Field(gt=0)
    volatility: Optional[float] = None
    risk_free_rate: float = Field(default=0.05, ge=0)
    option_type: Literal["call", "put"]
    is_american: bool = False
    market_source: Literal["spy", "nse"]

    trade_date: date
    bid_price: float = Field(ge=0)
    ask_price: float = Field(gt=0)
    volume: int = Field(default=0, ge=0)
    open_interest: int = Field(default=0, ge=0)
    data_source: Literal["spy", "nse"]


class ScraperRunUpdate(BaseModel):
    status: Literal["running", "success", "partial", "failed"]
    finished_at: Optional[str] = None
    rows_scraped: int = 0
    rows_validated: int = 0
    rows_inserted: int = 0
    error_count: int = 0
