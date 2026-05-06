"""Base class for all market data scrapers."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class BaseScraper(ABC):
    """Abstract base class for scrapers."""

    @abstractmethod
    async def scrape(self, trade_date: date) -> list[dict[str, Any]]:
        """Scrape data for the given date and return a list of records."""
        pass
