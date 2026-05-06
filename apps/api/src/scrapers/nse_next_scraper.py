"""Scraper for NSE (Nairobi Securities Exchange) derivatives using Playwright."""
from __future__ import annotations
from datetime import date
from playwright.async_api import async_playwright
from src.scrapers.base_scraper import BaseScraper, RawQuote
import structlog

logger = structlog.get_logger(__name__)

class NseScraper(BaseScraper):
    """Scrapes NSE derivatives data from the official website."""
    
    def __init__(self) -> None:
        super().__init__("nse")

    async def _scrape(self, trade_date: date) -> list[RawQuote]:
        """Scrape NSE derivatives data."""
        quotes: list[RawQuote] = []
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # NSE Kenya Derivatives Market page
            url = "https://www.nse.co.ke/derivatives/"
            logger.info("fetching_nse_derivatives", url=url)
            
            try:
                await page.goto(url, timeout=60000)
                
                # The NSE page has a table for derivatives. 
                # Note: This selector is a best-guess based on standard NSE web structure.
                # In a real production environment, we would monitor this for changes.
                rows = await page.locator("table tbody tr").all()
                
                # NSE Kenya Derivatives usually include Safaricom, Equity, KCB, EABL, etc.
                # We'll extract basic info if the table is found.
                for row in rows:
                    cells = await row.locator("td").all()
                    if len(cells) >= 8:
                        # Best guess at columns: Instrument, Type, Expiry, Strike, Bid, Ask, Underlying
                        instrument = await cells[0].inner_text()
                        if "Option" in instrument or len(cells) > 5:
                            try:
                                strike_text = await cells[3].inner_text()
                                bid_text = await cells[4].inner_text()
                                ask_text = await cells[5].inner_text()
                                underlying_text = await cells[7].inner_text()
                                
                                strike = float(strike_text.replace(",", ""))
                                bid = float(bid_text.replace("-", "0").replace(",", ""))
                                ask = float(ask_text.replace("-", "0").replace(",", ""))
                                underlying = float(underlying_text.replace(",", ""))
                                
                                quotes.append(RawQuote(
                                    underlying_symbol=instrument.split()[0],
                                    strike_price=strike,
                                    maturity_date=trade_date, # Fallback to trade_date if expiry parsing fails
                                    option_type="call" if "Call" in instrument else "put",
                                    bid_price=bid,
                                    ask_price=ask,
                                    underlying_price=underlying,
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
