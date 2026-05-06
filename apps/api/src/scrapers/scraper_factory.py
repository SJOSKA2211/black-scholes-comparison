"""Factory for creating scraper instances."""
from __future__ import annotations
from typing import Any
from src.scrapers.base_scraper import BaseScraper
from src.scrapers.nse_next_scraper import NSEScraper
from src.scrapers.spy_scraper import SPYScraper

SCRAPERS: dict[str, type[BaseScraper]] = {
    "spy": SPYScraper,
    "nse": NSEScraper,
}

class ScraperFactory:
    """Factory for creating scraper instances."""
    
    @staticmethod
    def get_scraper(market: str, run_id: str | None = None) -> BaseScraper:
        """Returns an initialized scraper instance for the given market."""
        scraper_class = SCRAPERS.get(market.lower())
        if not scraper_class:
            raise ValueError(f"Unknown market: {market}")
        
        # Pass run_id if the constructor supports it
        try:
            return scraper_class(run_id=run_id)
        except TypeError:
            return scraper_class()

def get_scraper(market: str) -> BaseScraper:
    """Returns an initialized scraper instance for the given market."""
    return ScraperFactory.get_scraper(market)
