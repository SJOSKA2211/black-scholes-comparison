"""Validate infrastructure and compression using real scraped data (Zero-Mock)."""

import asyncio
from datetime import date

import structlog
from src.data.pipeline import get_pipeline
from src.cache.redis_client import get_redis
from src.queue.publisher import publish_scrape_task
from src.logging_config import setup_logging

setup_logging()
logger = structlog.get_logger(__name__)


async def validate():
    trade_date = date.today()
    
    # 1. Run Pipeline for SPY (Real Data + Compression + MinIO)
    logger.info("step_1_pipeline_spy")
    spy_pipeline = get_pipeline("spy")
    await spy_pipeline.run(trade_date)
    
    # 2. Run Pipeline for NSE (Real Data + Compression + MinIO)
    logger.info("step_2_pipeline_nse")
    nse_pipeline = get_pipeline("nse")
    await nse_pipeline.run(trade_date)

    # 3. Test Redis Cache
    logger.info("step_3_test_redis")
    redis = get_redis()
    cache_key = f"validation:{trade_date.isoformat()}"
    await redis.set(cache_key, "validated", ex=300)
    val = await redis.get(cache_key)
    assert val == "validated", "Redis cache failed"
    logger.info("redis_validation_success")

    # 4. Test RabbitMQ Publisher
    logger.info("step_4_test_rabbitmq")
    await publish_scrape_task("spy", trade_date)
    logger.info("rabbitmq_validation_success")

    logger.info("infrastructure_validation_complete", status="PASS")


if __name__ == "__main__":
    asyncio.run(validate())
