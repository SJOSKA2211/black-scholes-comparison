import logging
from unittest.mock import MagicMock

import pytest
import structlog

from src.logging_config import configure_logging


@pytest.mark.unit
def test_configure_logging(monkeypatch):
    """Test that logging configuration runs without error."""
    # Mock basicConfig to avoid issues with already initialized logging
    mock_basic_config = MagicMock()
    monkeypatch.setattr(logging, "basicConfig", mock_basic_config)

    # Mock structlog.configure
    mock_structlog_config = MagicMock()
    monkeypatch.setattr(structlog, "configure", mock_structlog_config)

    configure_logging()

    # Verify basicConfig was called
    mock_basic_config.assert_called_once()
    args, kwargs = mock_basic_config.call_args
    assert kwargs["level"] == logging.INFO

    # Verify structlog.configure was called
    mock_structlog_config.assert_called_once()
