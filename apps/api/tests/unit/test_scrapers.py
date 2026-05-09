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
    sl = MagicMock(); sl.all = AsyncMock(return_value=[]); c.locator.return_value = sl
    return c

@pytest.fixture
def p():
    m = MagicMock(); b = MagicMock(); c = MagicMock(); pg = MagicMock()
    m.chromium.launch = AsyncMock(return_value=b); b.new_context = AsyncMock(return_value=c); c.new_page = AsyncMock(return_value=pg)
    b.close = AsyncMock(); pg.goto = AsyncMock(); pg.wait_for_selector = AsyncMock(); pg.click = AsyncMock()
    l = MagicMock(); l.first = l; l.all = AsyncMock(return_value=[]); l.inner_text = AsyncMock(return_value=""); pg.locator.return_value = l
    sl = MagicMock(); sl.all = AsyncMock(return_value=[]); l.locator.return_value = sl
    return m, pg, l

@pytest.mark.unit
@pytest.mark.asyncio
async def test_spy_scraper_coverage(p):
    m, pg, l = p; s = SpyScraper()
    pr = MagicMock(); pr.first = pr; pr.inner_text = AsyncMock(return_value="500")
    r = MagicMock(); r.locator.return_value.all = AsyncMock(return_value=[mk("SPY260511C00700000"), mk(0), mk(700), mk(0), mk(10), mk(11), mk(0), mk(0), mk(0), mk(0)])
    rs = MagicMock(); rs.all = AsyncMock(return_value=[r, MagicMock(locator=MagicMock(return_value=MagicMock(all=AsyncMock(return_value=[]))))])
    pg.locator.side_effect = lambda sel: pr if "regularMarketPrice" in sel else rs
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert len(res.quotes) == 1

@pytest.mark.unit
@pytest.mark.asyncio
async def test_nse_scraper_coverage(p):
    m, pg, l = p; s = NseScraper()
    # Trigger line 50: tab click fail
    pg.click.side_effect = Exception("tab fail")
    # Mock fallback to cover lines 60-65
    pg.wait_for_selector.side_effect = Exception("selector fail")
    t = MagicMock(); t.inner_text = AsyncMock(return_value="Contract Name")
    l.all = AsyncMock(return_value=[t])
    
    # Rows in t
    # d1: success with (
    d1 = MagicMock(); d1.locator.return_value.all = AsyncMock(return_value=[mk("KCB (KCB)"), mk(0), mk("18-Jun-2026"), mk(45), mk(0), mk(44)])
    # d2: success without ( to cover line 86 branch
    d2 = MagicMock(); d2.locator.return_value.all = AsyncMock(return_value=[mk("SAFCOM"), mk(0), mk("18-Jun-2026"), mk(10), mk(0), mk(11)])
    # d3: bad date -> fallback to trade_date (line 98)
    d3 = MagicMock(); d3.locator.return_value.all = AsyncMock(return_value=[mk("EQ (SAF)"), mk(0), mk("bad-date"), mk(45), mk(0), mk(44)])
    # d4: row parse failed (ValueError) (line 113)
    d4 = MagicMock(); d4.locator.return_value.all = AsyncMock(return_value=[mk("FAIL (F)"), mk(0), mk("18-Jun-2026"), mk("bad-float"), mk(0), mk(44)])
    # d_short: len < 6
    d_short = MagicMock(); d_short.locator.return_value.all = AsyncMock(return_value=[mk(0)])
    # d_skip: header row
    d_skip = MagicMock(); d_skip.locator.return_value.all = AsyncMock(return_value=[mk("Contract Name"), mk(0), mk(0), mk(0), mk(0), mk(0)])
    
    rows_loc = MagicMock(); rows_loc.all = AsyncMock(return_value=[d1, d2, d3, d4, d_short, d_skip])
    t.locator.return_value = rows_loc
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=CM(m)):
        res = await s.run(date.today()); assert len(res.quotes) == 3

@pytest.mark.unit
@pytest.mark.asyncio
async def test_scrapers_fail_coverage(p):
    m, pg, l = p; s1 = SpyScraper(); s2 = NseScraper()
    pg.goto.side_effect = Exception("fail")
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=CM(m)):
        await s1.run(date.today())
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=CM(m)):
        await s2.run(date.today())
    # Cover no table found
    pg.goto.side_effect = None; l.all = AsyncMock(return_value=[])
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=CM(m)):
        await s2.run(date.today())
