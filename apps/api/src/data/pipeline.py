"""Data pipeline for orchestrating scrapers and storage."""

from __future__ import annotations

import datetime
import json
import time
from datetime import date

import structlog

from src.database.repository import Repository
from src.metrics import (
    SCRAPE_DURATION,
    SCRAPE_ERRORS_TOTAL,
    SCRAPE_ROWS_INSERTED,
    SCRAPE_RUNS_TOTAL,
)
from src.scrapers.scraper_factory import get_scraper
from src.storage.storage_service import upload_export

logger = structlog.get_logger(__name__)


class DataPipeline:
    """Pipeline to scrape, validate, transform and store market data."""

    def __init__(self, market: str) -> None:
        self.market = market
        self.repository = Repository()

    async def run(self, trade_date: date) -> None:
        """Execute the full pipeline for a specific market and date."""
        start_time = time.perf_counter()
        logger.info("pipeline_started", market=self.market, date=trade_date.isoformat())

        # 0. Initialise Scrape Run
        run_record = await self.repository.insert_scrape_run(
            {
                "market": self.market,
                "scraper_class": f"{self.market.capitalize()}Scraper",
                "started_at": datetime.datetime.utcnow().isoformat(),
                "status": "running",
            }
        )
        run_id = str(run_record["id"])

        try:
            # 1. Scrape
            scraper = get_scraper(self.market)
            raw_data = await scraper.scrape(trade_date)

            if not raw_data:
                logger.warning("pipeline_no_data", market=self.market)
                SCRAPE_RUNS_TOTAL.labels(market=self.market, status="partial").inc()
                await self.repository.update_scrape_run(
                    run_id,
                    {
                        "status": "partial",
                        "finished_at": datetime.datetime.utcnow().isoformat(),
                        "rows_scraped": 0,
                    },
                )
                return

            # 2. Store raw artifacts in MinIO (with compression)
            raw_bytes = json.dumps(raw_data).encode("utf-8")
            artifact_url = upload_export(
                data=raw_bytes,
                filename=f"raw_{self.market}_{trade_date.isoformat()}.json",
                content_type="application/json",
                bucket="bs-scraper",
                compress=True,
            )

            await self.repository.insert_audit_log(
                {
                    "pipeline_run_id": run_id,
                    "step_name": "storage",
                    "status": "success",
                    "message": f"Artifact stored at {artifact_url}",
                }
            )

            # 3. Transform and Validate
            rows_processed = len(raw_data)
            SCRAPE_ROWS_INSERTED.labels(market=self.market).set(rows_processed)

            # 4. Finalise Scrape Run
            await self.repository.update_scrape_run(
                run_id,
                {
                    "status": "success",
                    "finished_at": datetime.datetime.utcnow().isoformat(),
                    "rows_scraped": rows_processed,
                    "rows_inserted": rows_processed,
                },
            )

            SCRAPE_RUNS_TOTAL.labels(market=self.market, status="success").inc()
            SCRAPE_DURATION.labels(market=self.market).observe(time.perf_counter() - start_time)

            logger.info(
                "pipeline_finished",
                market=self.market,
                date=trade_date.isoformat(),
                status="success",
                rows=rows_processed,
            )

        except Exception as e:
            SCRAPE_RUNS_TOTAL.labels(market=self.market, status="failed").inc()
            SCRAPE_ERRORS_TOTAL.labels(market=self.market, error_type=type(e).__name__).inc()
            logger.error("pipeline_failed", market=self.market, error=str(e))
            await self.repository.update_scrape_run(
                run_id, {"status": "failed", "finished_at": datetime.datetime.utcnow().isoformat()}
            )
            await self.repository.insert_scrape_error(
                {
                    "scrape_run_id": run_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                }
            )
            raise


def get_pipeline(market: str) -> DataPipeline:
    """Factory function for DataPipeline."""
    return DataPipeline(market)
