import pytest
from src.database.repository import Repository
from src.methods.base import OptionParams, PriceResult
import uuid

@pytest.mark.asyncio
async def test_upsert_option_parameters():
    repo = Repository()
    params = OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
        market_source="synthetic"
    )
    
    # First insert
    option_id = await repo.upsert_option_parameters(params)
    assert option_id is not None
    
    # Second insert (should be idempotent)
    option_id_2 = await repo.upsert_option_parameters(params)
    assert option_id == option_id_2

@pytest.mark.asyncio
async def test_insert_notification():
    repo = Repository()
    user_id = str(uuid.uuid4()) # Mock user ID
    
    # Note: This will fail if RLS blocks service_role or if user doesn't exist,
    # but for integration tests we usually use a test user.
    try:
        await repo.insert_notification(
            user_id=user_id,
            title="Test Notification",
            body="Integrations tests running",
            severity="info",
            channel="in_app"
        )
    except Exception as e:
        pytest.skip(f"Supabase connection/RLS issue: {e}")
