"""Data transformers for converting raw scraper data to validated models."""
from __future__ import annotations
import pandas as pd
from src.data.validators import MarketDataInput
 
def transform_raw_quotes(df: pd.DataFrame, source: str) -> list[MarketDataInput]:
    """
    Clean and transform raw market data DataFrame to validated Input models.
    Handles NaN removal and type coercion.
    """
    # Placeholder for actual transformation logic per source (SPY vs NSE)
    # 1. Drop rows with missing critical prices
    df = df.dropna(subset=['bid', 'ask', 'strike'])
    
    # 2. Convert to models
    validated_rows = []
    for _, row in df.iterrows():
        try:
            validated_rows.append(MarketDataInput(
                option_id=row['option_id'], # Assigned during pipeline
                trade_date=row['date'],
                bid_price=float(row['bid']),
                ask_price=float(row['ask']),
                volume=int(row.get('volume', 0)),
                open_interest=int(row.get('open_interest', 0)),
                implied_vol=float(row['iv']) if not pd.isna(row.get('iv')) else None,
                data_source=source
            ))
        except Exception:
            continue # Log via structlog in pipeline
            
    return validated_rows
