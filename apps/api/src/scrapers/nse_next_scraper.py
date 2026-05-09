"""Scraper for NSE (Nairobi Securities Exchange) derivatives using Playwright."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from playwright.async_api import async_playwright

from src.scrapers.base_scraper import BaseScraper, RawQuote

if TYPE_CHECKING:
    from datetime import date

logger = structlog.get_logger(__name__)


class NseScraper(BaseScraper):
    """Scrapes NSE derivatives data from the official statistics page."""

    def __init__(self) -> None:
        super().__init__("nse")

    async def _scrape(self, trade_date: date) -> list[RawQuote]:
        """Scrape NSE derivatives data."""
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

            url = "https://www.nse.co.ke/dataservices/market-statistics/"
            logger.info("fetching_nse_statistics", url=url)

            try:
                await page.goto(url, timeout=60000)

                # Use the exact CSS selector for the Derivatives Statistics tab
                tab_selector = "a[href='#tab-1639079360113-10']"
                # Find all tables and look for the one with 'Contract Name'
                tables = await page.locator("table.nsetable").all()
                target_table = None
                for table in tables:
                    header_text = await table.inner_text()
                    if "Contract Name" in header_text:
                        target_table = table
                        break

                if not target_table:
                    logger.error("nse_table_not_found")
                    await browser.close()
                    return []

                rows = await target_table.locator("tr").all()
                logger.info("nse_rows_found", count=len(rows))

                for i, row in enumerate(rows):
                    cells = await row.locator("td").all()
                    if len(cells) < 6:
                        continue

                    texts = [await c.inner_text() for c in cells]
                    contract_name = texts[0].strip()
                    if not contract_name or contract_name == "Contract Name":
                        continue

                    try:
                        # Parsing "INDEX (N25I)" or "EQ (Safaricom)"
                        symbol = contract_name
                        if "(" in contract_name:
                            symbol = contract_name.split("(")[1].split(")")[0]

                        mtm_price = float(texts[3].strip().replace(",", ""))
                        prev_price = float(texts[5].strip().replace(",", ""))

                        # Expiry Date: "18-Jun-2026"
                        from datetime import datetime

                        try:
                            expiry_date = datetime.strptime(texts[2].strip(), "%d-%b-%Y").date()
                        except ValueError:
                            expiry_date = trade_date

                        quotes.append(
                            RawQuote(
                                underlying_symbol=symbol,
                                strike_price=mtm_price,
                                maturity_date=expiry_date,
                                option_type="call",
                                bid_price=mtm_price,
                                ask_price=mtm_price,
                                underlying_price=prev_price,
                                data_source="nse",
                            )
                        )
                    except (ValueError, IndexError) as e:
                        logger.warning("row_parse_failed", index=i, error=str(e))
                        continue

                await browser.close()
            except Exception as e:
                logger.error("nse_scrape_failed", error=str(e))
                await browser.close()
                raise

        logger.info("nse_scrape_completed", count=len(quotes))
        return quotes
