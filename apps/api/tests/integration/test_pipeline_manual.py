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
from src.database.repository import upsert_option_parameters, upsert_market_data
from src.data.transformers import transform_to_db_params, transform_to_db_market_data

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pipeline_step_by_step() -> None:
    """
    Test pipeline steps manually to see where it fails.
    """
    unique_price = 7777.0 + (float(uuid.uuid4().int % 100) / 100.0)
    trade_date = date.today()
    
    quote = RawQuote(
        underlying_symbol="TEST_MANUAL",
        strike_price=unique_price,
        maturity_date=date(2026, 12, 31),
        option_type="call",
        bid_price=10.0,
        ask_price=11.0,
        underlying_price=unique_price,
        data_source="spy"
    )
    
    # 1. Transform
    param_dict = transform_to_db_params(quote, trade_date)
    print(f"DEBUG: Params to upsert: {param_dict}")
    
    # 2. Upsert Option
    try:
        opt_resp = await upsert_option_parameters(param_dict)
        print(f"DEBUG: Opt Resp Data: {opt_resp.data}")
        assert len(opt_resp.data) > 0, "Upsert returned no data"
        option_id = opt_resp.data[0]["id"]
    except Exception as e:
        pytest.fail(f"Upsert option failed: {e}")
        
    # 3. Upsert Market Data
    try:
        market_dict = transform_to_db_market_data(quote, option_id, trade_date)
        print(f"DEBUG: Market Dict: {market_dict}")
        market_resp = await upsert_market_data([market_dict])
        print(f"DEBUG: Market Resp Data: {market_resp.data}")
        assert len(market_resp.data) > 0, "Market data upsert returned no data"
    except Exception as e:
        pytest.fail(f"Upsert market data failed: {e}")
        
    # 4. Verification
    client = get_supabase()
    db_opt = client.table("option_parameters").select("*").eq("id", option_id).execute()
    assert len(db_opt.data) == 1, "Could not find option by ID after insert"
    
    # 5. Cleanup (manual cascade)
    try:
        client.table("market_data").delete().eq("option_id", option_id).execute()
        client.table("option_parameters").delete().eq("id", option_id).execute()
    except Exception as e:
        print(f"Cleanup error (ignored): {e}")
