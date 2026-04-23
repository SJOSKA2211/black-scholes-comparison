import pandas as pd
import pytest

from src.data.transformers import transform_batch_df, transform_market_row
from src.methods.base import OptionParams


@pytest.mark.unit
class TestTransformers:
    def test_transform_market_row_success(self) -> None:
        row = {
            "underlying_price": "100.0",
            "strike_price": 100,
            "maturity_years": 1.0,
            "volatility": 0.2,
            "risk_free_rate": 0.05,
            "option_type": "call",
            "is_american": True,
        }
        params = transform_market_row(row, market_source="spy")
        assert isinstance(params, OptionParams)
        assert params.underlying_price == 100.0
        assert params.is_american is True
        assert params.market_source == "spy"

    def test_transform_market_row_failure(self) -> None:
        # Missing key
        with pytest.raises(KeyError):
            transform_market_row({"underlying_price": 100})
        # Invalid value type
        with pytest.raises(ValueError):
            transform_market_row(
                {
                    "underlying_price": "invalid",
                    "strike_price": 100,
                    "maturity_years": 1,
                    "volatility": 0.2,
                    "risk_free_rate": 0.05,
                    "option_type": "call",
                }
            )

    def test_transform_batch_df_success(self) -> None:
        data = [
            {
                "underlying_price": 100,
                "strike_price": 100,
                "maturity_years": 1,
                "volatility": 0.2,
                "risk_free_rate": 0.05,
                "option_type": "call",
            },
            {
                "underlying_price": 110,
                "strike_price": 100,
                "maturity_years": 1,
                "volatility": 0.2,
                "risk_free_rate": 0.05,
                "option_type": "put",
            },
        ]
        df = pd.DataFrame(data)
        results = transform_batch_df(df)
        assert len(results) == 2
        assert results[0].underlying_price == 100.0
        assert results[1].option_type == "put"

    def test_transform_batch_df_partial_failure(self) -> None:
        data = [
            {
                "underlying_price": 100,
                "strike_price": 100,
                "maturity_years": 1,
                "volatility": 0.2,
                "risk_free_rate": 0.05,
                "option_type": "call",
            },
            {"invalid": "row"},
        ]
        df = pd.DataFrame(data)
        results = transform_batch_df(df)
        assert len(results) == 1
        assert results[0].underlying_price == 100.0
