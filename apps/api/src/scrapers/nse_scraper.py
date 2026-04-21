import asyncio
from datetime import date, datetime

import structlog
from playwright.async_api import async_playwright

from src.data.pipeline import DataPipeline
from src.database import repository

logger = structlog.get_logger(__name__)


class NSEScraper:
    """Scraper for NSE (National Stock Exchange of India) NIFTY options."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.pipeline = DataPipeline(run_id)
        self.target_url = "https://www.nseindia.com/option-chain"

    async def run(self):
        logger.info("scraper_started", market="nse", run_id=self.run_id)

        async with async_playwright() as playwright_instance:
            browser = await playwright_instance.chromium.launch(headless=True)
            browser_context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            page = await browser_context.new_page()

            try:
                # Step 1: Visit home to establish session/cookies
                await page.goto("https://www.nseindia.com", wait_until="networkidle")
                await asyncio.sleep(2)

                # Step 2: Navigate to option chain
                await page.goto(self.target_url, wait_until="networkidle")
                await page.wait_for_selector("#optionChainTable", timeout=20000)

                # Step 3: Extract underlying value
                underlying_element = await page.query_selector("#equity_underlyingVal")
                underlying_text = (
                    await underlying_element.inner_text()
                    if underlying_element
                    else "NIFTY 22000.00"
                )
                underlying_price = float(underlying_text.split()[-1].replace(",", ""))

                # Step 4: Extract table rows
                table_rows = await page.query_selector_all("#optionChainTable tbody tr")
                scraped_data = []

                for row_element in table_rows:
                    columns = await row_element.query_selector_all("td")
                    if len(columns) < 20:
                        continue

                    strike_text = await columns[11].inner_text()
                    if not strike_text.strip():
                        continue
                    strike_price = float(strike_text.replace(",", ""))

                    # Common maturity for weekly NIFTY (7 days)
                    maturity_years = 7 / 365.0

                    # CALLS (Columns 1-10)
                    call_bid = float(
                        (await columns[8].inner_text())
                        .replace("-", "0")
                        .replace(",", "")
                    )
                    call_ask = float(
                        (await columns[9].inner_text())
                        .replace("-", "0")
                        .replace(",", "")
                    )
                    call_volume = int(
                        (await columns[3].inner_text())
                        .replace("-", "0")
                        .replace(",", "")
                    )
                    call_oi = int(
                        (await columns[1].inner_text())
                        .replace("-", "0")
                        .replace(",", "")
                    )

                    if call_ask > 0:
                        scraped_data.append(
                            {
                                "underlying_price": underlying_price,
                                "strike_price": strike_price,
                                "maturity_years": maturity_years,
                                "option_type": "call",
                                "market_source": "nse",
                                "trade_date": date.today(),
                                "bid_price": call_bid,
                                "ask_price": call_ask,
                                "volume": call_volume,
                                "open_interest": call_oi,
                                "data_source": "nse",
                            }
                        )

                    # PUTS (Columns 12-21)
                    put_bid = float(
                        (await columns[13].inner_text())
                        .replace("-", "0")
                        .replace(",", "")
                    )
                    put_ask = float(
                        (await columns[14].inner_text())
                        .replace("-", "0")
                        .replace(",", "")
                    )
                    put_volume = int(
                        (await columns[19].inner_text())
                        .replace("-", "0")
                        .replace(",", "")
                    )
                    put_oi = int(
                        (await columns[21].inner_text())
                        .replace("-", "0")
                        .replace(",", "")
                    )

                    if put_ask > 0:
                        scraped_data.append(
                            {
                                "underlying_price": underlying_price,
                                "strike_price": strike_price,
                                "maturity_years": maturity_years,
                                "option_type": "put",
                                "market_source": "nse",
                                "trade_date": date.today(),
                                "bid_price": put_bid,
                                "ask_price": put_ask,
                                "volume": put_volume,
                                "open_interest": put_oi,
                                "data_source": "nse",
                            }
                        )

                await self.pipeline.process_rows(scraped_data)
                logger.info(
                    "scraper_finished", market="nse", rows_processed=len(scraped_data)
                )

            except Exception as scraper_error:
                logger.error("scraper_failed", market="nse", error=str(scraper_error))
                await repository.update_scrape_run(
                    self.run_id,
                    {"status": "failed", "finished_at": datetime.utcnow().isoformat()},
                )
            finally:
                await browser.close()
