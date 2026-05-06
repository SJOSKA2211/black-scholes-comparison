"""Scraper for SPY options using Playwright."""
from __future__ import annotations
from datetime import date
from playwright.async_api import async_playwright
from src.scrapers.base_scraper import BaseScraper, RawQuote
import structlog

logger = structlog.get_logger(__name__)

class SpyScraper(BaseScraper):
    """Scrapes SPY options data from Yahoo Finance."""
    
    def __init__(self) -> None:
        super().__init__("spy")

    async def _scrape(self, trade_date: date) -> list[RawQuote]:
        """Scrape SPY options data."""
        quotes: list[RawQuote] = []
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Yahoo Finance SPY options page
            url = "https://finance.yahoo.com/quote/SPY/options"
            await page.goto(url, timeout=60000)
            
            # Extract underlying price
            underlying_locator = page.locator('fin-streamer[data-field="regularMarketPrice"][data-symbol="SPY"]')
            await underlying_locator.first.wait_for(state="visible", timeout=60000)
            underlying_price_text = await underlying_locator.first.inner_text()
            underlying_price = float(underlying_price_text.replace(",", ""))
            
            # Extract call options
            call_rows = await page.locator("table.calls tbody tr").all()
            for row in call_rows:
                cells = await row.locator("td").all()
                if len(cells) >= 6:
                    strike = float(await cells[2].inner_text())
                    bid = float((await cells[4].inner_text()).replace("-", "0"))
                    ask = float((await cells[5].inner_text()).replace("-", "0"))
                    
                    quotes.append(RawQuote(
                        underlying_symbol="SPY",
                        strike_price=strike,
                        maturity_date=trade_date,
                        option_type="call",
                        bid_price=bid,
                        ask_price=ask,
                        underlying_price=underlying_price,
                        data_source="spy"
                    ))
                    
            await browser.close()
            
        return quotes
