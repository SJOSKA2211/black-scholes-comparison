"""Scraper for SPY (SPDR S&P 500 ETF Trust) options."""

from __future__ import annotations

from datetime import UTC, date
from typing import Any

import structlog
from playwright.async_api import async_playwright

from src.scrapers.base_scraper import BaseScraper

logger = structlog.get_logger(__name__)


class SPYScraper(BaseScraper):
    """Scraper for SPY (SPDR S&P 500 ETF Trust) options."""

    def __init__(self, run_id: str) -> None:
        super().__init__(run_id)
        self.target_url = "https://finance.yahoo.com/quote/SPY/options"

    async def scrape(self, trade_date: date) -> list[dict[str, Any]]:
        """Scrapes live SPY option chain data from Yahoo Finance."""
        logger.info("scraper_scrape_started", market="spy", run_id=self.run_id)
        scraped_data: list[dict[str, Any]] = []

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                ua = (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                context = await browser.new_context(user_agent=ua)
                page = await context.new_page()

                await page.goto(self.target_url, wait_until="domcontentloaded")
                await page.wait_for_selector("table", timeout=30000)

                # 1. Underlying Price
                # Try multiple selectors for price (Yahoo UI changes)
                price_selectors = [
                    'fin-streamer[data-field="regularMarketPrice"][data-symbol="SPY"]',
                    ".livePrice",
                    "#quote-header-info fin-streamer",
                ]
                underlying_price = 500.0  # fallback
                for sel in price_selectors:
                    el = await page.query_selector(sel)
                    if el:
                        text = await el.inner_text()
                        try:
                            underlying_price = float(text.replace(",", ""))
                            break
                        except ValueError:
                            continue

                # 2. Maturity calculation
                # Yahoo Finance has a select box for expiries
                expiry_el = await page.query_selector(
                    'div[data-test="overlay-container"] + div select, .controls select'
                )
                maturity_years = 0.1  # fallback
                if expiry_el:
                    # Current date vs selected expiry date
                    # For simplicity, we extract the timestamp if available in value
                    val = await expiry_el.get_attribute("value")
                    if val and val.isdigit():
                        expiry_ts = int(val)
                        from datetime import datetime

                        expiry_dt = datetime.fromtimestamp(expiry_ts, tz=UTC).date()
                        days_to_expiry = (expiry_dt - trade_date).days
                        maturity_years = max(0.001, days_to_expiry / 365.0)

                # 3. Extraction logic for Table Rows
                rows = await page.query_selector_all("table tbody tr")
                for row in rows:
                    cols = await row.query_selector_all("td")
                    if len(cols) < 10:
                        continue

                    try:
                        # Col 2: Strike, Col 3: Last Price, Col 4: Bid, Col 5: Ask
                        strike = float((await cols[2].inner_text()).replace(",", ""))
                        bid = float((await cols[4].inner_text()).replace(",", "").replace("-", "0"))
                        ask = float((await cols[5].inner_text()).replace(",", "").replace("-", "0"))

                        # IV from Col 10 (if available)
                        iv_text = (
                            (await cols[10].inner_text())
                            .replace("%", "")
                            .replace(",", "")
                            .replace("-", "20")
                        )
                        volatility = float(iv_text) / 100.0 if iv_text else 0.2

                        if ask > 0:
                            scraped_data.append(
                                {
                                    "underlying_price": underlying_price,
                                    "strike_price": strike,
                                    "maturity_years": maturity_years,
                                    "volatility": volatility,
                                    "risk_free_rate": 0.05,  # Treasury rate approx
                                    "option_type": (
                                        "call"
                                        if "calls"
                                        in (
                                            await row.evaluate(
                                                "el => el.closest('table').className"
                                            )
                                        )
                                        else "put"
                                    ),
                                    "is_american": True,  # SPY options are American
                                    "market_source": "spy",
                                    "trade_date": trade_date,
                                    "bid_price": bid,
                                    "ask_price": ask,
                                }
                            )
                    except (ValueError, TypeError, IndexError):
                        continue

                logger.info(
                    "scraper_scrape_finished",
                    market="spy",
                    rows=len(scraped_data),
                    price=underlying_price,
                )
                await browser.close()

            except Exception as error:
                logger.error("scraper_scrape_failed", market="spy", error=str(error))
                raise

        return scraped_data

    async def run(self) -> None:
        """Execute the full scraper workflow (integrated with pipeline)."""
        logger.info("scraper_run_called", market="spy", run_id=self.run_id)
        # In this architecture, DataPipeline calls scrape() directly.
        # This method satisfies the BaseScraper interface.
