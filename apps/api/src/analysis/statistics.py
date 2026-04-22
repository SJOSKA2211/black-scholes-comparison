"""Statistical analysis for pricing results."""
from __future__ import annotations
from typing import List, Dict, Any
import numpy as np
import pandas as pd

def compute_mape(results: List[Dict[str, Any]], analytical_ref: float) -> float:
    """Computes Mean Absolute Percentage Error for a set of results."""
    if not results or analytical_ref == 0:
        return 0.0
        
    errors = [abs(r["computed_price"] - analytical_ref) / analytical_ref for r in results]
    return float(np.mean(errors)) * 100

def get_convergence_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extracts convergence data points from method results."""
    # Logic to map (num_steps or num_paths) -> error
    df = pd.DataFrame(results)
    if df.empty:
        return {}
        
    # Assume results contain parameter_set with resolution info
    # This is a placeholder for more complex analysis
    return {
        "count": len(df),
        "mean_price": df["computed_price"].mean(),
        "std_dev": df["computed_price"].std()
    }
