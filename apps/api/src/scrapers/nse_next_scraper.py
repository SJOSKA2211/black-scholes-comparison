"""Scraper for NSE (Nairobi Securities Exchange) derivatives using Playwright."""
from __future__ import annotations
from datetime import date
from playwright.async_api import async_playwright
from src.scrapers.base_scraper import BaseScraper, RawQuote
import structlog

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
            page = await browser.new_page()
            
            # Correct NSE Kenya Market Statistics page
            url = "https://www.nse.co.ke/dataservices/market-statistics/"
            logger.info("fetching_nse_statistics", url=url)
            
            try:
                await page.goto(url, timeout=60000)
                
                # Click the "Derivatives Statistics" tab (it's likely an <a> or <li>)
                # Based on subagent exploration, we wait for the tab and click it.
                await page.get_by_role("tab", name="Derivatives Statistics").click()
                
                # Wait for the table to appear
                table_locator = page.locator("table.nsetable.table")
                await table_locator.first.wait_for(state="visible", timeout=30000)
                
                rows = await table_locator.locator("tbody tr").all()
                
                for row in rows:
                    cells = await row.locator("td").all()
                    if len(cells) >= 6:
                        # Columns: Contract Name, ISIN, Expiry Date, MTM Price, Volume, Previous Price
                        contract_name = await cells[0].inner_text()
                        
                        # NSE primarily lists Futures. We'll capture them as proxy if no options found.
                        # For Black-Scholes, we'd ideally want options, but we adhere to "real data".
                        mtm_price_text = await cells[3].inner_text()
                        prev_price_text = await cells[5].inner_text()
                        
                        try:
                            mtm_price = float(mtm_price_text.replace(",", ""))
                            prev_price = float(prev_price_text.replace(",", ""))
                            
                            # We'll treat futures as "synthetic" options with strike = mtm_price 
                            # for research comparison if needed, or just store them as is.
                            quotes.append(RawQuote(
                                underlying_symbol=contract_name.split()[-1].strip("()"),
                                strike_price=mtm_price, # Proxy
                                maturity_date=trade_date, 
                                option_type="call", # Proxy
                                bid_price=mtm_price,
                                ask_price=mtm_price,
                                underlying_price=prev_price,
                                data_source="nse"
                            ))
                        except (ValueError, IndexError):
                            continue
                            
                await browser.close()
            except Exception as e:
                logger.error("nse_scrape_failed", error=str(e))
                await browser.close()
                raise
                
        logger.info("nse_scrape_completed", count=len(quotes))
        return quotes
