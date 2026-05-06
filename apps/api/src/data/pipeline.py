"""Data pipeline for orchestrating scrapers and validation."""
from __future__ import annotations
from datetime import date
from src.scrapers.base_scraper import BaseScraper
from src.scrapers.spy_scraper import SpyScraper
from src.scrapers.nse_next_scraper import NseScraper
from src.data.validators import validate_quote
from src.metrics import SCRAPE_ROWS_INSERTED
import structlog

logger = structlog.get_logger(__name__)

class PipelineResult:
    """Result of a pipeline run."""
    def __init__(self, market: str, rows_scraped: int, rows_validated: int) -> None:
        self.market = market
        self.rows_scraped = rows_scraped
        self.rows_validated = rows_validated

class DataPipeline:
    """Orchestrates scraping, validation, and storage."""
    
    def __init__(self, market: str) -> None:
        self.market = market
        self.scraper: BaseScraper
        if market == "spy":
            self.scraper = SpyScraper()
        else:
            self.scraper = NseScraper()

    async def run(self, trade_date: date) -> PipelineResult:
        """Run the pipeline for a given date."""
        logger.info("pipeline_started", market=self.market, date=trade_date.isoformat())
        
        scraper_result = await self.scraper.run(trade_date)
        rows_scraped = len(scraper_result.quotes)
        
        validated_quotes = [q for q in scraper_result.quotes if validate_quote(q)]
        rows_validated = len(validated_quotes)
        
        SCRAPE_ROWS_INSERTED.labels(market=self.market).set(float(rows_validated))
        
        logger.info("pipeline_finished", 
                    market=self.market, 
                    scraped=rows_scraped, 
                    validated=rows_validated)
        
        return PipelineResult(self.market, rows_scraped, rows_validated)

def get_pipeline(market: str) -> DataPipeline:
    """Factory function for pipelines."""
    return DataPipeline(market)
