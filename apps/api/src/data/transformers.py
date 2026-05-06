"""Data transformation utilities for market data pipelines."""

from __future__ import annotations

import pandas as pd


def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw scraped data: handle NaNs, convert types, and calculate mid price.
    Descriptive variable names used.
    """
    # Drop rows with missing critical prices
    df = df.dropna(subset=["bid_price", "ask_price", "underlying_price"])

    # Ensure numeric types
    df["bid_price"] = pd.to_numeric(df["bid_price"])
    df["ask_price"] = pd.to_numeric(df["ask_price"])
    df["underlying_price"] = pd.to_numeric(df["underlying_price"])

    # Calculate mid price
    df["mid_price"] = (df["bid_price"] + df["ask_price"]) / 2.0

    # Filter out invalid prices
    df = df[df["mid_price"] > 0]

    return df


def prepare_for_upsert(df: pd.DataFrame) -> list[dict[str, any]]:
    """Convert DataFrame to list of dicts for Supabase upsert."""
    return df.to_dict(orient="records")
