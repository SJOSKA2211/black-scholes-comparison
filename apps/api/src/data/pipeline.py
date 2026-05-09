"""Data pipeline — coordinates scrapers, validators, transformers, and repository."""

from __future__ import annotations

from datetime import date  # noqa: TCH003
from typing import Any

import structlog
from pydantic import BaseModel

from src.data.transformers import transform_to_db_market_data, transform_to_db_params
from src.data.validators import validate_quote
from src.database.repository import upsert_market_data, upsert_option_parameters
from src.metrics import SCRAPE_ROWS_TOTAL

logger = structlog.get_logger(__name__)


class PipelineResult(BaseModel):
    """Result of a pipeline run."""

    market: str
    trade_date: date
    rows_scraped: int
    rows_validated: int
    rows_inserted: int
    status: str


class DataPipeline:
    """Coordinates the data extraction, validation, and persistence process."""

    def __init__(self, market: str, scraper: Any) -> None:
        self.market = market
        self.scraper = scraper

    async def run(self, trade_date: date) -> PipelineResult:
        """Execute the pipeline for a given date."""
        logger.info("pipeline_started", market=self.market, date=trade_date.isoformat())

        try:
            scraper_result = await self.scraper.run(trade_date)
            raw_quotes = scraper_result.quotes

            valid_quotes = [q for q in raw_quotes if validate_quote(q)]

            inserted_count = 0
            for quote in valid_quotes:
                try:
                    # 1. Upsert option parameters to get/create the ID
                    param_dict = transform_to_db_params(quote, trade_date)
                    opt_resp = await upsert_option_parameters(param_dict)
                    option_id = opt_resp[0]["id"]

                    # 2. Upsert market data for this option and date
                    market_dict = transform_to_db_market_data(quote, option_id, trade_date)
                    await upsert_market_data([market_dict])

                    inserted_count += 1
                except Exception as e:
                    logger.error("persistence_failed", quote=quote, error=str(e))
                    continue

            SCRAPE_ROWS_TOTAL.labels(market=self.market, status="raw").inc(len(raw_quotes))
            SCRAPE_ROWS_TOTAL.labels(market=self.market, status="validated").inc(len(valid_quotes))
            SCRAPE_ROWS_TOTAL.labels(market=self.market, status="inserted").inc(inserted_count)

            logger.info(
                "pipeline_finished",
                market=self.market,
                scraped=len(raw_quotes),
                validated=len(valid_quotes),
                inserted=inserted_count,
            )

            return PipelineResult(
                market=self.market,
                trade_date=trade_date,
                rows_scraped=len(raw_quotes),
                rows_validated=len(valid_quotes),
                rows_inserted=inserted_count,
                status="success",
            )
        except Exception as error:
            logger.error("pipeline_failed", market=self.market, error=str(error))
            return PipelineResult(
                market=self.market,
                trade_date=trade_date,
                rows_scraped=0,
                rows_validated=0,
                rows_inserted=0,
                status="failed",
            )


def get_pipeline(market: str) -> DataPipeline:
    """Factory for DataPipeline."""
    m = market.lower()
    if m == "spy":
        from src.scrapers.spy_scraper import SpyScraper

        return DataPipeline("spy", SpyScraper())
    if m == "nse":
        # Note: using nse_next_scraper as indicated in tests
        from src.scrapers.nse_next_scraper import NseScraper

        return DataPipeline("nse", NseScraper())
    raise ValueError(f"Unsupported market: {market}")
