"""Data transformation utilities for market data and parameters."""
from __future__ import annotations
from typing import Any
import pandas as pd
from src.data.validators import OptionParamsInput

def transform_market_row(row: dict[str, Any]) -> OptionParamsInput:
    """Transforms a raw market data row into OptionParamsInput."""
    # Ensure numeric types
    data = {
        "underlying_price": float(row["underlying_price"]),
        "strike_price": float(row["strike_price"]),
        "maturity_years": float(row["maturity_years"]),
        "volatility": float(row["volatility"]),
        "risk_free_rate": float(row["risk_free_rate"]),
        "option_type": str(row["option_type"]).lower(),
        "market_source": row.get("market_source", "synthetic")
    }
    return OptionParamsInput(**data)

def transform_batch_df(df: pd.DataFrame) -> list[OptionParamsInput]:
    """Transforms a DataFrame of market data into a list of OptionParamsInput."""
    results = []
    for _, row in df.iterrows():
        try:
            results.append(transform_market_row(row.to_dict()))
        except (KeyError, ValueError, TypeError):
            # Skip invalid rows in batch transformation
            continue
    return results

def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans and validates a DataFrame of market data."""
    if df.empty:
        return df
    
    # Ensure mandatory columns
    required = ["underlying_price", "strike_price", "maturity_years", "option_type", "bid_price", "ask_price"]
    for col in required:
        if col not in df.columns:
            df[col] = 0.0 # Or raise error
            
    # Basic cleaning
    df["underlying_price"] = pd.to_numeric(df["underlying_price"], errors="coerce")
    df["strike_price"] = pd.to_numeric(df["strike_price"], errors="coerce")
    df["maturity_years"] = pd.to_numeric(df["maturity_years"], errors="coerce")
    df["bid_price"] = pd.to_numeric(df["bid_price"], errors="coerce")
    df["ask_price"] = pd.to_numeric(df["ask_price"], errors="coerce")
    df["option_type"] = df["option_type"].str.lower()
    
    # Drop invalid rows
    df = df.dropna(subset=required)
    
    return df
