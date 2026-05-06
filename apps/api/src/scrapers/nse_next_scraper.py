"""NSE (Nairobi Securities Exchange) NEXT market scraper using Playwright."""

import asyncio
from datetime import date
from typing import Any

import structlog
from playwright.async_api import async_playwright

from src.scrapers.base_scraper import BaseScraper

logger = structlog.get_logger(__name__)


class NseNextScraper(BaseScraper):
    """Scrapes derivatives data from the NSE NEXT market."""

    async def scrape(self, trade_date: date) -> list[dict[str, Any]]:
        url = "https://www.nse.co.ke/derivatives-market/market-statistics.html"
        logger.info("scraping_nse", url=url, date=trade_date.isoformat())

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            )
            page = await context.new_page()

            try:
                # NSE site can be slow or have anti-bot
                await page.goto(url, timeout=45000)
                await asyncio.sleep(5)  # Wait for JS rendering

                # Look for the statistics table
                # NSE often uses an iframe or dynamic table for market stats
                table_selector = "table.table-striped"
                # Wait for any table to appear if specific class is not there
                try:
                    await page.wait_for_selector(table_selector, timeout=10000)
                except Exception:
                    table_selector = "table"
                    await page.wait_for_selector(table_selector, timeout=10000)

                rows = await page.query_selector_all(f"{table_selector} tbody tr")
                data = []
                for row in rows:
                    cols = await row.query_selector_all("td")
                    if len(cols) >= 5:
                        data.append(
                            {
                                "symbol": await cols[0].inner_text(),
                                "expiry": await cols[1].inner_text(),
                                "option_type": await cols[2].inner_text(),
                                "strike": await cols[3].inner_text(),
                                "last_price": await cols[4].inner_text(),
                            }
                        )

                logger.info("scrape_success", market="nse", rows=len(data))
                return data
            except Exception as e:
                logger.error("scrape_error", market="nse", error=str(e))
                return []
            finally:
                await browser.close()
