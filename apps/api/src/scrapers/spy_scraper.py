"""Scraper for SPY (S&P 500 ETF) option data using Playwright."""

from __future__ import annotations

from datetime import date, datetime

import structlog
from playwright.async_api import async_playwright

from src.scrapers.base_scraper import BaseScraper, RawQuote

logger = structlog.get_logger(__name__)


class SpyScraper(BaseScraper):
    """Scraper for SPY options using Playwright."""

    def __init__(self) -> None:
        super().__init__(market_name="spy")

    async def _scrape(self, trade_date: date) -> list[RawQuote]:
        """Fetch SPY option chain via Playwright."""
        quotes: list[RawQuote] = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                )
            )
            page = await context.new_page()

            url = "https://finance.yahoo.com/quote/SPY/options"
            logger.info("fetching_spy_options", url=url)

            try:
                await page.goto(url, timeout=60000)

                # Wait for the price to load
                price_selector = "[data-test='qsp-price'], .livePrice"
                try:
                    await page.wait_for_selector(price_selector, timeout=10000)
                    price_text = await page.locator(price_selector).first.inner_text()
                    underlying_price = float(price_text.replace(",", ""))
                except Exception:
                    # Fallback or log
                    logger.warning("spy_price_not_found_using_default")
                    underlying_price = 0.0

                # Wait for the table
                table_selector = "table"
                await page.wait_for_selector(table_selector, timeout=30000)

                rows = await page.locator("table tbody tr").all()
                logger.info("spy_rows_found", count=len(rows))

                for row in rows:
                    cells = await row.locator("td").all()
                    if len(cells) < 6:
                        continue

                    # Contract Name (contains expiry info), Strike, Last, Bid, Ask
                    contract = await cells[0].inner_text()
                    strike_text = await cells[2].inner_text()
                    bid_text = await cells[4].inner_text()
                    ask_text = await cells[5].inner_text()

                    try:
                        # Extract expiry from contract name: SPY260511C00700000 -> 26-05-11
                        # Format: SYMBOL + YYMMDD + TYPE + STRIKE
                        expiry_str = contract[3:9]
                        expiry_date = datetime.strptime(expiry_str, "%y%m%d").date()
                        opt_type = "call" if "C" in contract[9:11] else "put"

                        bid = float(bid_text.replace(",", ""))
                        ask = float(ask_text.replace(",", ""))
                        strike = float(strike_text.replace(",", ""))

                        if bid <= 0 or ask <= 0:
                            continue

                        quotes.append(
                            RawQuote(
                                underlying_symbol="SPY",
                                strike_price=strike,
                                maturity_date=expiry_date,
                                option_type=opt_type,
                                bid_price=bid,
                                ask_price=ask,
                                underlying_price=underlying_price,
                                data_source="spy",
                            )
                        )
                    except (ValueError, IndexError):
                        continue

                await browser.close()
            except Exception as e:
                logger.error("spy_scrape_failed", error=str(e))
                await browser.close()
                # Don't re-raise, return what we have

        return quotes
