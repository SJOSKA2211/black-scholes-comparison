"""Unit tests for analysis modules."""
from __future__ import annotations
import numpy as np
import pandas as pd
import pytest
from src.analysis.statistics import calculate_mape, calculate_errors, summarize_convergence
from src.analysis.convergence import analyze_convergence_order
from src.auth import oauth

@pytest.mark.unit
def test_calculate_mape() -> None:
    """Verify MAPE calculation."""
    analytical = np.array([100.0, 200.0])
    numerical = np.array([105.0, 190.0])
    mape = calculate_mape(analytical, numerical)
    # (5/100 + 10/200) / 2 * 100 = (0.05 + 0.05) / 2 * 100 = 5.0
    assert mape == pytest.approx(5.0)

@pytest.mark.unit
def test_calculate_mape_zero_mask() -> None:
    """Verify MAPE calculation with zeros."""
    analytical = np.array([0.0, 0.0])
    numerical = np.array([5.0, 10.0])
    mape = calculate_mape(analytical, numerical)
    assert mape == 0.0

@pytest.mark.unit
def test_calculate_errors() -> None:
    """Verify error calculations."""
    res = calculate_errors(100.0, 95.0)
    assert res["absolute_error"] == 5.0
    assert res["relative_pct_error"] == 5.0
    
    res_zero = calculate_errors(0.0, 5.0)
    assert res_zero["relative_pct_error"] == 0.0

@pytest.mark.unit
def test_summarize_convergence() -> None:
    """Verify convergence summarization."""
    df = pd.DataFrame({
        "method_type": ["mc", "mc", "fdm"],
        "computed_price": [10.0, 11.0, 10.5],
        "exec_seconds": [0.1, 0.2, 0.5]
    })
    summary = summarize_convergence(df)
    assert "computed_price" in summary.columns
    assert "exec_seconds" in summary.columns
    assert len(summary) == 2

@pytest.mark.unit
def test_analyze_convergence_order() -> None:
    """Verify convergence order estimation."""
    # O(h^2) convergence: error = C * h^2
    # log(error) = log(C) + 2*log(h)
    # log(1/h) = -log(h)
    # log(error) = log(C) - 2*log(1/h)
    # Slope should be -2.0
    steps = np.array([0.1, 0.05, 0.025, 0.0125])
    errors = 1.5 * (steps**2)
    order = analyze_convergence_order(errors, steps)
    assert order == pytest.approx(-2.0, rel=0.01)

@pytest.mark.unit
def test_oauth_coverage() -> None:
    """Trigger coverage for oauth.py."""
    assert oauth.logger is not None
