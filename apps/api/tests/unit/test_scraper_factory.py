"""Unit tests for scraper factory."""
from __future__ import annotations
import pytest
from src.scrapers.scraper_factory import get_scraper
from src.scrapers.spy_scraper import SpyScraper
from src.scrapers.nse_next_scraper import NseScraper

@pytest.mark.unit
def test_get_scraper_spy() -> None:
    """Verify SPY scraper creation."""
    scraper = get_scraper("spy")
    assert isinstance(scraper, SpyScraper)

@pytest.mark.unit
def test_get_scraper_nse() -> None:
    """Verify NSE scraper creation."""
    scraper = get_scraper("nse")
    assert isinstance(scraper, NseScraper)

@pytest.mark.unit
def test_get_scraper_invalid() -> None:
    """Verify error for unknown market."""
    with pytest.raises(ValueError, match="Unknown market"):
        get_scraper("invalid")
