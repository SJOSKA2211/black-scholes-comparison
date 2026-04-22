"""Base scraper interface."""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Dict, Any

class BaseScraper(ABC):
    """Abstract base class for all market data scrapers."""

    def __init__(self, run_id: str):
        self.run_id = run_id

    @abstractmethod
    async def scrape(self, trade_date: date) -> List[Dict[str, Any]]:
        """Scrapes raw data for the given date and returns a list of dictionaries."""
        pass

    @abstractmethod
    async def run(self) -> None:
        """Execute the full scraper workflow (integrated with pipeline)."""
        pass
