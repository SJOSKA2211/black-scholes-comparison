import json
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aio_pika
import pytest

from src.task_queues.consumer import handle_experiment_task, handle_scrape_task, start_consumers
from src.task_queues.publisher import publish_experiment_task, publish_scrape_task


@pytest.mark.unit
class TestPublisher:
    @patch("src.task_queues.publisher.get_rabbitmq_connection")
    async def test_publish_scrape_task(self, mock_get_conn: Any) -> None:
        mock_conn = AsyncMock()
        mock_get_conn.return_value = mock_conn

        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        # connection.channel() should be a regular method returning an async context manager
        mock_conn.channel = MagicMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_channel
        mock_conn.channel.return_value = mock_cm

        mock_channel.declare_exchange.return_value = mock_exchange

        await publish_scrape_task("spy", date(2026, 4, 22))

        mock_channel.declare_exchange.assert_called()
        mock_exchange.publish.assert_called_once()
        args, _ = mock_exchange.publish.call_args
        message = args[0]
        assert json.loads(message.body.decode())["market"] == "spy"

    @patch("src.task_queues.publisher.get_rabbitmq_connection")
    async def test_publish_experiment_task(self, mock_get_conn: Any) -> None:
        mock_conn = AsyncMock()
        mock_get_conn.return_value = mock_conn

        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_conn.channel = MagicMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_channel
        mock_conn.channel.return_value = mock_cm

        mock_channel.declare_exchange.return_value = mock_exchange

        params = {"S_range": [90, 110]}
        await publish_experiment_task(params)

        mock_exchange.publish.assert_called_once()
        kwargs = mock_exchange.publish.call_args.kwargs
        assert kwargs["routing_key"] == "experiment"


@pytest.mark.unit
class TestConsumer:
    @patch("src.task_queues.consumer.DataPipeline")
    async def test_handle_scrape_task(self, mock_pipeline_class: Any) -> None:
        mock_msg = MagicMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_msg.body = json.dumps({"market": "spy", "date": "2026-04-22"}).encode()

        # Mock message processing context manager
        mock_process = AsyncMock()
        mock_msg.process.return_value = mock_process
        mock_process.__aenter__.return_value = mock_msg

        mock_pipeline = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline

        await handle_scrape_task(mock_msg)

        mock_pipeline_class.assert_called()
        args, kwargs = mock_pipeline_class.call_args
        assert kwargs["market"] == "spy"

    async def test_handle_scrape_task_failure(self) -> None:
        mock_msg = MagicMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_msg.body = b"invalid json"

        with pytest.raises(json.JSONDecodeError):
            await handle_scrape_task(mock_msg)

    @patch("src.task_queues.consumer.DataPipeline")
    async def test_handle_scrape_task_execution_failure(self, mock_pipeline_class: Any) -> None:
        mock_msg = MagicMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_msg.body = json.dumps({"market": "spy", "date": "2026-04-22"}).encode()
        mock_process = AsyncMock()
        mock_msg.process.return_value = mock_process

        mock_pipeline = AsyncMock()
        mock_pipeline.run.side_effect = Exception("Pipeline failed")
        mock_pipeline_class.return_value = mock_pipeline

        with pytest.raises(Exception, match="Pipeline failed"):
            await handle_scrape_task(mock_msg)

    @patch("scripts.run_experiments.run_experiments")
    async def test_handle_experiment_task(self, mock_run_exp: Any) -> None:
        mock_msg = MagicMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_msg.body = json.dumps({"test": "data"}).encode()
        mock_process = AsyncMock()
        mock_msg.process.return_value = mock_process

        # Success
        await handle_experiment_task(mock_msg)
        mock_run_exp.assert_called_once_with({"test": "data"})

        # Failure
        mock_run_exp.side_effect = Exception("Run failed")
        with pytest.raises(Exception, match="Run failed"):
            await handle_experiment_task(mock_msg)

    @patch("src.task_queues.consumer.get_rabbitmq_connection")
    async def test_start_consumers_failure(self, mock_get_conn: Any) -> None:
        mock_get_conn.side_effect = Exception("Conn failed")
        # Should log but not raise
        await start_consumers()
