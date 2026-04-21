"""Pydantic validators for market data, scrapes, and operational tables."""
from __future__ import annotations
from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, UUID4
 
class OptionParamsInput(BaseModel):
    underlying_price: float = Field(gt=0)
    strike_price: float = Field(gt=0)
    maturity_years: float = Field(gt=0)
    volatility: float = Field(gt=0)
    risk_free_rate: float = Field(ge=0)
    option_type: Literal["call", "put"]
    is_american: bool = False
    market_source: Literal["synthetic", "spy", "nse"]
 
class MarketDataInput(BaseModel):
    option_id: UUID4
    trade_date: date
    bid_price: float = Field(ge=0)
    ask_price: float = Field(ge=0)
    volume: Optional[int] = Field(default=0, ge=0)
    open_interest: Optional[int] = Field(default=0, ge=0)
    implied_vol: Optional[float] = None
    data_source: Literal["spy", "nse"]
 
class ScraperRunInput(BaseModel):
    market: str
    scraper_class: str
    status: Literal["running", "success", "partial", "failed"] = "running"
    triggered_by: Optional[UUID4] = None
 
class ScraperRunUpdate(BaseModel):
    status: Literal["running", "success", "partial", "failed"]
    finished_at: Optional[datetime] = None
    rows_scraped: int = 0
    rows_validated: int = 0
    rows_inserted: int = 0
    error_count: int = 0
 
class AuditLogInput(BaseModel):
    pipeline_run_id: UUID4
    step_name: str
    status: str
    rows_affected: int = 0
    message: Optional[str] = None
 
class NotificationInput(BaseModel):
    user_id: UUID4
    title: str
    body: str
    severity: Literal["info", "warning", "error", "critical"] = "info"
    channel: Literal["in_app", "email", "push"] = "in_app"
    action_url: Optional[str] = None
 
class ValidationMetricsInput(BaseModel):
    option_id: UUID4
    method_result_id: UUID4
    absolute_error: float = Field(ge=0)
    relative_pct_error: float
    mape: float
    market_deviation: float
