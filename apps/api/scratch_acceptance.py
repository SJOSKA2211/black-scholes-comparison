from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import OptionParams
import math

def test_acceptance():
    params = OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call"
    )
    result = BlackScholesAnalytical().price(params)
    print(f"Computed Price: {result.computed_price:.4f}")
    assert abs(result.computed_price - 10.4506) < 0.01
    print("Acceptance Gate: PASS")

if __name__ == "__main__":
    test_acceptance()
