import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import aio_pika
import pytest

import src.task_queues.rabbitmq_client as rabbitmq_client
from src.task_queues.consumer import handle_experiment_task, handle_scrape_task, start_consumers
from src.task_queues.publisher import publish_experiment_task, publish_scrape_task
from src.task_queues.rabbitmq_client import close_rabbitmq_connection, get_rabbitmq_connection


@pytest.fixture(autouse=True)
def reset_rmq_global():
    rabbitmq_client._connection = None
    yield
    rabbitmq_client._connection = None


@pytest.mark.unit
class TestRabbitMQClient:
    @pytest.mark.asyncio
    @patch("src.task_queues.rabbitmq_client.aio_pika.connect_robust", new_callable=AsyncMock)
    @patch("src.task_queues.rabbitmq_client.get_settings")
    async def test_get_connection_reuse(self, mock_settings, mock_connect):
        mock_settings.return_value.rabbitmq_url = "amqp://test"
        mock_conn = AsyncMock()
        mock_conn.is_closed = False
        mock_connect.return_value = mock_conn

        c1 = await get_rabbitmq_connection()
        assert c1 == mock_conn
        assert mock_connect.call_count == 1

        c2 = await get_rabbitmq_connection()
        assert c2 == mock_conn
        assert mock_connect.call_count == 1

    @pytest.mark.asyncio
    async def test_close_connection(self):
        mock_conn = AsyncMock()
        mock_conn.is_closed = False
        rabbitmq_client._connection = mock_conn

        await close_rabbitmq_connection()
        mock_conn.close.assert_called_once()

        # Test already closed
        mock_conn.is_closed = True
        await close_rabbitmq_connection()
        assert mock_conn.close.call_count == 1


@pytest.mark.unit
class TestPublisher:
    @pytest.mark.asyncio
    @patch("src.task_queues.publisher.get_rabbitmq_connection")
    async def test_publish_scrape(self, mock_get_conn):
        mock_conn = MagicMock()  # Use MagicMock for the connection object
        mock_get_conn.return_value = mock_conn
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        # connection.channel() is a regular method returning an async context manager
        mock_conn.channel = MagicMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_channel
        mock_conn.channel.return_value = mock_cm

        mock_channel.declare_exchange.return_value = mock_exchange

        await publish_scrape_task("spy", date(2024, 1, 1))
        mock_exchange.publish.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.task_queues.publisher.get_rabbitmq_connection")
    async def test_publish_experiment(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_conn.channel = MagicMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_channel
        mock_conn.channel.return_value = mock_cm

        mock_channel.declare_exchange.return_value = mock_exchange

        await publish_experiment_task({"id": "test"})
        mock_exchange.publish.assert_called_once()


@pytest.mark.unit
class TestConsumer:
    @pytest.mark.asyncio
    @patch("src.task_queues.consumer.DataPipeline")
    async def test_handle_scrape_task(self, mock_pipeline_class):
        mock_msg = MagicMock()
        mock_msg.body = json.dumps({"market": "spy", "date": "2024-01-01"}).encode()
        mock_msg.process.return_value.__aenter__ = AsyncMock()
        mock_msg.process.return_value.__aexit__ = AsyncMock()

        mock_pipeline = MagicMock()
        mock_pipeline.run = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline

        await handle_scrape_task(mock_msg)
        mock_pipeline.run.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.task_queues.consumer.DataPipeline")
    async def test_handle_scrape_task_failure(self, mock_pipeline_class):
        mock_msg = MagicMock()
        mock_msg.body = json.dumps({"market": "spy", "date": "2024-01-01"}).encode()

        # Mock the context manager correctly
        mock_process = MagicMock()
        mock_process.__aenter__ = AsyncMock()
        mock_process.__aexit__ = AsyncMock(return_value=False)  # Do not suppress
        mock_msg.process.return_value = mock_process

        mock_pipeline = MagicMock()
        mock_pipeline.run = AsyncMock(side_effect=Exception("Fail"))
        mock_pipeline_class.return_value = mock_pipeline

        with pytest.raises(Exception, match="Fail"):
            await handle_scrape_task(mock_msg)

    @pytest.mark.asyncio
    async def test_handle_scrape_task_json_fail(self):
        mock_msg = MagicMock()
        mock_msg.body = b"invalid"
        mock_process = MagicMock()
        mock_process.__aenter__ = AsyncMock()
        mock_process.__aexit__ = AsyncMock(return_value=False)
        mock_msg.process.return_value = mock_process
        with pytest.raises(json.JSONDecodeError):
            await handle_scrape_task(mock_msg)

    @pytest.mark.asyncio
    @patch("scripts.run_experiments.run_experiments", new_callable=AsyncMock)
    async def test_handle_experiment_task_success(self, mock_run):
        mock_msg = MagicMock()
        mock_msg.body = json.dumps({"test": 1}).encode()
        mock_msg.process.return_value.__aenter__ = AsyncMock()
        mock_msg.process.return_value.__aexit__ = AsyncMock()

        await handle_experiment_task(mock_msg)
        mock_run.assert_called_once()

    @pytest.mark.asyncio
    @patch("scripts.run_experiments.run_experiments", new_callable=AsyncMock)
    async def test_handle_experiment_task_failure(self, mock_run):
        mock_msg = MagicMock()
        mock_msg.body = json.dumps({"test": 1}).encode()

        mock_process = MagicMock()
        mock_process.__aenter__ = AsyncMock()
        mock_process.__aexit__ = AsyncMock(return_value=False)
        mock_msg.process.return_value = mock_process

        mock_run.side_effect = Exception("Fail")
        with pytest.raises(Exception, match="Fail"):
            await handle_experiment_task(mock_msg)

    @pytest.mark.asyncio
    @patch("src.task_queues.consumer.get_rabbitmq_connection")
    async def test_start_consumers_success(self, mock_get_conn):
        mock_conn = AsyncMock()
        mock_get_conn.return_value = mock_conn
        mock_channel = AsyncMock()

        # connection.channel() is async in consumer.py:68?
        # No: await connection.channel() means it returns a coroutine.
        mock_conn.channel.return_value = mock_channel

        mock_queue = AsyncMock()
        mock_channel.declare_queue.return_value = mock_queue

        await start_consumers()
        mock_channel.set_qos.assert_called_once_with(prefetch_count=1)
        assert mock_channel.declare_queue.call_count == 2
        assert mock_queue.consume.call_count == 2

    @pytest.mark.asyncio
    @patch("src.task_queues.consumer.get_rabbitmq_connection")
    async def test_start_consumers_error(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("RMQ Fail")
        await start_consumers()


@pytest.mark.unit
class TestScrapers:
    def test_scraper_factory(self):
        from src.scrapers.scraper_factory import ScraperFactory

        s = ScraperFactory.get_scraper("spy", "run-1")
        assert s.run_id == "run-1"
        with pytest.raises(ValueError):
            ScraperFactory.get_scraper("invalid", "run-1")


@pytest.mark.unit
class TestWebSocket:
    @pytest.mark.asyncio
    async def test_manager_connect_disconnect(self):
        from src.websocket.manager import WebSocketManager

        manager = WebSocketManager()
        ws = AsyncMock()
        await manager.connect(ws, "channel-1")
        assert "channel-1" in manager._connections
        assert ws in manager._connections["channel-1"]

        await manager.disconnect(ws, "channel-1")
        assert "channel-1" not in manager._connections

    def test_channels(self):
        from src.websocket.channels import ALLOWED_CHANNELS

        assert "experiments" in ALLOWED_CHANNELS
        assert "scrapers" in ALLOWED_CHANNELS
