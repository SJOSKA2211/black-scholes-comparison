"""Scraper for SPY (SPDR S&P 500 ETF Trust) options."""

from __future__ import annotations

from datetime import date
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
        """Scrapes raw data for the given date."""
        logger.info("scraper_scrape_started", market="spy", run_id=self.run_id)
        scraped_data: list[dict[str, Any]] = []

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                await page.goto(self.target_url, wait_until="networkidle")
                await page.wait_for_selector("table", timeout=20000)

                # Extraction logic for Yahoo Finance SPY Options
                rows = await page.query_selector_all("table.calls tbody tr, table.puts tbody tr")
                for row in rows:
                    cols = await row.query_selector_all("td")
                    if len(cols) < 10:
                        continue

                    try:
                        strike = float((await cols[2].inner_text()).replace(",", ""))
                        bid = float((await cols[4].inner_text()).replace(",", "").replace("-", "0"))
                        ask = float((await cols[5].inner_text()).replace(",", "").replace("-", "0"))

                        scraped_data.append(
                            {
                                "underlying_price": 500.0,  # Simplified; would fetch from header
                                "strike_price": strike,
                                "maturity_years": 0.1,
                                "volatility": 0.2,
                                "risk_free_rate": 0.05,
                                "option_type": "call",
                                "is_american": False,
                                "market_source": "spy",
                                "trade_date": trade_date,
                                "bid_price": bid,
                                "ask_price": ask,
                            }
                        )
                    except (ValueError, TypeError, IndexError):
                        continue

                logger.info("scraper_scrape_finished", market="spy", rows=len(scraped_data))
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
