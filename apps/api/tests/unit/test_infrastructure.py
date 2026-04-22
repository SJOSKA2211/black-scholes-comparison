import pytest
import os
from unittest.mock import MagicMock, patch
from src.config import get_settings, Settings
from src.exceptions import BlackScholesError, NumericalMethodError
from src.metrics import PRICE_COMPUTATION_DURATION_SECONDS, EXPERIMENT_GRID_PROGRESS

@pytest.mark.unit
class TestInfrastructure:
    def test_settings_load(self):
        with patch("src.config.Settings") as mock_settings_class:
            mock_settings_class.return_value.supabase_url = "http://test"
            get_settings.cache_clear()
            settings = get_settings()
            assert settings.supabase_url == "http://test"

    def test_exceptions(self):
        ex = BlackScholesError(message="test")
        assert ex.message == "test"
        
        ex2 = NumericalMethodError("math error")
        assert "math error" in str(ex2)

    def test_metrics_definitions(self):
        assert PRICE_COMPUTATION_DURATION_SECONDS._name == "black_scholes_price_computation_duration_seconds"
        assert EXPERIMENT_GRID_PROGRESS._name == "black_scholes_experiment_grid_progress_ratio"

    @patch("src.logging_config.structlog")
    def test_logging_config(self, mock_structlog):
        from src.logging_config import configure_logging
        configure_logging()
        assert mock_structlog.configure.called
