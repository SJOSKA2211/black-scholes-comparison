"""Unit tests for run_experiments script."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from src.scripts.run_experiments import run_experiments, main

@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_experiments_success():
    payload = {"params": {"market": "spy"}}
    mock_params = [{
        "id": "1",
        "underlying_price": 100,
        "strike_price": 100,
        "maturity_years": 1,
        "volatility": 0.2,
        "risk_free_rate": 0.05,
        "option_type": "call",
        "is_american": False
    }]
    
    with patch("src.scripts.run_experiments.list_option_parameters", AsyncMock(return_value=mock_params)), \
         patch("src.scripts.run_experiments.upsert_method_result", AsyncMock(return_value=[{"id": "res1"}])), \
         patch("src.scripts.run_experiments.upsert_validation_metrics", AsyncMock()), \
         patch("src.scripts.run_experiments.EXPERIMENT_PROGRESS"), \
         patch("src.scripts.run_experiments.EXPERIMENTS_TOTAL"), \
         patch("src.scripts.run_experiments.PRICE_MAPE_GAUGE"):
        await run_experiments(payload)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_experiments_no_params():
    with patch("src.scripts.run_experiments.list_option_parameters", AsyncMock(return_value=[])):
        await run_experiments({"params": {"market": "spy"}})

@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_experiments_invalid_row():
    mock_params = [{"id": "1", "underlying_price": "bad"}]
    with patch("src.scripts.run_experiments.list_option_parameters", AsyncMock(return_value=mock_params)):
        await run_experiments({"params": {"market": "spy"}})

@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_experiments_step_fail():
    mock_params = [{
        "id": "1", "underlying_price": 100, "strike_price": 100, "maturity_years": 1,
        "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call"
    }]
    with patch("src.scripts.run_experiments.list_option_parameters", AsyncMock(return_value=mock_params)), \
         patch("src.scripts.run_experiments.BlackScholesAnalytical") as m:
        m().price.side_effect = Exception("err")
        await run_experiments({"params": {"market": "spy"}})

@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_experiments_metrics_fail():
    payload = {"params": {"market": "spy"}}
    mock_params = [{
        "id": "1", "underlying_price": 100, "strike_price": 100, "maturity_years": 1,
        "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call"
    }]
    with patch("src.scripts.run_experiments.list_option_parameters", AsyncMock(return_value=mock_params)), \
         patch("src.scripts.run_experiments.upsert_method_result", AsyncMock(return_value=[{"id": "res1"}])), \
         patch("src.scripts.run_experiments.upsert_validation_metrics", AsyncMock(side_effect=Exception("err"))), \
         patch("src.scripts.run_experiments.EXPERIMENT_PROGRESS"), \
         patch("src.scripts.run_experiments.EXPERIMENTS_TOTAL"), \
         patch("src.scripts.run_experiments.PRICE_MAPE_GAUGE"):
        await run_experiments(payload)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_main():
    with patch("src.scripts.run_experiments.run_experiments", AsyncMock()) as m:
        await main()
        assert m.called
