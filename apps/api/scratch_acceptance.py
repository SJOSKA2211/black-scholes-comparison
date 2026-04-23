import os
import sys

# Add apps/api to path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "apps/api")))

from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import OptionParams
from src.methods.tree_methods.binomial_crr import BinomialCRR


def verify_mape() -> None:
    params = OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call"
    )

    analytical = BlackScholesAnalytical()
    ref_price = analytical.price(params).computed_price

    tree = BinomialCRR()
    # High resolution
    tree_price = tree.price(params, num_steps=2000).computed_price

    mape = abs(tree_price - ref_price) / ref_price * 100
    print(f"Ref: {ref_price:.6f}, Tree: {tree_price:.6f}, MAPE: {mape:.6f}%")
    assert mape < 0.1

if __name__ == "__main__":
    verify_mape()
