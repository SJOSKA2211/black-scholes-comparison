"""Base class for market data scrapers."""
from __future__ import annotations
import time
from abc import ABC, abstractmethod
from datetime import date
import structlog
from pydantic import BaseModel
from src.metrics import SCRAPE_DURATION, SCRAPE_RUNS_TOTAL

logger = structlog.get_logger(__name__)

class RawQuote(BaseModel):
    """Raw market data quote from a scraper."""
    underlying_symbol: str
    strike_price: float
    maturity_date: date
    option_type: str  # call/put
    bid_price: float
    ask_price: float
    underlying_price: float
    data_source: str

class ScraperResult(BaseModel):
    """Result of a scraper run."""
    quotes: list[RawQuote]
    execution_seconds: float
    market: str
    status: str

class BaseScraper(ABC):
    """Abstract base class for scrapers."""
    
    def __init__(self, market_name: str) -> None:
        self.market_name = market_name

    @abstractmethod
    async def _scrape(self, trade_date: date) -> list[RawQuote]:
        """Internal scraping logic."""
        pass

    async def run(self, trade_date: date) -> ScraperResult:
        """Execute scraper and record metrics."""
        start_time = time.perf_counter()
        try:
            quotes = await self._scrape(trade_date)
            duration = time.perf_counter() - start_time
            
            SCRAPE_RUNS_TOTAL.labels(market=self.market_name, status="success").inc()
            SCRAPE_DURATION.labels(market=self.market_name).observe(duration)
            
            return ScraperResult(
                quotes=quotes,
                execution_seconds=duration,
                market=self.market_name,
                status="success"
            )
        except Exception as error:
            duration = time.perf_counter() - start_time
            SCRAPE_RUNS_TOTAL.labels(market=self.market_name, status="failed").inc()
            logger.error("scraper_failed", market=self.market_name, error=str(error))
            raise
