"""Unit tests for the RabbitMQ client."""
from unittest.mock import patch, AsyncMock
import pytest
from src.queue.rabbitmq_client import get_rabbitmq_connection

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_rabbitmq_connection():
    """Test that get_rabbitmq_connection returns a connection."""
    with patch("aio_pika.connect_robust", new_callable=AsyncMock) as mock_connect:
        mock_conn = AsyncMock()
        mock_connect.return_value = mock_conn
        
        conn = await get_rabbitmq_connection()
        
        assert conn == mock_conn
        mock_connect.assert_called_once()
