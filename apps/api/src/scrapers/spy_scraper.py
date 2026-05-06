"""SPY option scraper using Yahoo Finance."""
from __future__ import annotations
from datetime import date, datetime
import pandas as pd
import yfinance as yf
from src.scrapers.base_scraper import BaseScraper
import structlog

logger = structlog.get_logger(__name__)

class SPYScraper(BaseScraper):
    """Scrapes SPY option chain data from Yahoo Finance."""

    async def scrape(self, trade_date: date) -> pd.DataFrame:
        """
        Scrape SPY data. 
        Note: Yahoo Finance usually provides current data, so trade_date might be ignored
        in a simple implementation, but we'll try to fetch snapshots if possible.
        """
        logger.info("spy_scrape_started", date=trade_date.isoformat())
        
        spy = yf.Ticker("SPY")
        expirations = spy.options
        
        all_data = []
        underlying_price = spy.history(period="1d")["Close"].iloc[-1]
        
        # Limit to first few expirations for performance in this research context
        for exp in expirations[:5]:
            opt = spy.option_chain(exp)
            
            # Maturity in years
            exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
            days_to_expiry = (exp_date - date.today()).days
            maturity_years = max(days_to_expiry / 365.0, 0.001)
            
            for chain, opt_type in [(opt.calls, "call"), (opt.puts, "put")]:
                temp_df = chain[["strike", "bid", "ask", "volume", "openInterest"]].copy()
                temp_df["option_type"] = opt_type
                temp_df["underlying_price"] = underlying_price
                temp_df["maturity_years"] = maturity_years
                temp_df["strike_price"] = temp_df["strike"]
                temp_df["bid_price"] = temp_df["bid"]
                temp_df["ask_price"] = temp_df["ask"]
                all_data.append(temp_df)
                
        if not all_data:
            return pd.DataFrame()
            
        final_df = pd.concat(all_data, ignore_index=True)
        logger.info("spy_scrape_completed", rows=len(final_df))
        
        return final_df
