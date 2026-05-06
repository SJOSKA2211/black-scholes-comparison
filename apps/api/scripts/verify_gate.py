import os
import sys

sys.path.append(os.path.join(os.getcwd(), "apps/api"))

import numpy as np

from src.methods.analytical import BlackScholesAnalytical
from src.methods.base import OptionParams
from src.methods.finite_difference.crank_nicolson import CrankNicolsonFDM
from src.methods.finite_difference.explicit import ExplicitFDM
from src.methods.finite_difference.implicit import ImplicitFDM
from src.methods.monte_carlo.antithetic import AntitheticMC
from src.methods.monte_carlo.control_variates import ControlVariateMC
from src.methods.monte_carlo.quasi_mc import QuasiMC
from src.methods.monte_carlo.standard import StandardMC
from src.methods.tree_methods.binomial_crr import BinomialCRR
from src.methods.tree_methods.richardson import BinomialCRRRichardson, TrinomialRichardson
from src.methods.tree_methods.trinomial import TrinomialTree


def verify():
    np.random.seed(42)
    params = OptionParams(
        underlying_price=100.0,
        strike_price=100.0,
        maturity_years=1.0,
        volatility=0.2,
        risk_free_rate=0.05,
        option_type="call",
    )

    analytical = BlackScholesAnalytical().price(params)
    target = analytical.computed_price
    print(f"Analytical: {target:.4f}")

    methods = [
        ExplicitFDM(num_time_steps=20000, num_price_steps=200),
        ImplicitFDM(num_time_steps=500, num_price_steps=250),
        CrankNicolsonFDM(num_time_steps=500, num_price_steps=250),
        StandardMC(num_simulations=2000000),
        AntitheticMC(num_simulations=1000000),
        ControlVariateMC(num_simulations=500000, num_steps=200),
        QuasiMC(num_simulations=262144),
        BinomialCRR(num_steps=1000),
        TrinomialTree(num_steps=500),
        BinomialCRRRichardson(num_steps=500),
        TrinomialRichardson(num_steps=250),
    ]

    all_pass = True
    for m in methods:
        res = m.price(params)
        mape = abs(res.computed_price - target) / target
        passed = mape < 0.001
        print(
            f"{m.__class__.__name__}: {res.computed_price:.4f} (MAPE: {mape:.6f}) - {'PASS' if passed else 'FAIL'}"
        )
        if not passed:
            all_pass = False

    if all_pass:
        print("ALL METHODS PASSED ACCEPTANCE GATE")
    else:
        print("SOME METHODS FAILED ACCEPTANCE GATE")


if __name__ == "__main__":
    verify()
