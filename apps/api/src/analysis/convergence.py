"""Convergence analysis for numerical methods."""
from __future__ import annotations
from typing import Any
import numpy as np

def analyze_convergence_order(
    errors: np.ndarray[Any, np.dtype[np.float64]], 
    steps: np.ndarray[Any, np.dtype[np.float64]]
) -> float:
    """Estimate the order of convergence from errors and step sizes."""
    log_errors = np.log(errors)
    log_steps = np.log(1.0 / steps)
    
    # Simple linear regression on log-log plot
    coefficients = np.polyfit(log_steps, log_errors, 1)
    return float(coefficients[0])
