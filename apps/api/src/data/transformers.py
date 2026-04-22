"""Data transformers — cleans and converts raw market data into canonical models."""
from __future__ import annotations
from typing import Any, Dict, List
import pandas as pd
from src.methods.base import OptionParams
import structlog

logger = structlog.get_logger(__name__)

def transform_market_row(row: Dict[str, Any], market_source: str = "synthetic") -> OptionParams:
    """
    Converts a raw market data row into an OptionParams instance.
    Expected row keys: underlying_price, strike_price, maturity_years, volatility, 
    risk_free_rate, option_type, is_american.
    """
    try:
        return OptionParams(
            underlying_price=float(row["underlying_price"]),
            strike_price=float(row["strike_price"]),
            maturity_years=float(row["maturity_years"]),
            volatility=float(row["volatility"]),
            risk_free_rate=float(row["risk_free_rate"]),
            option_type=row["option_type"],
            is_american=bool(row.get("is_american", False)),
            market_source=market_source
        )
    except (KeyError, ValueError, TypeError) as e:
        logger.error("transformation_error", error=str(e), row=row)
        raise

def transform_batch_df(df: pd.DataFrame, market_source: str = "synthetic") -> List[OptionParams]:
    """Converts a DataFrame of market data into a list of OptionParams."""
    params_list: List[OptionParams] = []
    for _, row in df.iterrows():
        try:
            params_list.append(transform_market_row(row.to_dict(), market_source))
        except Exception:
            continue
    return params_list
