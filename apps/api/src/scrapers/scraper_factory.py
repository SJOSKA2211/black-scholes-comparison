"""Factory for creating scraper instances."""

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.nse_next_scraper import NseNextScraper
from src.scrapers.spy_scraper import SpyScraper


def get_scraper(market: str) -> BaseScraper:
    """Return a scraper instance for the given market."""
    market = market.lower()
    if market == "spy":
        return SpyScraper()
    if market == "nse":
        return NseNextScraper()
    raise ValueError(f"No scraper implemented for market: {market}")
