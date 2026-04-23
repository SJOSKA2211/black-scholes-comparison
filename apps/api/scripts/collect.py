"""CLI script for manual and scheduled market data collection."""

from __future__ import annotations

import argparse
import asyncio
from datetime import date

import structlog

from src.data.pipeline import get_pipeline

logger = structlog.get_logger(__name__)

async def run_collection(market: str, target_date_str: str) -> None:
    """
    CLI entry point for running a specific scraper.
    """
    try:
        target_date = date.fromisoformat(target_date_str)
    except ValueError:
        logger.error("invalid_date_format", date=target_date_str)
        return

    logger.info("cli_scraper_started", market=market, collection_date=target_date.isoformat())

    # In this architecture, we use the DataPipeline to handle the full workflow
    pipeline = get_pipeline(market)
    try:
        await pipeline.run(target_date)
        logger.info("cli_scraper_completed", market=market)
    except Exception as error:
        logger.error("cli_scraper_failed", market=market, error=str(error))

def main() -> None:
    parser = argparse.ArgumentParser(description="Black-Scholes Market Data Scraper CLI")
    parser.add_argument("--market", choices=["spy", "nse", "both"], required=True, help="Market to scrape")
    parser.add_argument("--date", default=date.today().strftime("%Y-%m-%d"), help="Target date (YYYY-MM-DD)")

    args = parser.parse_args()

    if args.market == "both":
        async def run_both() -> None:
            await asyncio.gather(
                run_collection("spy", args.date),
                run_collection("nse", args.date)
            )
        asyncio.run(run_both())
    else:
        asyncio.run(run_collection(args.market, args.date))

if __name__ == "__main__":
    main()
