"""Base class for all market data scrapers."""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
import pandas as pd


class BaseScraper(ABC):
    """Abstract base class for scraping market data."""

    @abstractmethod
    async def scrape(self, trade_date: date) -> pd.DataFrame:
        """
        Scrape data for a specific date.
        Returns a DataFrame with columns: 
        [underlying_price, strike_price, maturity_years, option_type, bid_price, ask_price]
        """
        pass
