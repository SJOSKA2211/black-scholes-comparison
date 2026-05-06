"""Script to trigger market data collection."""

from __future__ import annotations

import argparse
import asyncio
from datetime import date

import structlog

from src.data.pipeline import get_pipeline

logger = structlog.get_logger(__name__)


async def main() -> None:
    """Main entry point for data collection."""
    parser = argparse.ArgumentParser(description="Collect market data for Black-Scholes platform.")
    parser.add_argument(
        "--market", type=str, required=True, choices=["spy", "nse"], help="Market to scrape"
    )
    parser.add_argument(
        "--date", type=str, default=date.today().isoformat(), help="Trade date in ISO format"
    )

    args = parser.parse_args()
    trade_date = date.fromisoformat(args.date)

    logger.info("collection_script_started", market=args.market, date=trade_date.isoformat())

    pipeline = get_pipeline(args.market)
    try:
        result = await pipeline.run(trade_date)
        logger.info(
            "collection_script_finished",
            market=result.market,
            scraped=result.rows_scraped,
            validated=result.rows_validated,
        )
    except Exception as error:
        logger.error("collection_script_failed", error=str(error))
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
