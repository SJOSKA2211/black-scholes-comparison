"""Unit tests for pure logic components (No Mocks).
"""

import pytest
from src.scrapers.scraper_factory import ScraperFactory
from src.websocket.channels import ALLOWED_CHANNELS

@pytest.mark.unit
def test_scraper_factory():
    s = ScraperFactory.get_scraper("spy", "run-1")
    assert s.run_id == "run-1"
    with pytest.raises(ValueError):
        ScraperFactory.get_scraper("invalid", "run-1")

@pytest.mark.unit
def test_allowed_channels():
    assert "experiments" in ALLOWED_CHANNELS
    assert "scrapers" in ALLOWED_CHANNELS
