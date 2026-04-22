"""Factory for creating scraper instances."""

from __future__ import annotations

from typing import ClassVar

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.nse_next_scraper import NSEScraper
from src.scrapers.spy_scraper import SPYScraper


class ScraperFactory:
    """Factory to retrieve scraper classes by market identifier."""

    _SCRAPERS: ClassVar[dict[str, type[BaseScraper]]] = {
        "spy": SPYScraper,
        "nse": NSEScraper,
    }

    @classmethod
    def get_scraper(cls, market: str, run_id: str) -> BaseScraper:
        """Returns an initialized scraper instance for the given market."""
        scraper_class = cls._SCRAPERS.get(market.lower())
        if not scraper_class:
            raise ValueError(f"Unknown market: {market}")
        return scraper_class(run_id=run_id)
