"""Scraper for SPY (S&P 500 ETF) option data using Yahoo Finance."""

from __future__ import annotations

import asyncio
from datetime import date, datetime

import pandas as pd
import requests
import yfinance as yf

from src.scrapers.base_scraper import BaseScraper, RawQuote


class SpyScraper(BaseScraper):
    """Scraper for SPY options."""

    def __init__(self) -> None:
        super().__init__(market_name="spy")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
                )
            }
        )

    async def _scrape(self, trade_date: date) -> list[RawQuote]:
        """Fetch SPY option chain via yfinance."""
        # yfinance is blocking, run in thread
        return await asyncio.to_thread(self._scrape_sync, trade_date)

    def _scrape_sync(self, trade_date: date) -> list[RawQuote]:
        """Synchronous scraping logic for yfinance."""
        ticker = yf.Ticker("SPY", session=self.session)
        expirations = ticker.options
        if not expirations:
            return []

        # Get underlying price
        # fast_info might be better for current price
        underlying_price = ticker.fast_info["last_price"]

        quotes: list[RawQuote] = []

        # To avoid heavy load and stay within rate limits, we take the first 2 expirations
        for exp in expirations[:2]:
            opt_chain = ticker.option_chain(exp)

            # Process calls
            quotes.extend(self._process_df(opt_chain.calls, exp, underlying_price, "call"))
            # Process puts
            quotes.extend(self._process_df(opt_chain.puts, exp, underlying_price, "put"))

        return quotes

    def _process_df(
        self, df: pd.DataFrame, expiration: str, underlying_price: float, opt_type: str
    ) -> list[RawQuote]:
        """Convert yfinance dataframe to RawQuote list."""
        quotes: list[RawQuote] = []
        maturity_date = datetime.strptime(expiration, "%Y-%m-%d").date()

        for _, row in df.iterrows():
            # Basic validation: must have bid/ask
            if pd.isna(row["bid"]) or pd.isna(row["ask"]) or row["bid"] <= 0 or row["ask"] <= 0:
                continue

            quotes.append(
                RawQuote(
                    underlying_symbol="SPY",
                    strike_price=float(row["strike"]),
                    maturity_date=maturity_date,
                    option_type=opt_type,
                    bid_price=float(row["bid"]),
                    ask_price=float(row["ask"]),
                    underlying_price=underlying_price,
                    data_source="spy",
                )
            )
        return quotes
