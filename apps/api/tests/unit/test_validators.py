import pytest
from pydantic import ValidationError as PydanticValidationError
from src.data.validators import (
    ValidationError,
    validate_maturity,
    validate_quote,
    validate_risk_free_rate,
    validate_strike_price,
    validate_underlying_price,
    validate_volatility,
    OptionParamsInput,
    MarketDataInput,
    ScraperRunInput,
    ScraperRunUpdate,
    AuditLogInput,
    NotificationInput,
    ValidationMetricsInput
)
import uuid

@pytest.mark.unit
class TestNumericValidators:
    def test_success(self):
        assert validate_underlying_price(100.0) == 100.0
        assert validate_strike_price(100.0) == 100.0
        assert validate_maturity(1.0) == 1.0
        assert validate_volatility(0.2) == 0.2
        assert validate_risk_free_rate(0.05) == 0.05

    def test_failure(self):
        with pytest.raises(ValidationError): validate_underlying_price(0)
        with pytest.raises(ValidationError): validate_strike_price(-1)
        with pytest.raises(ValidationError): validate_maturity(0)
        with pytest.raises(ValidationError): validate_volatility(-0.1)
        with pytest.raises(ValidationError): validate_risk_free_rate(-0.01)

@pytest.mark.unit
class TestQuoteValidator:
    def test_success(self):
        quote = {"bid": 10.0, "ask": 11.0, "underlying": 100.0}
        assert validate_quote(quote) == quote

    def test_missing_keys(self):
        with pytest.raises(ValidationError, match="Missing required key"):
            validate_quote({"bid": 10.0})

    def test_invalid_values(self):
        with pytest.raises(ValidationError, match="Bid price cannot be negative"):
            validate_quote({"bid": -1.0, "ask": 10.0, "underlying": 100.0})
        with pytest.raises(ValidationError, match="Ask price must be positive"):
            validate_quote({"bid": 5.0, "ask": 0.0, "underlying": 100.0})
        with pytest.raises(ValidationError, match="Bid cannot be greater than ask"):
            validate_quote({"bid": 12.0, "ask": 11.0, "underlying": 100.0})
        with pytest.raises(ValidationError, match="Underlying price must be positive"):
            validate_quote({"bid": 10.0, "ask": 11.0, "underlying": 0.0})

@pytest.mark.unit
class TestInputModels:
    def test_option_params_input(self):
        data = {
            "underlying_price": 100, "strike_price": 100, "maturity_years": 1,
            "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call",
            "market_source": "spy"
        }
        assert OptionParamsInput(**data).underlying_price == 100.0
        with pytest.raises(PydanticValidationError):
            OptionParamsInput(**{**data, "underlying_price": 0})

    def test_market_data_input(self):
        data = {
            "option_id": uuid.uuid4(), "trade_date": "2024-01-01",
            "bid_price": 10, "ask_price": 11, "data_source": "spy"
        }
        assert MarketDataInput(**data).bid_price == 10.0

    def test_scraper_run_input(self):
        data = {"market": "spy", "scraper_class": "SpyScraper"}
        assert ScraperRunInput(**data).status == "running"

    def test_scraper_run_update(self):
        data = {"status": "success", "rows_scraped": 100}
        assert ScraperRunUpdate(**data).rows_scraped == 100

    def test_audit_log_input(self):
        data = {"pipeline_run_id": uuid.uuid4(), "step_name": "S", "status": "ok"}
        assert AuditLogInput(**data).step_name == "S"

    def test_notification_input(self):
        data = {"user_id": uuid.uuid4(), "title": "T", "body": "B"}
        assert NotificationInput(**data).title == "T"

    def test_validation_metrics_input(self):
        data = {
            "option_id": uuid.uuid4(), "method_result_id": uuid.uuid4(),
            "absolute_error": 1.0, "relative_pct_error": 0.1, "mape": 0.1, "market_deviation": 0.05
        }
        assert ValidationMetricsInput(**data).absolute_error == 1.0

@pytest.mark.unit
class TestTransformers:
    def test_transform_market_row(self):
        from src.data.transformers import transform_market_row
        row = {
            "underlying_price": "100", "strike_price": "100", "maturity_years": "1",
            "volatility": "0.2", "risk_free_rate": "0.05", "option_type": "call"
        }
        params = transform_market_row(row)
        assert params.underlying_price == 100.0
        with pytest.raises(KeyError):
            transform_market_row({"invalid": 1})

    def test_transform_batch_df(self):
        from src.data.transformers import transform_batch_df
        import pandas as pd
        df = pd.DataFrame([
            {"underlying_price": 100, "strike_price": 100, "maturity_years": 1, "volatility": 0.2, "risk_free_rate": 0.05, "option_type": "call"},
            {"invalid": "row"}
        ])
        res = transform_batch_df(df)
        assert len(res) == 1

@pytest.mark.unit
class TestAuth:
    @pytest.mark.asyncio
    async def test_get_current_user(self):
        from src.auth.dependencies import get_current_user
        user = await get_current_user()
        assert user["role"] == "researcher"

    @pytest.mark.asyncio
    async def test_verify_ws_token(self):
        from unittest.mock import MagicMock
        from src.auth.dependencies import verify_ws_token
        res = await verify_ws_token(MagicMock(), "token")
        assert res["email"] == "researcher@example.com"

@pytest.mark.unit
class TestConfig:
    def test_settings_overrides(self):
        from src.config import Settings
        s = Settings(RABBITMQ_URL="amqp://custom")
        assert s.rabbitmq_url == "amqp://custom"
        s2 = Settings(RABBITMQ_URL=None)
        assert "amqp://" in s2.rabbitmq_url
