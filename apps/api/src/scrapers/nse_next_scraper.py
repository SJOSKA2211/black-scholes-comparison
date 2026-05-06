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
            context = await browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
            page = await context.new_page()
            
            url = "https://www.nse.co.ke/dataservices/market-statistics/"
            logger.info("fetching_nse_statistics", url=url)
            
            try:
                await page.goto(url, timeout=60000)
                
                # Use the exact CSS selector for the Derivatives Statistics tab
                tab_selector = "a[href='#tab-1639079360113-10']"
                await page.wait_for_selector(tab_selector, timeout=30000)
                await page.click(tab_selector)
                
                # Wait for the AJAX-loaded table to appear
                table_row_selector = "table.nsetable.table tbody tr"
                await page.wait_for_selector(table_row_selector, timeout=30000)
                
                rows = await page.locator(table_row_selector).all()
                logger.info("nse_rows_found", count=len(rows))
                
                for row in rows:
                    cells = await row.locator("td").all()
                    if len(cells) >= 6:
                        # Columns: Contract Name, ISIN, Expiry Date, MTM Price, Volume, Previous Price
                        contract_name = await cells[0].inner_text()
                        mtm_price_text = await cells[3].inner_text()
                        prev_price_text = await cells[5].inner_text()
                        
                        try:
                            mtm_price = float(mtm_price_text.replace(",", ""))
                            prev_price = float(prev_price_text.replace(",", ""))
                            
                            # Treat futures as proxy for now (NSE NEXT is mainly futures)
                            quotes.append(RawQuote(
                                underlying_symbol=contract_name.split()[-1].strip("()"),
                                strike_price=mtm_price,
                                maturity_date=trade_date, 
                                option_type="call",
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
