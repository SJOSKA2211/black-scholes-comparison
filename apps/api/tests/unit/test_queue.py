from typing import Any
import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import date
import aio_pika
from src.queue.publisher import publish_scrape_task, publish_experiment_task
from src.queue.consumer import handle_scrape_task

@pytest.mark.unit
class TestPublisher:
    @patch("src.queue.publisher.get_rabbitmq_connection")
    async def test_publish_scrape_task(self, mock_get_conn: Any) -> None:
        mock_conn = AsyncMock()
        mock_get_conn.return_value = mock_conn
        
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        
        mock_conn.channel.return_value.__aenter__.return_value = mock_channel
        mock_channel.get_exchange.return_value = mock_exchange
        
        await publish_scrape_task("spy", date(2026, 4, 22))
        
        mock_channel.get_exchange.assert_called_with("bs.tasks")
        mock_exchange.publish.assert_called_once()
        args, kwargs = mock_exchange.publish.call_args
        message = args[0]
        assert json.loads(message.body.decode())["market"] == "spy"
        assert kwargs["routing_key"] == "scrape"

    @patch("src.queue.publisher.get_rabbitmq_connection")
    async def test_publish_experiment_task(self, mock_get_conn: Any) -> None:
        mock_conn = AsyncMock()
        mock_get_conn.return_value = mock_conn
        
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        
        mock_conn.channel.return_value.__aenter__.return_value = mock_channel
        mock_channel.get_exchange.return_value = mock_exchange
        
        params = {"S_range": [90, 110]}
        await publish_experiment_task(params)
        
        assert mock_exchange.publish.called
        kwargs = mock_exchange.publish.call_args.kwargs
        assert kwargs["routing_key"] == "experiment"

@pytest.mark.unit
class TestConsumer:
    @patch("src.queue.consumer.DataPipeline")
    @patch("src.queue.consumer.get_supabase_client")
    async def test_handle_scrape_task(self, mock_supa: Any, mock_pipeline_class: Any) -> None:
        mock_msg = MagicMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_msg.body = json.dumps({"market": "spy", "run_id": "test-run", "rows": []}).encode()
        
        mock_process = AsyncMock()
        mock_msg.process.return_value = mock_process
        mock_process.__aenter__.return_value = mock_msg
        
        mock_pipeline = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline
        
        await handle_scrape_task(mock_msg)
        
        mock_pipeline_class.assert_called()
        # Verify it was called with spy and test-run
        args, kwargs = mock_pipeline_class.call_args
        assert kwargs["run_id"] == "test-run"
        assert args[1] == "spy"

    async def test_handle_scrape_task_failure(self) -> None:
        mock_msg = MagicMock(spec=aio_pika.abc.AbstractIncomingMessage)
        mock_msg.body = b"invalid json"
        
        with pytest.raises(json.JSONDecodeError):
             await handle_scrape_task(mock_msg)
