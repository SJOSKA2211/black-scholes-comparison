"""Statistical analysis for research results."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    import pandas as pd


def calculate_mape(
    analytical_prices: np.ndarray[Any, np.dtype[np.float64]],
    numerical_prices: np.ndarray[Any, np.dtype[np.float64]],
) -> float:
    """Calculate Mean Absolute Percentage Error."""
    # Avoid division by zero
    mask = analytical_prices > 0
    if not np.any(mask):
        return 0.0
    absolute_errors = np.abs(analytical_prices[mask] - numerical_prices[mask])
    percentage_errors = absolute_errors / analytical_prices[mask]
    return float(np.mean(percentage_errors) * 100)


def calculate_errors(
    analytical_price: float,
    numerical_price: float,
) -> dict[str, float]:
    """Calculate absolute and relative errors."""
    abs_error = abs(analytical_price - numerical_price)
    rel_error = (abs_error / analytical_price * 100) if analytical_price > 0 else 0.0
    return {
        "absolute_error": abs_error,
        "relative_pct_error": rel_error,
    }


def summarize_convergence(results_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize convergence characteristics of different methods."""
    return results_df.groupby("method_type").agg(
        {"computed_price": ["mean", "std"], "exec_seconds": ["mean", "max"]}
    )
