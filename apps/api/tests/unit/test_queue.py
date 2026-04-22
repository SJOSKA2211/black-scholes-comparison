import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import date
import aio_pika
from src.queue.publisher import publish_scrape_task, publish_experiment_task
from src.queue.consumer import handle_scrape_task

@pytest.mark.unit
class TestPublisher:
    @pytest.mark.asyncio
    @patch("src.queue.publisher.get_rabbitmq_connection")
    async def test_publish_scrape_task(self, mock_get_conn: AsyncMock) -> None:
        # Setup
        mock_conn = AsyncMock()
        mock_get_conn.return_value = mock_conn
        
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        
        # Configure connection.channel() to return an async context manager
        mock_conn.channel = MagicMock()
        mock_conn.channel.return_value.__aenter__ = AsyncMock(return_value=mock_channel)
        mock_conn.channel.return_value.__aexit__ = AsyncMock()
        
        mock_channel.get_exchange.return_value = mock_exchange
        
        # Execute
        from datetime import date
        await publish_scrape_task("spy", date(2026, 4, 22))
        
        # Verify
        mock_channel.get_exchange.assert_called_with("bs.tasks")
        mock_exchange.publish.assert_called_once()
        args, kwargs = mock_exchange.publish.call_args
        message = args[0]
        assert json.loads(message.body.decode()) == {"market": "spy", "date": "2026-04-22"}
        assert kwargs["routing_key"] == "scrape"

    @pytest.mark.asyncio
    @patch("src.queue.publisher.get_rabbitmq_connection")
    async def test_publish_experiment_task(self, mock_get_conn: AsyncMock) -> None:
        mock_conn = AsyncMock()
        mock_get_conn.return_value = mock_conn
        
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()
        
        mock_conn.channel = MagicMock()
        mock_conn.channel.return_value.__aenter__ = AsyncMock(return_value=mock_channel)
        mock_conn.channel.return_value.__aexit__ = AsyncMock()
        
        mock_channel.get_exchange.return_value = mock_exchange
        
        params = {"S_range": [90, 110]}
        await publish_experiment_task(params)
        
        assert mock_exchange.publish.called
        kwargs = mock_exchange.publish.call_args.kwargs
        assert kwargs["routing_key"] == "experiment"

@pytest.mark.unit
class TestConsumer:
    @pytest.mark.asyncio
    @patch("src.queue.consumer.DataPipeline")
    async def test_handle_scrape_task(self, mock_pipeline_class: MagicMock) -> None:
        # Setup
        mock_msg = MagicMock(spec=aio_pika.IncomingMessage)
        mock_msg.body = json.dumps({"market": "spy", "run_id": "test-run", "rows": []}).encode()
        
        # mock_msg.process() is an async context manager
        mock_process = AsyncMock()
        mock_msg.process.return_value = mock_process
        mock_process.__aenter__ = AsyncMock(return_value=mock_msg)
        mock_process.__aexit__ = AsyncMock()
        
        mock_pipeline = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline
        
        # Execute
        await handle_scrape_task(mock_msg)
        
        # Verify
        mock_pipeline_class.assert_called_with(run_id="test-run")
        mock_pipeline.process_rows.assert_called_with([])

    @pytest.mark.asyncio
    @patch("src.queue.consumer.DataPipeline")
    async def test_handle_scrape_task_failure(self, mock_pipeline_class: MagicMock) -> None:
        mock_msg = MagicMock(spec=aio_pika.IncomingMessage)
        mock_msg.body = b"invalid json"
        
        # Should catch error and not crash
        with pytest.raises(json.JSONDecodeError):
             await handle_scrape_task(mock_msg)
