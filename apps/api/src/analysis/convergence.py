"""Convergence analysis logic for numerical experiments."""

from __future__ import annotations

from typing import Any

import pandas as pd


def analyze_convergence_order(results: list[dict[str, Any]]) -> dict[str, float]:
    """
    Estimates the empirical convergence order from a series of runs.
    Calculates the slope of log(error) vs log(1/N).
    """
    if len(results) < 2:
        return {"convergence_order": 0.0}

    pd.DataFrame(results)
    # Placeholder for actual log-log regression
    return {"convergence_order": 1.0}
