"""Unit tests for experiment runner script."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from src.scripts.run_experiments import main

@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_experiments_main() -> None:
    """Verify experiment runner main logic."""
    with patch("src.scripts.run_experiments.run_experiments", new_callable=AsyncMock) as mock_run:
        await main()
        assert mock_run.called
