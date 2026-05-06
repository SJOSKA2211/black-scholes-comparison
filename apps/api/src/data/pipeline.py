"""Data pipeline for orchestrating scrapers and storage."""

from __future__ import annotations

from datetime import date

import structlog

from src.database.repository import Repository
from src.scrapers.scraper_factory import get_scraper

logger = structlog.get_logger(__name__)


class DataPipeline:
    """Pipeline to scrape, validate, transform and store market data."""

    def __init__(self, market: str) -> None:
        self.market = market
        self.repository = Repository()

    async def run(self, trade_date: date) -> None:
        """Execute the full pipeline for a specific market and date."""
        logger.info("pipeline_started", market=self.market, date=trade_date.isoformat())

        try:
            # 1. Scrape
            scraper = get_scraper(self.market)
            await scraper.scrape(trade_date)

            # 2. Store raw artifacts in MinIO (omitted for brevity in this block)

            # 3. Transform and Validate
            # (Logic depends on the specific scraper's output)

            # 4. Upsert to Supabase
            # await self.repository.upsert_market_data(processed_data)

            logger.info(
                "pipeline_finished",
                market=self.market,
                date=trade_date.isoformat(),
                status="success",
            )

        except Exception as e:
            logger.error("pipeline_failed", market=self.market, error=str(e))
            raise


def get_pipeline(market: str) -> DataPipeline:
    """Factory function for DataPipeline."""
    return DataPipeline(market)
