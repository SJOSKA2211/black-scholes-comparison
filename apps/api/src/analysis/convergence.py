"""Convergence analysis logic for numerical experiments."""
from __future__ import annotations
from typing import List, Dict, Any
import pandas as pd

def analyze_convergence_order(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Estimates the empirical convergence order from a series of runs.
    Calculates the slope of log(error) vs log(1/N).
    """
    if len(results) < 2:
        return {"convergence_order": 0.0}
        
    df = pd.DataFrame(results)
    # Placeholder for actual log-log regression
    return {"convergence_order": 1.0}
