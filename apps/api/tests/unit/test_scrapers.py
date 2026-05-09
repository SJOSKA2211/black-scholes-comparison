"""Unit tests for scrapers."""
from __future__ import annotations
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from src.scrapers.spy_scraper import SpyScraper
from src.scrapers.nse_next_scraper import NseScraper

class CM:
    def __init__(self, v): self.v = v
    async def __aenter__(self): return self.v
    async def __aexit__(self, *a): pass

def mk(t):
    c = MagicMock(); c.inner_text = AsyncMock(return_value=str(t)); return c

@pytest.fixture
def p():
    m = MagicMock(); pg = MagicMock()
    m.chromium.launch = AsyncMock(return_value=AsyncMock(new_context=AsyncMock(return_value=AsyncMock(new_page=AsyncMock(return_value=pg)))))
    pg.goto = AsyncMock(); pg.wait_for_selector = AsyncMock()
    return m, pg

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_run_success(p):
    m, pg = p; s = SpyScraper()
    pr = MagicMock(); pr.inner_text = AsyncMock(return_value="500"); pr.first = pr
    r = MagicMock(); r.locator.return_value.all = AsyncMock(return_value=[mk("SPY260511C00700000"), mk(0), mk(700), mk(0), mk(10), mk(11)])
    rows = MagicMock(); rows.all = AsyncMock(return_value=[r])
    pg.locator.side_effect = lambda sel: pr if "price" in sel or "livePrice" in sel else rows
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_price_not_found(p):
    m, pg = p; s = SpyScraper()
    pg.wait_for_selector.side_effect = Exception("timeout")
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_row_fail(p):
    m, pg = p; s = SpyScraper()
    pr = MagicMock(); pr.inner_text = AsyncMock(return_value="500"); pr.first = pr
    r = MagicMock(); r.locator.return_value.all = AsyncMock(return_value=[mk("S1"), mk("bad")]) # cells < 6
    rows = MagicMock(); rows.all = AsyncMock(return_value=[r])
    pg.locator.side_effect = lambda sel: pr if "price" in sel or "livePrice" in sel else rows
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_run_success(p):
    m, pg = p; s = NseScraper()
    h = MagicMock(inner_text=AsyncMock(return_value="Contract Name"))
    d = MagicMock(inner_text=AsyncMock(return_value="KCB (KCB)"))
    d.locator.return_value.all = AsyncMock(return_value=[mk("KCB (KCB)"), mk("0"), mk("18-Jun-2026"), mk(4500), mk(0), mk(4400)])
    h.locator.return_value.all = AsyncMock(return_value=[])
    pg.locator.return_value.all = AsyncMock(side_effect=[[h], [h, d]])
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_no_table(p):
    m, pg = p; s = NseScraper()
    pg.locator.return_value.all = AsyncMock(return_value=[])
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_row_fail(p):
    m, pg = p; s = NseScraper()
    h = MagicMock(inner_text=AsyncMock(return_value="Contract Name"))
    d = MagicMock(inner_text=AsyncMock(return_value="KCB"))
    # Make parsing fail (IndexError)
    d.locator.return_value.all = AsyncMock(return_value=[mk("KCB")]) # Less than 6 cells
    pg.locator.return_value.all = AsyncMock(side_effect=[[h], [h, d]])
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_exception_handling():
    s = SpyScraper()
    with patch("src.scrapers.spy_scraper.async_playwright", side_effect=Exception("err")):
        res = await s.run(date.today()); assert res.status == "failed"
