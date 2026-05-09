"""Unit tests for convergence analysis module."""
from __future__ import annotations
import numpy as np
import pytest
from src.analysis.convergence import analyze_convergence_order

@pytest.mark.unit
def test_analyze_convergence_order() -> None:
    """Verify convergence order estimation."""
    # For a method with order p, error ~ C * h^p => log(error) ~ log(C) + p * log(h)
    # Here steps = 1/h, so log(error) ~ log(C) - p * log(steps)
    # Wait, analyze_convergence_order uses log(1.0/steps) which is log(h).
    # log_steps = np.log(1.0 / steps) = log(h)
    # log_errors = np.log(errors)
    # log_errors ~ log(C) + p * log_steps
    # So slope should be p.
    
    steps = np.array([10, 20, 40, 80])
    h = 1.0 / steps
    p = 2.0  # quadratic convergence
    errors = 0.5 * (h ** p)
    
    order = analyze_convergence_order(errors, steps)
    assert pytest.approx(order, rel=1e-2) == p
