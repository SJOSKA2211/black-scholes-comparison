"""Scraper for NSE (National Stock Exchange of India) NIFTY options."""
from __future__ import annotations
import asyncio
from datetime import date, datetime
from typing import List, Dict, Any
import structlog
from playwright.async_api import async_playwright
from src.scrapers.base_scraper import BaseScraper

logger = structlog.get_logger(__name__)

class NSEScraper(BaseScraper):
    """Scraper for NSE (National Stock Exchange of India) NIFTY options."""

    def __init__(self, run_id: str):
        super().__init__(run_id)
        self.target_url = "https://www.nseindia.com/option-chain"

    async def scrape(self, trade_date: date) -> List[Dict[str, Any]]:
        """Scrapes raw data for the given date."""
        logger.info("scraper_scrape_started", market="nse", run_id=self.run_id)
        scraped_data: List[Dict[str, Any]] = []

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                # Step 1: Establish session
                await page.goto("https://www.nseindia.com", wait_until="networkidle")
                await asyncio.sleep(2)

                # Step 2: Option chain
                await page.goto(self.target_url, wait_until="networkidle")
                await page.wait_for_selector("#optionChainTable", timeout=20000)

                underlying_element = await page.query_selector("#equity_underlyingVal")
                underlying_text = (
                    await underlying_element.inner_text() if underlying_element else "22000"
                )
                underlying_price = float(underlying_text.split()[-1].replace(",", ""))

                rows = await page.query_selector_all("#optionChainTable tbody tr")

                for row in rows:
                    cols = await row.query_selector_all("td")
                    if len(cols) < 20:
                        continue

                    try:
                        strike = float((await cols[11].inner_text()).replace(",", ""))
                        call_bid = float(
                            (await cols[8].inner_text()).replace("-", "0").replace(",", "")
                        )
                        call_ask = float(
                            (await cols[9].inner_text()).replace("-", "0").replace(",", "")
                        )

                        if call_ask > 0:
                            scraped_data.append(
                                {
                                    "underlying_price": underlying_price,
                                    "strike_price": strike,
                                    "maturity_years": 7 / 365.0,
                                    "volatility": 0.2,
                                    "risk_free_rate": 0.07,
                                    "option_type": "call",
                                    "is_american": False,
                                    "market_source": "nse",
                                    "trade_date": trade_date,
                                    "bid_price": call_bid,
                                    "ask_price": call_ask,
                                }
                            )
                    except (ValueError, TypeError):
                        continue

                logger.info("scraper_scrape_finished", market="nse", rows=len(scraped_data))
                await browser.close()

            except Exception as e:
                logger.error("scraper_scrape_failed", market="nse", error=str(e))
                raise
                
        return scraped_data

    async def run(self) -> None:
        """Required by BaseScraper but logic is in DataPipeline."""
        pass
