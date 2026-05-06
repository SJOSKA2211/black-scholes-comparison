"""Factory for creating scraper instances."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.scrapers.nse_next_scraper import NseScraper
from src.scrapers.spy_scraper import SpyScraper

if TYPE_CHECKING:
    from src.scrapers.base_scraper import BaseScraper


def get_scraper(market: str) -> BaseScraper:
    """Return the scraper for the specified market."""
    if market.lower() == "spy":
        return SpyScraper()
    elif market.lower() == "nse":
        return NseScraper()
    else:
        raise ValueError(f"Unknown market: {market}")
