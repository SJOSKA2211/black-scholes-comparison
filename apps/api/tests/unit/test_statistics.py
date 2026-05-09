"""Unit tests for statistics analysis module."""
from __future__ import annotations
import numpy as np
import pandas as pd
import pytest
from src.analysis.statistics import calculate_mape, summarize_convergence

@pytest.mark.unit
def test_calculate_mape() -> None:
    """Verify MAPE calculation."""
    analytical = np.array([10.0, 20.0, 30.0])
    numerical = np.array([10.5, 19.0, 31.5])  # 5% error each
    mape = calculate_mape(analytical, numerical)
    assert pytest.approx(mape) == 5.0

@pytest.mark.unit
def test_summarize_convergence() -> None:
    """Verify convergence summary aggregation."""
    data = {
        "method_type": ["analytical", "analytical", "fdm", "fdm"],
        "computed_price": [10.0, 10.1, 10.2, 10.3],
        "exec_seconds": [0.1, 0.1, 0.5, 0.6]
    }
    df = pd.DataFrame(data)
    summary = summarize_convergence(df)
    assert "computed_price" in summary.columns
    assert "exec_seconds" in summary.columns
    assert len(summary) == 2  # analytical and fdm
