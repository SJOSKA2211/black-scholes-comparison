"""Yahoo Finance SPY options scraper using Playwright."""

from datetime import date
from typing import Any

import structlog
from playwright.async_api import async_playwright

from src.scrapers.base_scraper import BaseScraper

logger = structlog.get_logger(__name__)


class SpyScraper(BaseScraper):
    """Scrapes SPY option chain from Yahoo Finance."""

    async def scrape(self, trade_date: date) -> list[dict[str, Any]]:
        url = "https://finance.yahoo.com/quote/SPY/options"
        logger.info("scraping_spy", url=url, date=trade_date.isoformat())

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
                await page.goto(url, timeout=30000)
                await page.wait_for_selector("table", timeout=15000)

                # Basic data extraction (example logic)
                # In a real implementation, we would parse the tables for calls and puts
                rows = await page.query_selector_all("table tbody tr")
                data = []
                for row in rows[:10]:  # Limit for demo
                    cols = await row.query_selector_all("td")
                    if len(cols) >= 10:
                        data.append(
                            {
                                "strike": await cols[2].inner_text(),
                                "lastPrice": await cols[3].inner_text(),
                                "bid": await cols[4].inner_text(),
                                "ask": await cols[5].inner_text(),
                                "volume": await cols[8].inner_text(),
                                "openInterest": await cols[9].inner_text(),
                            }
                        )

                logger.info("scrape_success", market="spy", rows=len(data))
                return data
            except Exception as e:
                logger.error("scrape_error", market="spy", error=str(e))
                return []
            finally:
                await browser.close()
