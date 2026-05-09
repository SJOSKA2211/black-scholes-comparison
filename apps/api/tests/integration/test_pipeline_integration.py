"""Integration tests for data pipeline with real infrastructure."""
from __future__ import annotations
import uuid
import asyncio
from datetime import date
from unittest.mock import AsyncMock
import pytest
from src.data.pipeline import DataPipeline
from src.scrapers.base_scraper import RawQuote, ScraperResult
from src.database.supabase_client import get_supabase

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_persistence_real_supabase() -> None:
    """
    Test pipeline execution and persistence in real Supabase.
    """
    mock_scraper = AsyncMock()
    # Use a price that won't have precision issues
    unique_price = 9999.0 + (float(uuid.uuid4().int % 100) / 100.0)
    
    mock_quote = RawQuote(
        underlying_symbol="TEST_PIPELINE",
        strike_price=unique_price,
        maturity_date=date(2026, 12, 31),
        option_type="call",
        bid_price=10.0,
        ask_price=11.0,
        underlying_price=unique_price,
        data_source="spy"
    )
    
    mock_scraper.run.return_value = ScraperResult(
        quotes=[mock_quote],
        execution_seconds=0.1,
        market="spy",
        status="success"
    )
    
    pipeline = DataPipeline("spy", mock_scraper)
    trade_date = date.today()
    result = await pipeline.run(trade_date)
    
    assert result.status == "success", f"Pipeline failed: {result}"
    assert result.rows_inserted == 1
    
    client = get_supabase()
    # Use a wider query first
    db_all = client.table("option_parameters").select("*").order("created_at", desc=True).limit(5).execute()
    print(f"Recent options: {db_all.data}")
    
    db_opt = client.table("option_parameters").select("*").eq("underlying_price", unique_price).execute()
    assert len(db_opt.data) >= 1, f"Option not found for price {unique_price}. Recent: {db_all.data}"
    option_id = db_opt.data[0]["id"]
    
    client.table("market_data").delete().eq("option_id", option_id).execute()
    client.table("option_parameters").delete().eq("id", option_id).execute()
