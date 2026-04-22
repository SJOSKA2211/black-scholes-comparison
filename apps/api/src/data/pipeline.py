"""Data pipeline — orchestrates scraping, transformation, validation, and storage."""
from __future__ import annotations
import asyncio
from datetime import date
from typing import Optional, List, Dict, Any
import structlog
import time
import pandas as pd
from src.scrapers.scraper_factory import ScraperFactory
from src.data.transformers import transform_batch_df
from src.data.validators import validate_quote
from src.database.repository import upsert_option_parameters, insert_market_data, create_scrape_run, update_scrape_run
from src.metrics import SCRAPE_RUNS_TOTAL, SCRAPE_ROWS_INSERTED, SCRAPE_DURATION_SECONDS

logger = structlog.get_logger(__name__)

class DataPipeline:
    """Orchestrates the end-to-end data flow."""

    def __init__(self, run_id: str, market: Optional[str] = None) -> None:
        self.run_id = run_id
        self.market = market

    async def run(self, trade_date: Optional[date] = None) -> Dict[str, int]:
        """Full run: Scrape -> Transform -> Validate -> Upsert."""
        if not self.market:
            raise ValueError("Market must be specified for a full run.")
            
        if trade_date is None:
            trade_date = date.today()

        start_time = time.time()
        scraper = ScraperFactory.get_scraper(self.market, self.run_id)
        
        SCRAPE_RUNS_TOTAL.labels(market=self.market, status="running").inc()
        
        try:
            logger.info("pipeline_scrape_started", market=self.market, run_id=self.run_id)
            raw_data = await scraper.scrape(trade_date)
            return await self.process_rows(raw_data, trade_date)
        except Exception as e:
            logger.error("pipeline_failed", market=self.market, run_id=self.run_id, error=str(e))
            SCRAPE_RUNS_TOTAL.labels(market=self.market, status="failed").inc()
            await update_scrape_run(self.run_id, {"status": "failed"})
            raise

    async def process_rows(self, rows: List[Dict[str, Any]], trade_date: Optional[date] = None) -> Dict[str, int]:
        """Processes a batch of raw rows."""
        if trade_date is None:
            trade_date = date.today()
            
        start_time = time.time()
        market = self.market or "unknown"
        
        logger.info("pipeline_processing_batch", run_id=self.run_id, count=len(rows))
        
        # Transform
        params_list = transform_batch_df(pd.DataFrame(rows), market_source=market) if rows else []
        
        inserted_count = 0
        market_data_to_insert = []
        
        for params in params_list:
            try:
                # Validate
                validate_quote(
                    params.underlying_price, 
                    params.strike_price, 
                    params.volatility, 
                    params.risk_free_rate, 
                    params.maturity_years
                )
                
                # Persistence
                option_id = await upsert_option_parameters(params.dict())
                
                market_data_to_insert.append({
                    "option_id": option_id,
                    "trade_date": trade_date.isoformat(),
                    "bid_price": 0.0,
                    "ask_price": 0.0,
                    "data_source": market
                })
                inserted_count += 1
            except Exception:
                continue

        if market_data_to_insert:
            await insert_market_data(market_data_to_insert)

        # Metrics
        duration = time.time() - start_time
        SCRAPE_DURATION_SECONDS.labels(market=market).observe(duration)
        SCRAPE_ROWS_INSERTED.labels(market=market).set(inserted_count)
        
        await update_scrape_run(
            self.run_id, 
            {
                "status": "success", 
                "rows_scraped": len(rows), 
                "rows_inserted": inserted_count
            }
        )
        
        return {"scraped": len(rows), "inserted": inserted_count}
