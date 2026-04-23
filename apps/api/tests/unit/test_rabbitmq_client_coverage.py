"""Unit tests for additional rabbitmq_client coverage."""

from unittest.mock import AsyncMock, patch

import pytest

import src.task_queues.rabbitmq_client as rabbitmq_client
from src.task_queues.rabbitmq_client import close_rabbitmq_connection, get_rabbitmq_connection


@pytest.mark.unit
async def test_get_rabbitmq_connection_reuse() -> None:
    """Test that connection is reused if already open."""
    # Reset global state
    rabbitmq_client._connection = None

    with patch("aio_pika.connect_robust", new_callable=AsyncMock) as mock_connect:
        mock_conn = AsyncMock()
        mock_conn.is_closed = False
        mock_connect.return_value = mock_conn

        # First call creates connection
        conn1 = await get_rabbitmq_connection()
        assert conn1 == mock_conn
        assert mock_connect.call_count == 1

        # Second call reuses connection
        conn2 = await get_rabbitmq_connection()
        assert conn2 == mock_conn
        assert mock_connect.call_count == 1


@pytest.mark.unit
async def test_close_rabbitmq_connection_flow() -> None:
    """Test the close connection logic."""
    mock_conn = AsyncMock()
    mock_conn.is_closed = False
    rabbitmq_client._connection = mock_conn

    # Successful close
    await close_rabbitmq_connection()
    mock_conn.close.assert_called_once()

    # Try closing again (should not call close again if already closed or None)
    mock_conn.is_closed = True
    await close_rabbitmq_connection()
    assert mock_conn.close.call_count == 1

    rabbitmq_client._connection = None
    await close_rabbitmq_connection()
    assert mock_conn.close.call_count == 1
