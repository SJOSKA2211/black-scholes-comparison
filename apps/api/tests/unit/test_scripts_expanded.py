"""Expanded unit tests for run_experiments logic."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from src.scripts.run_experiments import run_experiments

@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_experiments_logic_success():
    """Verify run_experiments logic with mocked DB and engines."""
    payload = {"params": {"market": "spy"}, "user_id": "test-user"}
    
    mock_params = [
        {
            "id": "opt-1",
            "underlying_price": 100.0,
            "strike_price": 100.0,
            "maturity_years": 1.0,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call",
            "is_american": False
        }
    ]
    
    with patch("src.scripts.run_experiments.list_option_parameters", AsyncMock(return_value=mock_params)), \
         patch("src.scripts.run_experiments.upsert_method_result", AsyncMock(return_value=[{"id": "res-1"}])), \
         patch("src.scripts.run_experiments.upsert_validation_metrics", AsyncMock()) as mock_upsert_val, \
         patch("src.scripts.run_experiments.calculate_errors") as mock_calc_err, \
         patch("src.scripts.run_experiments.EXPERIMENT_PROGRESS"), \
         patch("src.scripts.run_experiments.EXPERIMENTS_TOTAL"), \
         patch("src.scripts.run_experiments.PRICE_MAPE_GAUGE"):
        
        mock_calc_err.return_value = {"absolute_error": 0.01, "relative_pct_error": 0.001}
        
        await run_experiments(payload)
        
        assert mock_upsert_val.called

@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_experiments_no_data():
    """Verify run_experiments handles empty DB data."""
    payload = {"params": {"market": "spy"}}
    
    with patch("src.scripts.run_experiments.list_option_parameters", AsyncMock(return_value=[])):
        await run_experiments(payload)
        # Should return early without crashing

@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_experiments_invalid_params():
    """Verify run_experiments handles invalid parameter rows."""
    payload = {"params": {"market": "spy"}}
    
    mock_params = [
        {
            "id": "opt-invalid",
            "underlying_price": -100.0, # Invalid
            "strike_price": 100.0,
            "maturity_years": 1.0,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call"
        }
    ]
    
    with patch("src.scripts.run_experiments.list_option_parameters", AsyncMock(return_value=mock_params)):
        await run_experiments(payload)
        # Should continue to next row or finish
