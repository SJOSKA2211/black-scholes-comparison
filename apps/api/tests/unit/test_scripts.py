"""Unit tests for experiment runner script."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
import pytest
from src.scripts.run_experiments import main

@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_experiments_main() -> None:
    """Verify experiment runner main logic."""
    # Patch the publisher to avoid real RabbitMQ calls
    with patch("src.scripts.run_experiments.publish_experiment_task", new_callable=AsyncMock) as mock_publish:
        await main()
        assert mock_publish.called
