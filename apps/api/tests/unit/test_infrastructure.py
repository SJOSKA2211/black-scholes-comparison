from typing import Any
import pytest
from unittest.mock import MagicMock, patch
from src.config import get_settings
from src.exceptions import BlackScholesError, NumericalMethodError
from src.metrics import PRICE_DURATION_SECONDS, EXPERIMENT_PROGRESS

@pytest.mark.unit
class TestInfrastructure:
    def test_settings_load(self) -> None:
        with patch("src.config.Settings") as mock_settings_class:
            mock_settings_class.return_value.supabase_url = "http://test"
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.supabase_url == "http://test"

    def test_exceptions(self) -> None:
        ex = BlackScholesError(message="test")
        assert ex.message == "test"
        
        ex2 = NumericalMethodError("math error")
        assert "math error" in str(ex2)

    def test_metrics_definitions(self) -> None:
        assert "price_computation_duration_seconds" in PRICE_DURATION_SECONDS._name
        assert "experiment_grid_progress_ratio" in EXPERIMENT_PROGRESS._name

    @patch("src.metrics.Counter")
    def test_metrics_logging(self, mock_counter: Any) -> None:
        from src.metrics import PRICE_COMPUTATIONS_TOTAL
        assert PRICE_COMPUTATIONS_TOTAL is not None
