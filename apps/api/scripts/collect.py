import asyncio
import argparse
import structlog
from datetime import datetime
from src.scrapers.spy_scraper import SPYScraper
from src.scrapers.nse_scraper import NSEScraper
from src.database import repository

logger = structlog.get_logger(__name__)

async def run_collection(market: str, collection_date: str):
    """
    CLI entry point for running a specific scraper.
    """
    logger.info("cli_scraper_started", market=market, collection_date=collection_date)
    
    # Create a record in scrape_runs
    run_id = await repository.create_scrape_run(market)
    
    try:
        if market == "spy":
            scraper = SPYScraper(run_id)
        elif market == "nse":
            scraper = NSEScraper(run_id)
        else:
            raise ValueError(f"Unknown market: {market}")
            
        await scraper.run()
        logger.info("cli_scraper_completed", market=market, run_id=run_id)
        
    except Exception as e:
        logger.error("cli_scraper_failed", market=market, error=str(e))
        await repository.update_scrape_run(run_id, {
            "status": "failed",
            "finished_at": datetime.utcnow().isoformat()
        })

def main():
    parser = argparse.ArgumentParser(description="Black-Scholes Market Data Scraper CLI")
    parser.add_argument("--market", choices=["spy", "nse"], required=True, help="Market to scrape")
    parser.add_argument("--date", default=datetime.today().strftime("%Y-%m-%d"), help="Target date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    asyncio.run(run_collection(args.market, args.date))

if __name__ == "__main__":
    main()
