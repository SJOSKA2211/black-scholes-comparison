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
    c = MagicMock()
    c.inner_text = AsyncMock(return_value=str(t))
    return c

@pytest.fixture
def p():
    m = MagicMock()
    browser = MagicMock()
    m.chromium.launch = AsyncMock(return_value=browser)
    context = MagicMock()
    browser.new_context = AsyncMock(return_value=context)
    page = MagicMock()
    context.new_page = AsyncMock(return_value=page)
    browser.close = AsyncMock()
    page.goto = AsyncMock()
    page.wait_for_selector = AsyncMock()
    loc = MagicMock(); loc.all = AsyncMock(return_value=[])
    page.locator.return_value = loc
    return m, page, loc

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_run_success(p):
    m, pg, _ = p; s = SpyScraper()
    pr = MagicMock(); pr.inner_text = AsyncMock(return_value="500"); pr.first = pr
    r = MagicMock(); r.locator.return_value.all = AsyncMock(return_value=[mk("SPY260511C00700000"), mk(0), mk(700), mk(0), mk(10), mk(11)])
    rows = MagicMock(); rows.all = AsyncMock(return_value=[r])
    pg.locator.side_effect = lambda sel: pr if "price" in sel or "livePrice" in sel else rows
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_edge_cases(p):
    m, pg, _ = p; s = SpyScraper()
    pr = MagicMock(); pr.inner_text = AsyncMock(return_value="500"); pr.first = pr
    # Row with bid=0 (line 83)
    r1 = MagicMock(); r1.locator.return_value.all = AsyncMock(return_value=[mk("S1"), mk(0), mk(700), mk(0), mk(0), mk(11)])
    # Row with error (line 97-98)
    r2 = MagicMock(); r2.locator.side_effect = Exception("err")
    rows = MagicMock(); rows.all = AsyncMock(return_value=[r1, r2])
    pg.locator.side_effect = lambda sel: pr if "price" in sel or "livePrice" in sel else rows
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_price_not_found(p):
    m, pg, _ = p; s = SpyScraper()
    pg.wait_for_selector.side_effect = Exception("timeout")
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_run_success(p):
    m, pg, loc = p; s = NseScraper()
    h = mk("Contract Name")
    d = mk("KCB (KCB)")
    # Successful row with (parentheses) - covers line 76-79
    d.locator.return_value.all = AsyncMock(return_value=[mk("KCB (KCB)"), mk("0"), mk("18-Jun-2026"), mk(4500), mk(0), mk(4400)])
    # Invalid date row - covers line 86-87
    d2 = mk("KCB (KCB)")
    d2.locator.return_value.all = AsyncMock(return_value=[mk("KCB (KCB)"), mk("0"), mk("bad-date"), mk(4500), mk(0), mk(4400)])
    # Skip row - covers line 71
    d3 = mk("Contract Name")
    d3.locator.return_value.all = AsyncMock(return_value=[mk("Contract Name")])
    # Parsing error row - covers line 101-103
    d4 = mk("ERR")
    d4.locator.return_value.all = AsyncMock(return_value=[mk("ERR"), mk("0"), mk("18-Jun-2026"), mk("bad-num"), mk(0), mk(4400)])
    
    rows_loc = MagicMock(); rows_loc.all = AsyncMock(return_value=[h, d, d2, d3, d4])
    h.locator.side_effect = lambda sel: rows_loc if sel == "tr" else MagicMock(all=AsyncMock(return_value=[]))
    loc.all.return_value = [h]
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_no_table(p):
    m, pg, loc = p; s = NseScraper()
    # Covers line 56-58
    loc.all.return_value = []
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "success"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_fail_cases(p):
    m, pg, loc = p; s = NseScraper()
    # Covers line 106-109
    pg.goto.side_effect = Exception("err")
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert res.status == "failed"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_exception_handling():
    s = SpyScraper()
    with patch("src.scrapers.spy_scraper.async_playwright", side_effect=Exception("err")):
        res = await s.run(date.today()); assert res.status == "failed"
