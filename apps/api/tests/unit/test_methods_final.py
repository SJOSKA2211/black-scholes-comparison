import pytest
from src.methods.base import OptionParams
from src.methods.tree_methods.binomial_crr import price_binomial_crr
from src.methods.tree_methods.trinomial import price_trinomial

@pytest.fixture
def base_params():
    return OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
        is_american=False
    )

@pytest.mark.unit
def test_binomial_american_put_coverage(base_params):
    base_params.is_american = True
    base_params.option_type = "put"
    res = price_binomial_crr(base_params, num_steps=10)
    assert res.computed_price > 0

@pytest.mark.unit
def test_trinomial_american_call_coverage(base_params):
    base_params.is_american = True
    base_params.option_type = "call"
    res = price_trinomial(base_params, num_steps=10)
    assert res.computed_price > 0
