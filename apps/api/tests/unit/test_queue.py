"""Unit tests for the RabbitMQ message queue layer."""

import asyncio
import json
from datetime import date
from typing import Any

import aio_pika
import pytest

from src.queue.consumer import handle_experiment_task, handle_scrape_task, start_consumers
from src.queue.publisher import publish_experiment_task, publish_scrape_task
from src.queue.rabbitmq_client import close_rabbitmq_connection, get_rabbitmq_connection


@pytest.fixture(autouse=True)
async def cleanup_rabbitmq() -> Any:  # noqa: ANN401
    """Ensure a fresh connection for each test and clean up after."""
    yield
    await close_rabbitmq_connection()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_and_consume_scrape() -> None:
    """Test publishing a scrape task and verify it is received in the queue."""
    test_date = date(2024, 1, 1)
    await publish_scrape_task("SPY", test_date)

    # Small delay to ensure RabbitMQ processes the message
    await asyncio.sleep(0.5)

    connection = await get_rabbitmq_connection()
    async with connection.channel() as channel:
        queue = await channel.declare_queue("bs.scrape", durable=True)
        message = await queue.get(timeout=5)
        assert message is not None

        async with message.process():
            payload = json.loads(message.body)
            assert payload["market"] == "SPY"
            assert payload["date"] == "2024-01-01"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_publish_and_consume_experiment() -> None:
    """Test publishing an experiment task."""
    test_params = {"method": "crank_nicolson", "underlying": 100.0}
    await publish_experiment_task(test_params)

    await asyncio.sleep(0.5)

    connection = await get_rabbitmq_connection()
    async with connection.channel() as channel:
        queue = await channel.declare_queue("bs.experiment", durable=True)
        message = await queue.get(timeout=5)
        assert message is not None

        async with message.process():
            payload = json.loads(message.body)
            assert payload["method"] == "crank_nicolson"
            assert payload["underlying"] == 100.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_queue_persistence() -> None:
    """Verify that messages are persistent."""
    await publish_scrape_task("NSE", date(2024, 2, 2))

    await asyncio.sleep(0.5)

    connection = await get_rabbitmq_connection()
    async with connection.channel() as channel:
        queue = await channel.declare_queue("bs.scrape", durable=True)
        message = await queue.get(timeout=5)
        assert message is not None
        async with message.process():
            assert message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handlers() -> None:
    """Test consumer handlers directly with mock-like real messages."""
    test_date = date(2024, 3, 3)
    await publish_scrape_task("SPY", test_date)

    await asyncio.sleep(0.5)

    connection = await get_rabbitmq_connection()
    async with connection.channel() as channel:
        queue = await channel.declare_queue("bs.scrape", durable=True)
        message: aio_pika.abc.AbstractIncomingMessage = await queue.get(timeout=5)
        assert message is not None
        # Call handler
        await handle_scrape_task(message)

    await publish_experiment_task({"test": "data"})
    await asyncio.sleep(0.5)
    async with connection.channel() as channel:
        queue = await channel.declare_queue("bs.experiment", durable=True)
        exp_message: aio_pika.abc.AbstractIncomingMessage = await queue.get(timeout=5)
        assert exp_message is not None
        await handle_experiment_task(exp_message)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_start_consumers() -> None:
    """Test starting consumers."""
    await start_consumers()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_close_rabbitmq_connection_none() -> None:
    """Test closing the connection when it is already None or closed."""
    # Ensure it's None
    await close_rabbitmq_connection()
    # Call again to trigger the 'if not _connection' branch
    await close_rabbitmq_connection()
