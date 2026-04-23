import pytest

from src.analysis.convergence import analyze_convergence_order
from src.analysis.statistics import compute_mape, get_convergence_metrics


@pytest.mark.unit
class TestAnalysis:
    def test_analyze_convergence_order(self) -> None:
        results = [{"dt": 0.1, "error": 0.01}, {"dt": 0.05, "error": 0.0025}]
        res = analyze_convergence_order(results)
        assert abs(res["convergence_order"] - 2.0) < 1e-10
        assert analyze_convergence_order([])["convergence_order"] == 0.0

    def test_compute_mape(self) -> None:
        results = [{"computed_price": 110.0}, {"computed_price": 90.0}]
        mape = compute_mape(results, 100.0)
        assert mape == 10.0
        assert compute_mape([], 100.0) == 0.0

    def test_get_convergence_metrics(self) -> None:
        results = [{"computed_price": 10.0}, {"computed_price": 20.0}]
        res = get_convergence_metrics(results)
        assert res["count"] == 2
        assert res["mean_price"] == 15.0
        assert get_convergence_metrics([]) == {}
