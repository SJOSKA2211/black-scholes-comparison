"""Unit tests to fill coverage gaps in backend."""
from __future__ import annotations
import pytest
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock
from src.analysis.convergence import analyze_convergence_order
from src.main import lifespan
from src.data.pipeline import DataPipeline, PipelineResult
from src.scrapers.base_scraper import ScraperResult, RawQuote
from datetime import date

class AsyncContextManagerMock:
    def __init__(self, value):
        self.value = value
    async def __aenter__(self):
        return self.value
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

def create_mock_cell(text):
    cell = MagicMock()
    cell.inner_text = AsyncMock(return_value=str(text))
    return cell

@pytest.fixture
def mock_playwright():
    pw = MagicMock()
    browser = MagicMock()
    pw.chromium.launch = AsyncMock(return_value=browser)
    context = MagicMock()
    browser.new_context = AsyncMock(return_value=context)
    page = MagicMock()
    context.new_page = AsyncMock(return_value=page)
    browser.close = AsyncMock()
    page.goto = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.click = AsyncMock()
    return pw, page

@pytest.mark.unit
def test_analyze_convergence_order() -> None:
    """Verify convergence order calculation."""
    steps = np.array([100, 200, 400, 800], dtype=np.float64)
    # Order 2 convergence: error ~ (1/steps)^2
    errors = (1.0 / steps) ** 2
    order = analyze_convergence_order(errors, steps)
    assert pytest.approx(order, rel=1e-2) == 2.0

@pytest.mark.unit
async def test_lifespan_startup_failure() -> None:
    """Verify app lifespan handles startup errors gracefully."""
    mock_app = MagicMock()
    with patch("src.main.start_consumers", side_effect=Exception("Startup fail")):
        async with lifespan(mock_app):
            pass
        # Should not raise exception, but log it (verified by coverage)

@pytest.mark.unit
async def test_pipeline_persistence_failure() -> None:
    """Verify pipeline handles persistence errors in the loop."""
    mock_scraper = AsyncMock()
    quote = RawQuote(
        underlying_symbol="TEST",
        strike_price=100.0,
        maturity_date=date(2026, 1, 1),
        option_type="call",
        bid_price=10.0,
        ask_price=11.0,
        underlying_price=100.0,
        data_source="test"
    )
    mock_scraper.run.return_value = ScraperResult(
        market="test",
        date=date(2026, 1, 1),
        quotes=[quote],
        execution_seconds=0.1,
        status="success"
    )
    
    pipeline = DataPipeline("test", mock_scraper)
    
    with patch("src.data.pipeline.upsert_option_parameters", side_effect=Exception("DB fail")):
        result = await pipeline.run(date(2026, 1, 1))
        assert result.rows_inserted == 0
        assert result.status == "success" # It continues

@pytest.mark.unit
async def test_pipeline_run_failure() -> None:
    """Verify pipeline handles overall run failure."""
    mock_scraper = AsyncMock()
    mock_scraper.run.side_effect = Exception("Scrape fail")
    
    pipeline = DataPipeline("test", mock_scraper)
    result = await pipeline.run(date(2026, 1, 1))
    assert result.status == "failed"
    assert result.rows_scraped == 0

@pytest.mark.unit
def test_oauth_placeholder() -> None:
    """Verify oauth placeholder (just for coverage)."""
    from src.auth import oauth
    assert oauth.logger is not None

@pytest.mark.unit
async def test_base_scraper_timing() -> None:
    """Verify base scraper timing logic."""
    from src.scrapers.base_scraper import BaseScraper, RawQuote
    class DummyScraper(BaseScraper):
        async def _scrape(self, date): return []
    
    scraper = DummyScraper("dummy")
    res = await scraper.run(date.today())
    assert res.execution_seconds >= 0

@pytest.mark.unit
async def test_repository_list_market_data_filtering() -> None:
    """Verify market data listing with filter."""
    from src.database import repository
    from unittest.mock import MagicMock
    mock_client = MagicMock()
    with patch("src.database.repository.get_supabase", return_value=mock_client):
        # Mock query chain
        query = mock_client.table.return_value.select.return_value.order.return_value.limit.return_value
        query.eq.return_value = query
        await repository.list_market_data(market="spy")
        query.eq.assert_called_with("option_parameters.market_source", "spy")

@pytest.mark.unit
async def test_nse_scraper_error_branches(mock_playwright) -> None:
    """Verify NSE scraper error branches."""
    from src.scrapers.nse_next_scraper import NseScraper
    pw, page = mock_playwright
    scraper = NseScraper()
    
    # Branch: target_table not found after searching all tables
    page.wait_for_selector.side_effect = Exception("not found")
    page.locator.return_value.all = AsyncMock(return_value=[]) # No tables found
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=AsyncContextManagerMock(pw)):
        res = await scraper.run(date.today())
        assert res.status == "success" # It returns empty list

@pytest.mark.unit
async def test_spy_scraper_error_branches(mock_playwright) -> None:
    """Verify SPY scraper error branches."""
    from src.scrapers.spy_scraper import SpyScraper
    pw, page = mock_playwright
    scraper = SpyScraper()
    
    # Branch: Row with bad float conversion
    row = MagicMock()
    # Contract, X, Strike, X, Bid, Ask, ...
    cells = [create_mock_cell(t) for t in ["SPY260511C00700000", "X", "bad-strike", "X", "10.0", "11.0", "X", "X", "X", "X"]]
    row.locator.return_value.all = AsyncMock(return_value=cells)
    
    price_loc = MagicMock()
    price_loc.first.inner_text = AsyncMock(return_value="500.0")
    
    rows_loc = MagicMock()
    rows_loc.all = AsyncMock(return_value=[row])
    
    page.locator.side_effect = lambda sel: price_loc if "regularMarketPrice" in sel else rows_loc
    
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=AsyncContextManagerMock(pw)):
        res = await scraper.run(date.today())
        assert res.status == "success"
        assert len(res.quotes) == 0 # Skipped due to ValueError

@pytest.mark.unit
async def test_spy_scraper_low_prices(mock_playwright) -> None:
    """Verify SPY scraper filters low prices."""
    from src.scrapers.spy_scraper import SpyScraper
    pw, page = mock_playwright
    scraper = SpyScraper()
    
    row = MagicMock()
    cells = [create_mock_cell(t) for t in ["SPY260511C00700000", "X", "700.0", "X", "0.0", "11.0", "X", "X", "X", "X"]]
    row.locator.return_value.all = AsyncMock(return_value=cells)
    
    price_loc = MagicMock()
    price_loc.first.inner_text = AsyncMock(return_value="500.0")
    rows_loc = MagicMock()
    rows_loc.all = AsyncMock(return_value=[row])
    
    page.locator.side_effect = lambda sel: price_loc if "regularMarketPrice" in sel else rows_loc
    
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=AsyncContextManagerMock(pw)):
        res = await scraper.run(date.today())
        assert len(res.quotes) == 0 # Filtered due to bid=0

@pytest.mark.unit
async def test_spy_scraper_price_exception(mock_playwright) -> None:
    """Verify SPY scraper handles price selection exception."""
    from src.scrapers.spy_scraper import SpyScraper
    pw, page = mock_playwright
    scraper = SpyScraper()
    
    # Trigger Exception in price wait
    page.wait_for_selector.side_effect = lambda sel, timeout: (
        Exception("Price fail") if "regularMarketPrice" in sel else None
    )
    
    rows_loc = MagicMock()
    rows_loc.all = AsyncMock(return_value=[])
    page.locator.side_effect = lambda sel: rows_loc
    
    with patch("src.scrapers.spy_scraper.async_playwright", return_value=AsyncContextManagerMock(pw)):
        res = await scraper.run(date.today())
        assert res.status == "success" # Should log and continue with 0.0

@pytest.mark.unit
async def test_nse_scraper_fallback_loop(mock_playwright) -> None:
    """Verify NSE scraper fallback loop over tables."""
    from src.scrapers.nse_next_scraper import NseScraper
    pw, page = mock_playwright
    scraper = NseScraper()
    
    page.wait_for_selector.side_effect = Exception("not found")
    
    table1 = MagicMock()
    table1.inner_text = AsyncMock(return_value="Random Table")
    table2 = MagicMock()
    table2.inner_text = AsyncMock(return_value="Contract Name")
    # Mock tr locator for table2
    table2.locator.return_value.all = AsyncMock(return_value=[])
    
    page.locator.return_value.all = AsyncMock(return_value=[table1, table2])
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=AsyncContextManagerMock(pw)):
        res = await scraper.run(date.today())
        assert res.status == "success"

@pytest.mark.unit
async def test_nse_scraper_date_parse_error(mock_playwright) -> None:
    """Verify NSE scraper handles bad date format."""
    from src.scrapers.nse_next_scraper import NseScraper
    pw, page = mock_playwright
    scraper = NseScraper()
    
    table = MagicMock()
    row = MagicMock()
    # Contract, X, BAD-DATE, MTM, X, Prev
    cells = [create_mock_cell(t) for t in ["KCB (KCB)", "X", "bad-date", "4500.0", "X", "4400.0"]]
    row.locator.return_value.all = AsyncMock(return_value=cells)
    table.locator.return_value.all = AsyncMock(return_value=[row])
    page.locator.return_value.first = table
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=AsyncContextManagerMock(pw)):
        res = await scraper.run(date.today())
        assert res.status == "success"
        assert res.quotes[0].maturity_date == date.today()

@pytest.mark.unit
async def test_nse_scraper_tab_click_fail(mock_playwright) -> None:
    """Verify NSE scraper handles tab click failure."""
    from src.scrapers.nse_next_scraper import NseScraper
    pw, page = mock_playwright
    scraper = NseScraper()
    
    # Branch: tab click fails
    page.click.side_effect = Exception("Click failed")
    
    table = MagicMock()
    table.locator.return_value.all = AsyncMock(return_value=[])
    page.locator.return_value.first = table
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=AsyncContextManagerMock(pw)):
        await scraper.run(date.today())
        # Should continue and try to find the table anyway

@pytest.mark.unit
async def test_nse_scraper_parse_errors(mock_playwright) -> None:
    """Verify NSE scraper handles parsing errors."""
    from src.scrapers.nse_next_scraper import NseScraper
    pw, page = mock_playwright
    scraper = NseScraper()
    
    table = MagicMock()
    # Row with bad MTM price (triggers ValueError at line 89)
    row_err = MagicMock()
    cells_err = [create_mock_cell(t) for t in ["KCB (KCB)", "X", "18-Jun-2026", "bad-price", "X", "4400.0"]]
    row_err.locator.return_value.all = AsyncMock(return_value=cells_err)
    
    # Row without symbol parens (covers line 85-86 else branch)
    row_no_parens = MagicMock()
    cells_no_parens = [create_mock_cell(t) for t in ["SAFCOM", "X", "18-Jun-2026", "50.0", "X", "48.0"]]
    row_no_parens.locator.return_value.all = AsyncMock(return_value=cells_no_parens)

    table.locator.return_value.all = AsyncMock(return_value=[row_err, row_no_parens])
    page.locator.return_value.first = table
    
    with patch("src.scrapers.nse_next_scraper.async_playwright", return_value=AsyncContextManagerMock(pw)):
        res = await scraper.run(date.today())
        assert len(res.quotes) == 1
        assert res.quotes[0].underlying_symbol == "SAFCOM"
