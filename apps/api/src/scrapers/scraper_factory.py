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

def get_scraper(market: str) -> BaseScraper:
    """Returns an initialized scraper instance for the given market."""
    scraper_class = SCRAPERS.get(market.lower())
    if not scraper_class:
        raise ValueError(f"Unknown market: {market}")
    # Defaulting to no-run_id for the factory function for now
    return scraper_class()
