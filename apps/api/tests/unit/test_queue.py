"""Unit tests for RabbitMQ publisher."""
from __future__ import annotations
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
import aio_pika
from src.queue.publisher import publish_scrape_task, publish_experiment_task

@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_scrape_task() -> None:
    """Verify scrape task publishing."""
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()
    
    # Configure connection.channel() to return an async context manager
    # async with connection.channel() as channel:
    mock_channel_context = AsyncMock()
    mock_channel_context.__aenter__.return_value = mock_channel
    # NOTE: connection.channel must be a regular MagicMock to be used in 'async with' 
    # without being awaited first.
    mock_connection.channel = MagicMock(return_value=mock_channel_context)
    
    mock_channel.declare_exchange.return_value = mock_exchange
    
    with patch("src.queue.publisher.get_rabbitmq_connection", return_value=mock_connection):
        await publish_scrape_task("spy", date(2025, 1, 1))
        
        mock_exchange.publish.assert_called_once()
        args, kwargs = mock_exchange.publish.call_args
        assert isinstance(args[0], aio_pika.Message)
        assert kwargs["routing_key"] == "scrape"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_experiment_task() -> None:
    """Verify experiment task publishing."""
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()
    
    mock_channel_context = AsyncMock()
    mock_channel_context.__aenter__.return_value = mock_channel
    mock_connection.channel = MagicMock(return_value=mock_channel_context)
    
    mock_channel.declare_exchange.return_value = mock_exchange
    
    with patch("src.queue.publisher.get_rabbitmq_connection", return_value=mock_connection):
        await publish_experiment_task({"grid": "params"})
        
        mock_exchange.publish.assert_called_once()
        args, kwargs = mock_exchange.publish.call_args
        assert isinstance(args[0], aio_pika.Message)
        assert kwargs["routing_key"] == "experiment"
