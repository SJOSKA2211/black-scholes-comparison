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
            # Use a realistic User-Agent to avoid being flagged as a bot
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Yahoo Finance SPY options page
            url = "https://finance.yahoo.com/quote/SPY/options"
            logger.info("fetching_spy_options", url=url)
            
            try:
                await page.goto(url, timeout=60000, wait_until="networkidle")
                
                # Check for "Scroll to bottom and accept" or "Agree" buttons (Yahoo Consent)
                if "consent.yahoo.com" in page.url or "guce.yahoo.com" in page.url:
                    logger.info("yahoo_consent_detected", url=page.url)
                    # Try to find and click the "Agree" button
                    agree_button = page.locator('button[name="agree"]')
                    if await agree_button.is_visible():
                        await agree_button.click()
                        await page.wait_for_load_state("networkidle")

                # Extract underlying price
                # We use a broader selector or multiple attempts if the specific one fails
                price_selector = 'fin-streamer[data-field="regularMarketPrice"][data-symbol="SPY"]'
                try:
                    await page.wait_for_selector(price_selector, timeout=30000)
                    underlying_price_text = await page.locator(price_selector).first.inner_text()
                    underlying_price = float(underlying_price_text.replace(",", ""))
                except Exception:
                    logger.warning("primary_price_selector_failed", attempting_fallback=True)
                    # Fallback to general price class if fin-streamer is missing
                    fallback_price = await page.locator('span[data-testid="qsp-price"]').first.inner_text()
                    underlying_price = float(fallback_price.replace(",", ""))

                # Extract call options rows
                # Updated selector based on subagent exploration
                rows_selector = "div.tableContainer table tbody tr"
                await page.wait_for_selector(rows_selector, timeout=30000)
                call_rows = await page.locator(rows_selector).all()
                
                logger.info("spy_rows_found", count=len(call_rows))
                
                for row in call_rows:
                    cells = await row.locator("td").all()
                    if len(cells) >= 6:
                        # Yahoo columns: Contract Name, Last Trade, Strike, Last Price, Bid, Ask, Change, %Change, Vol, Open Int, Imp Vol
                        # Wait, the structure can vary. We'll use a safer approach.
                        try:
                            # Strike is usually the 3rd column (index 2)
                            strike_text = await cells[2].inner_text()
                            # Bid is index 4, Ask is index 5
                            bid_text = await cells[4].inner_text()
                            ask_text = await cells[5].inner_text()
                            
                            strike = float(strike_text.replace(",", ""))
                            bid = float(bid_text.replace("-", "0").replace(",", ""))
                            ask = float(ask_text.replace("-", "0").replace(",", ""))
                            
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
                        except (ValueError, IndexError):
                            continue
                            
                await browser.close()
            except Exception as e:
                logger.error("spy_scrape_failed", error=str(e))
                await browser.close()
                raise
                
        logger.info("spy_scrape_completed", count=len(quotes))
        return quotes
