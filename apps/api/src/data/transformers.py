"""Data transformation logic for market data."""

from typing import Any

import pandas as pd


def transform_yahoo_finance_data(raw_data: list[dict[str, Any]]) -> pd.DataFrame:
    """Transform raw JSON data from Yahoo Finance into a standardized DataFrame."""
    df = pd.DataFrame(raw_data)
    if df.empty:
        return df

    # Standardize columns
    df = df.rename(
        columns={
            "strike": "strike_price",
            "lastPrice": "last_price",
            "bid": "bid_price",
            "ask": "ask_price",
            "volume": "volume",
            "openInterest": "open_interest",
            "impliedVolatility": "implied_vol",
        }
    )

    # Calculate mid price
    df["mid_price"] = (df["bid_price"] + df["ask_price"]) / 2

    return df


def transform_nse_data(raw_data: list[dict[str, Any]]) -> pd.DataFrame:
    """Transform raw data from NSE (Nairobi Securities Exchange) into a standardized DataFrame."""
    df = pd.DataFrame(raw_data)
    # Implement NSE specific transformation logic here
    return df
