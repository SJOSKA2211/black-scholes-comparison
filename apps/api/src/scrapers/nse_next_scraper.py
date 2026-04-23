"""Scraper for NSE (National Stock Exchange of India) NIFTY options."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

import structlog
from playwright.async_api import async_playwright

from src.scrapers.base_scraper import BaseScraper

logger = structlog.get_logger(__name__)


class NSEScraper(BaseScraper):
    """Scraper for NSE (National Stock Exchange of India) NIFTY options."""

    def __init__(self, run_id: str) -> None:
        super().__init__(run_id)
        self.target_url = "https://www.nseindia.com/option-chain"

    async def scrape(self, trade_date: date) -> list[dict[str, Any]]:
        """Scrapes live NSE NIFTY option chain data."""
        logger.info("scraper_scrape_started", market="nse", run_id=self.run_id)
        scraped_data: list[dict[str, Any]] = []

        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                )
                page = await context.new_page()

                # Step 1: Establish session (NSE requires visiting home first)
                await page.goto("https://www.nseindia.com", wait_until="networkidle")
                await asyncio.sleep(2)

                # Step 2: Option chain
                await page.goto(self.target_url, wait_until="networkidle")
                await page.wait_for_selector("#optionChainTable", timeout=30000)

                # 3. Underlying Price
                underlying_element = await page.query_selector("#equity_underlyingVal")
                underlying_text = (
                    await underlying_element.inner_text() if underlying_element else "22000"
                )
                # Text is usually "UNDERLYING VALUE 22,000.00"
                underlying_price = float(underlying_text.split()[-1].replace(",", ""))

                # 4. Maturity calculation
                # NSE has an expiry date dropdown
                expiry_el = await page.query_selector("#expirySelect")
                maturity_years = 7 / 365.0  # default 1 week
                if expiry_el:
                    selected_val = await expiry_el.get_attribute("value")
                    if selected_val:
                        # Format is usually DD-MMM-YYYY (e.g., 25-Apr-2024)
                        from datetime import datetime

                        try:
                            expiry_dt = datetime.strptime(selected_val, "%d-%b-%Y").date()
                            days_to_expiry = (expiry_dt - trade_date).days
                            maturity_years = max(0.001, days_to_expiry / 365.0)
                        except ValueError:
                            pass

                # 5. Extraction logic
                rows = await page.query_selector_all("#optionChainTable tbody tr")
                for row in rows:
                    cols = await row.query_selector_all("td")
                    if len(cols) < 20:
                        continue

                    try:
                        # Strike is in Col 11
                        strike = float((await cols[11].inner_text()).replace(",", ""))

                        # CALLS (Left side): Bid in 8, Ask in 9, IV in 7
                        c_bid = float(
                            (await cols[8].inner_text()).replace("-", "0").replace(",", "")
                        )
                        c_ask = float(
                            (await cols[9].inner_text()).replace("-", "0").replace(",", "")
                        )
                        c_iv = (
                            float((await cols[7].inner_text()).replace("-", "20").replace(",", ""))
                            / 100.0
                        )

                        # PUTS (Right side): Bid in 12, Ask in 13, IV in 14
                        p_bid = float(
                            (await cols[12].inner_text()).replace("-", "0").replace(",", "")
                        )
                        p_ask = float(
                            (await cols[13].inner_text()).replace("-", "0").replace(",", "")
                        )
                        p_iv = (
                            float((await cols[14].inner_text()).replace("-", "20").replace(",", ""))
                            / 100.0
                        )

                        if c_ask > 0:
                            scraped_data.append(
                                {
                                    "underlying_price": underlying_price,
                                    "strike_price": strike,
                                    "maturity_years": maturity_years,
                                    "volatility": c_iv,
                                    "risk_free_rate": 0.07,  # RBI rate approx
                                    "option_type": "call",
                                    "is_american": False,  # NIFTY options are European
                                    "market_source": "nse",
                                    "trade_date": trade_date,
                                    "bid_price": c_bid,
                                    "ask_price": c_ask,
                                }
                            )

                        if p_ask > 0:
                            scraped_data.append(
                                {
                                    "underlying_price": underlying_price,
                                    "strike_price": strike,
                                    "maturity_years": maturity_years,
                                    "volatility": p_iv,
                                    "risk_free_rate": 0.07,
                                    "option_type": "put",
                                    "is_american": False,
                                    "market_source": "nse",
                                    "trade_date": trade_date,
                                    "bid_price": p_bid,
                                    "ask_price": p_ask,
                                }
                            )

                    except (ValueError, TypeError, IndexError):
                        continue

                logger.info(
                    "scraper_scrape_finished",
                    market="nse",
                    rows=len(scraped_data),
                    price=underlying_price,
                )
                await browser.close()

            except Exception as error:
                logger.error("scraper_scrape_failed", market="nse", error=str(error))
                raise

        return scraped_data

    async def run(self) -> None:
        """Execute the full scraper workflow (integrated with pipeline)."""
        logger.info("scraper_run_called", market="nse", run_id=self.run_id)
        # DataPipeline handles the end-to-end orchestration.
