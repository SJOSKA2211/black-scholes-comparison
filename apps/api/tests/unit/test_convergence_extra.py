import pytest
from src.analysis.convergence import analyze_convergence_order

@pytest.mark.unit
class TestConvergenceExtra:
    def test_analyze_convergence_low_resolutions(self):
        # Coverage for line 52: len(resolutions) < 2 after filtering
        results = [
            {"num_steps": 10, "error": 0.01},
            {"num_steps": 0, "error": 0.0025}, # invalid resolution
        ]
        res = analyze_convergence_order(results)
        assert res["convergence_order"] == 0.0

    def test_analyze_convergence_dt_resolution(self):
        # Coverage for lines 35-43: no resolution, use dt
        results = [
            {"parameter_set": {"dt": 0.1}, "error": 0.01},
            {"parameter_set": {"dt": 0.05}, "error": 0.0025},
        ]
        res = analyze_convergence_order(results)
        assert abs(res["convergence_order"] - 2.0) < 1e-10

    def test_analyze_convergence_invalid_dt(self):
        # Coverage for line 42 branch (delta_t <= 0)
        results = [
            {"parameter_set": {"dt": 0.0}, "error": 0.01},
            {"parameter_set": {"dt": -0.1}, "error": 0.01},
        ]
        res = analyze_convergence_order(results)
        assert res["convergence_order"] == 0.0
