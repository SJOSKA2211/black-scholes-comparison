import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.task_queues.consumer import handle_experiment_task, handle_scrape_task, start_consumers


@pytest.mark.unit
class TestConsumerFinal:
    async def test_handle_scrape_task_empty(self):
        message = AsyncMock()
        # Mocking the async context manager 'process'
        process_mock = MagicMock()
        process_mock.__aenter__ = AsyncMock()
        process_mock.__aexit__ = AsyncMock()
        message.process = MagicMock(return_value=process_mock)

        message.body = json.dumps({"run_id": "1", "market": "spy", "date": "2024-01-01"}).encode()

        with patch("src.task_queues.consumer.DataPipeline") as mock_pipeline:
            await handle_scrape_task(message)
            assert not mock_pipeline.return_value.process_rows.called

    @patch("scripts.run_experiments.run_experiments", new_callable=AsyncMock)
    async def test_handle_experiment_task(self, mock_run):
        message = AsyncMock()
        process_mock = MagicMock()
        process_mock.__aenter__ = AsyncMock()
        process_mock.__aexit__ = AsyncMock()
        message.process = MagicMock(return_value=process_mock)

        message.body = json.dumps({"exp_id": "1"}).encode()
        await handle_experiment_task(message)
        # Verify it processes
        assert message.process.called
        assert mock_run.called

    @patch("src.task_queues.consumer.get_rabbitmq_connection")
    async def test_start_consumers_success(self, mock_get_conn):
        mock_conn = AsyncMock()
        mock_get_conn.return_value = mock_conn
        mock_channel = AsyncMock()
        mock_conn.channel.return_value = mock_channel

        await start_consumers()
        assert mock_channel.set_qos.called
        assert mock_channel.declare_queue.called

    @patch("src.task_queues.consumer.get_rabbitmq_connection")
    async def test_start_consumers_failure(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("RMQ Fail")
        await start_consumers()
        # Should log error and not crash
