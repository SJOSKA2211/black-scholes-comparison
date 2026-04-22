import pytest
import numpy as np
from src.analysis.convergence import analyze_convergence_order
from src.analysis.statistics import compute_mape, get_convergence_metrics

@pytest.mark.unit
class TestAnalysis:
    def test_analyze_convergence_order(self):
        results = [{"dt": 0.1, "error": 0.01}, {"dt": 0.05, "error": 0.0025}]
        res = analyze_convergence_order(results)
        assert res["convergence_order"] == 1.0
        assert analyze_convergence_order([])["convergence_order"] == 0.0

    def test_compute_mape(self):
        results = [{"computed_price": 110.0}, {"computed_price": 90.0}]
        mape = compute_mape(results, 100.0)
        assert mape == 10.0
        assert compute_mape([], 100.0) == 0.0

    def test_get_convergence_metrics(self):
        results = [{"computed_price": 10.0}, {"computed_price": 20.0}]
        res = get_convergence_metrics(results)
        assert res["count"] == 2
        assert res["mean_price"] == 15.0
        assert get_convergence_metrics([]) == {}
