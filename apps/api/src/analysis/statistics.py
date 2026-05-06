"""Statistical analysis for research results."""
from __future__ import annotations
from typing import Any
import numpy as np
import pandas as pd

def calculate_mape(
    analytical_prices: np.ndarray[Any, np.dtype[np.float64]], 
    numerical_prices: np.ndarray[Any, np.dtype[np.float64]]
) -> float:
    """Calculate Mean Absolute Percentage Error."""
    absolute_errors = np.abs(analytical_prices - numerical_prices)
    percentage_errors = absolute_errors / analytical_prices
    return float(np.mean(percentage_errors) * 100)

def summarize_convergence(results_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize convergence characteristics of different methods."""
    return results_df.groupby("method_type").agg({
        "computed_price": ["mean", "std"],
        "exec_seconds": ["mean", "max"]
    })
