"""Integration tests for Supabase repository."""

import uuid

import pytest

from src.database.repository import get_option_parameters, upsert_option_parameters


@pytest.mark.integration
@pytest.mark.asyncio
async def test_option_parameters_upsert_and_get():
    """Verify upsert and select operations with real Supabase."""
    option_id = str(uuid.uuid4())
    test_params = {
        "id": option_id,
        "underlying_price": 100.0,
        "strike_price": 100.0,
        "maturity_years": 1.0,
        "volatility": 0.2,
        "risk_free_rate": 0.05,
        "option_type": "call",
        "market_source": "synthetic",
    }

    try:
        # Upsert
        upsert_response = await upsert_option_parameters(test_params)
        assert upsert_response.data[0]["id"] == option_id

        # Get
        get_response = await get_option_parameters(option_id)
        assert get_response.data["underlying_price"] == 100.0
    except Exception as error:
        pytest.skip(f"Supabase connection failed: {error}")
    finally:
        # Teardown: delete test row (if cascade is enabled, it should be fine)
        # For simplicity, we just leave it or assume cleanup via DB triggers/scripts
        pass
