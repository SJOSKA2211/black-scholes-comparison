import asyncio
from datetime import date, datetime

import structlog
from playwright.async_api import async_playwright

from src.data.pipeline import DataPipeline
from src.database import repository

logger = structlog.get_logger(__name__)


class SPYScraper:
    """Scraper for SPY (S&P 500 ETF) option chains."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.pipeline = DataPipeline(run_id)
        self.target_url = "https://finance.yahoo.com/quote/SPY/options"

    async def run(self):
        logger.info("scraper_started", market="spy", run_id=self.run_id)

        async with async_playwright() as playwright_instance:
            browser = await playwright_instance.chromium.launch(headless=True)
            browser_context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await browser_context.new_page()

            try:
                await page.goto(self.target_url, wait_until="networkidle")

                # Wait for the table to load
                await page.wait_for_selector("table.options-table", timeout=10000)

                # Extract data
                table_rows = await page.query_selector_all(
                    "table.options-table tbody tr"
                )
                scraped_data = []

                # Get current underlying price
                underlying_element = await page.query_selector(
                    'fin-streamer[data-field="regularMarketPrice"]'
                )
                underlying_price = (
                    float(await underlying_element.get_attribute("value"))
                    if underlying_element
                    else 500.0
                )

                for row_element in table_rows:
                    columns = await row_element.query_selector_all("td")
                    if len(columns) < 10:
                        continue

                    strike_price = float(await columns[2].inner_text())
                    bid_price = float((await columns[4].inner_text()).replace(",", ""))
                    ask_price = float((await columns[5].inner_text()).replace(",", ""))
                    volume_count = int(
                        (await columns[8].inner_text())
                        .replace(",", "")
                        .replace("-", "0")
                    )
                    open_interest_count = int(
                        (await columns[9].inner_text())
                        .replace(",", "")
                        .replace("-", "0")
                    )

                    # Estimate maturity (30 days default)
                    maturity_years = 30 / 365.0

                    scraped_data.append(
                        {
                            "underlying_price": underlying_price,
                            "strike_price": strike_price,
                            "maturity_years": maturity_years,
                            "option_type": "call",
                            "market_source": "spy",
                            "trade_date": date.today(),
                            "bid_price": bid_price,
                            "ask_price": ask_price,
                            "volume": volume_count,
                            "open_interest": open_interest_count,
                            "data_source": "spy",
                        }
                    )

                await self.pipeline.process_rows(scraped_data)
                logger.info(
                    "scraper_finished", market="spy", rows_processed=len(scraped_data)
                )

            except Exception as scraper_error:
                logger.error("scraper_failed", market="spy", error=str(scraper_error))
                await repository.update_scrape_run(
                    self.run_id,
                    {"status": "failed", "finished_at": datetime.utcnow().isoformat()},
                )
            finally:
                await browser.close()


async def main():
    # Manual trigger for testing
    run_id = await repository.create_scrape_run("spy")
    scraper = SPYScraper(run_id)
    await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
