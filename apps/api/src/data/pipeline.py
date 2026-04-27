"""Data pipeline — orchestrates scraping, transformation, validation, and storage."""

from __future__ import annotations

import time
from datetime import date
from typing import Any

import pandas as pd
import structlog

from src.data.transformers import transform_batch_df
from src.data.validators import validate_quote
from src.database.repository import (
    create_audit_log,
    insert_market_data,
    update_scrape_run,
    upsert_option_parameters,
)
from src.metrics import SCRAPE_DURATION, SCRAPE_RUNS_TOTAL
from src.scrapers.scraper_factory import ScraperFactory

logger = structlog.get_logger(__name__)


def get_pipeline(market: str, run_id: str | None = None) -> DataPipeline:
    """Factory function for DataPipeline."""
    import uuid

    actual_run_id = run_id or str(uuid.uuid4())
    return DataPipeline(run_id=actual_run_id, market=market)


class DataPipeline:
    """Orchestrates the end-to-end data flow."""

    def __init__(self, run_id: str, market: str | None = None) -> None:
        self.run_id = run_id
        self.market = market

    async def process_rows(self, rows: list[dict[str, Any]], market: str, trade_date: date) -> int:
        """Handles Transformation, Validation, and Persistence for a batch of rows."""
        await create_audit_log(self.run_id, "transform_validate", "started")
        params_list = transform_batch_df(pd.DataFrame(rows), market_source=market) if rows else []

        inserted_count = 0
        market_data_to_insert = []

        for i, params in enumerate(params_list):
            try:
                # Validate
                validate_quote(
                    {
                        "bid": rows[i].get("bid_price", 0),
                        "ask": rows[i].get("ask_price", 0),
                        "underlying": params.underlying_price,
                    }
                )

                # Persistence
                option_id = await upsert_option_parameters(params.model_dump())

                # Prepare market data
                orig_row = rows[i]
                market_data_to_insert.append(
                    {
                        "option_id": option_id,
                        "trade_date": trade_date.isoformat(),
                        "bid_price": float(orig_row.get("bid_price", 0)),
                        "ask_price": float(orig_row.get("ask_price", 0)),
                        "volume": int(orig_row.get("volume", 0)),
                        "open_interest": int(orig_row.get("open_interest", 0)),
                        "data_source": market,
                    }
                )
                inserted_count += 1
            except Exception as error:
                logger.warning("row_skipped", error=str(error), run_id=self.run_id, row_index=i)
                continue

        # 3. Batch Insert Market Data
        if market_data_to_insert:
            await insert_market_data(market_data_to_insert)

        await create_audit_log(
            self.run_id, "transform_validate", "completed", rows_affected=inserted_count
        )
        return inserted_count

    async def run(self, trade_date: date | None = None) -> dict[str, Any]:
        """Full run: Scrape -> Transform -> Validate -> Upsert."""
        if not self.market:
            raise ValueError("Market must be specified for a full run.")

        if trade_date is None:
            trade_date = date.today()

        start_time = time.time()
        market = self.market

        SCRAPE_RUNS_TOTAL.labels(market=market, status="running").inc()

        try:
            # 0. Ensure run record exists
            from src.database.repository import upsert_scrape_run

            await upsert_scrape_run(self.run_id, market)

            # 1. Scrape
            await create_audit_log(self.run_id, "scrape", "started")
            scraper = ScraperFactory.get_scraper(market, self.run_id)
            rows = await scraper.scrape(trade_date)
            await create_audit_log(self.run_id, "scrape", "completed", rows_affected=len(rows))

            # 2. Process
            inserted_count = await self.process_rows(rows, market, trade_date)

            # Success
            result = {
                "status": "success",
                "rows_scraped": len(rows),
                "rows_inserted": inserted_count,
                "duration": time.time() - start_time,
            }
            await update_scrape_run(
                self.run_id,
                {
                    "status": "success",
                    "rows_scraped": len(rows),
                    "rows_validated": inserted_count,
                    "rows_inserted": inserted_count,
                    "error_count": 0,
                    "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
            )

            # 3. Notification (Section 10.1)
            from src.database.repository import insert_notification

            await insert_notification(
                user_id="a24fb1a2-700a-4590-8d43-2930596a14f2",
                title=f"Scrape Completed: {market.upper()}",
                body=f"Successfully ingested {inserted_count} market quotes.",
                severity="info",
                channel="in_app",
                action_url="/scrapers",
            )

            SCRAPE_RUNS_TOTAL.labels(market=market, status="success").inc()
            return result

        except Exception as error:
            logger.error("pipeline_failed", error=str(error), run_id=self.run_id)
            await create_audit_log(self.run_id, "pipeline", "failed", message=str(error))
            await update_scrape_run(self.run_id, {"status": "failed", "error_count": 1})

            from src.database.repository import insert_notification

            await insert_notification(
                user_id="a24fb1a2-700a-4590-8d43-2930596a14f2",
                title=f"Scrape Failed: {market.upper()}",
                body=f"Error: {error!s}",
                severity="error",
                channel="in_app",
            )

            SCRAPE_RUNS_TOTAL.labels(market=market, status="failed").inc()
            return {"status": "failed", "error": str(error)}
        finally:
            duration = time.time() - start_time
            SCRAPE_DURATION.labels(market=market).observe(duration)
