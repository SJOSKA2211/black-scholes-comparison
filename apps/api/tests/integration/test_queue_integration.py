"""Integration tests for RabbitMQ task queues.
Strictly zero-mock: uses real RabbitMQ instance.
"""

import asyncio
import json
import pytest
from src.task_queues.publisher import publish_scrape_task, publish_experiment_task
from src.task_queues.rabbitmq_client import get_rabbitmq_connection

@pytest.mark.integration
class TestRabbitMQIntegration:
    @pytest.mark.asyncio
    async def test_publish_and_declare_queues(self):
        """Test that we can publish and that queues are declared correctly."""
        # 1. Publish tasks
        await publish_scrape_task("spy", "2024-01-01")
        await publish_experiment_task({"id": "integration-test-exp"})
        
        # 2. Verify connection and channel
        conn = await get_rabbitmq_connection()
        async with conn.channel() as channel:
            # Pass passive=True to check if queue exists without creating it
            scrape_queue = await channel.declare_queue("bs.scrape", passive=True)
            exp_queue = await channel.declare_queue("bs.experiment", passive=True)
            
            assert scrape_queue.declaration_result.message_count >= 1
            assert exp_queue.declaration_result.message_count >= 1
            
            # Cleanup: Purge queues
            await scrape_queue.purge()
            await exp_queue.purge()

    @pytest.mark.asyncio
    async def test_robust_connection(self):
        """Test that we can get a robust connection and it's reuse logic."""
        c1 = await get_rabbitmq_connection()
        c2 = await get_rabbitmq_connection()
        assert c1 is c2
        assert not c1.is_closed
