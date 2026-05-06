"""Market data ingestion pipeline."""

from __future__ import annotations

import uuid
from datetime import date

import structlog

from src.data.transformers import clean_market_data
from src.database.repository import OptionRepository
from src.scrapers.scraper_factory import get_scraper

logger = structlog.get_logger(__name__)


class MarketDataPipeline:
    """
    Pipeline for scraping, validating, transforming, and storing market data.
    """

    def __init__(self, market: str) -> None:
        self.market = market
        self.repository = OptionRepository()

    async def run(self, trade_date: date) -> dict[str, int]:
        """
        Execute the full pipeline for a given market and date.
        Returns a summary of processed rows.
        """
        pipeline_run_id = uuid.uuid4()
        logger.info(
            "pipeline_started",
            market=self.market,
            date=trade_date.isoformat(),
            run_id=str(pipeline_run_id),
        )

        try:
            # 1. Scrape
            scraper = get_scraper(self.market)
            raw_data = await scraper.scrape(trade_date)
            await self.repository.log_audit(pipeline_run_id, "scrape", "success", len(raw_data))

            # 2. Transform & Clean
            cleaned_df = clean_market_data(raw_data)
            await self.repository.log_audit(
                pipeline_run_id, "transform", "success", len(cleaned_df)
            )

            # 3. Store
            inserted_count = await self.repository.upsert_market_data(cleaned_df, self.market)
            await self.repository.log_audit(pipeline_run_id, "store", "success", inserted_count)

            logger.info("pipeline_completed", market=self.market, inserted=inserted_count)
            return {"rows_inserted": inserted_count}

        except Exception as e:
            logger.error("pipeline_failed", market=self.market, error=str(e))
            await self.repository.log_audit(pipeline_run_id, "pipeline", "failed", 0, str(e))
            raise


def get_pipeline(market: str) -> MarketDataPipeline:
    """Factory function for market data pipelines."""
    return MarketDataPipeline(market)
