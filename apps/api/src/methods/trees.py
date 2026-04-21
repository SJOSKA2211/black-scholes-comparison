import time

import numpy as np

from src.methods.base import OptionParams, PriceResult


class TreeMethods:
    """Binomial and Trinomial tree models for option pricing."""

    def binomial_crr(self, params: OptionParams, num_steps: int = 500) -> PriceResult:
        start_time = time.time()

        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        risk_free_rate = params.risk_free_rate
        volatility = params.volatility

        time_step = maturity_years / num_steps
        up_factor = np.exp(volatility * np.sqrt(time_step))
        down_factor = 1.0 / up_factor

        discount_factor = np.exp(-risk_free_rate * time_step)
        prob_up = (np.exp(risk_free_rate * time_step) - down_factor) / (
            up_factor - down_factor
        )
        prob_down = 1.0 - prob_up

        # Terminal price grid
        terminal_underlyings = (
            underlying_price
            * (up_factor ** np.arange(num_steps, -1, -1))
            * (down_factor ** np.arange(0, num_steps + 1))
        )

        if params.option_type == "call":
            values = np.maximum(terminal_underlyings - strike_price, 0)
        else:
            values = np.maximum(strike_price - terminal_underlyings, 0)

        # Backward induction
        for step_idx in range(num_steps - 1, -1, -1):
            values = discount_factor * (prob_up * values[:-1] + prob_down * values[1:])
            # Early exercise (American) check
            if params.is_american:
                underlyings_at_step = (
                    underlying_price
                    * (up_factor ** np.arange(step_idx, -1, -1))
                    * (down_factor ** np.arange(0, step_idx + 1))
                )
                if params.option_type == "call":
                    exercise_values = np.maximum(underlyings_at_step - strike_price, 0)
                else:
                    exercise_values = np.maximum(strike_price - underlyings_at_step, 0)
                values = np.maximum(values, exercise_values)

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="binomial_crr",
            computed_price=float(values[0]),
            exec_seconds=exec_seconds,
            parameter_set={"num_steps": num_steps},
        )

    def trinomial(self, params: OptionParams, num_steps: int = 500) -> PriceResult:
        start_time = time.time()

        underlying_price = params.underlying_price
        strike_price = params.strike_price
        maturity_years = params.maturity_years
        risk_free_rate = params.risk_free_rate
        volatility = params.volatility

        time_step = maturity_years / num_steps
        up_factor = np.exp(volatility * np.sqrt(2 * time_step))
        down_factor = 1.0 / up_factor  # noqa: F841
        mid_factor = 1.0  # noqa: F841

        discount_factor = np.exp(-risk_free_rate * time_step)

        # Boyle (1986) probabilities
        vol_sq = volatility**2
        term1 = (  # noqa: F841
            np.exp(risk_free_rate * time_step / 2)
            - np.exp(-volatility * np.sqrt(time_step / 2))
        ) / (
            np.exp(volatility * np.sqrt(time_step / 2))
            - np.exp(-volatility * np.sqrt(time_step / 2))
        )
        prob_up = (
            (
                np.exp(risk_free_rate * time_step / 2)
                - np.exp(-volatility * np.sqrt(time_step / 2))
            )
            / (
                np.exp(volatility * np.sqrt(time_step / 2))
                - np.exp(-volatility * np.sqrt(time_step / 2))
            )
        ) ** 2
        prob_down = (
            (
                np.exp(volatility * np.sqrt(time_step / 2))
                - np.exp(risk_free_rate * time_step / 2)
            )
            / (
                np.exp(volatility * np.sqrt(time_step / 2))
                - np.exp(-volatility * np.sqrt(time_step / 2))
            )
        ) ** 2
        prob_mid = 1.0 - prob_up - prob_down

        # Refined probabilities for stability
        m_val = np.exp(risk_free_rate * time_step)
        v_sq = m_val**2 * (np.exp(vol_sq * time_step) - 1)  # noqa: F841

        # Grid sizes
        num_nodes = 2 * num_steps + 1  # noqa: F841
        terminal_underlyings = underlying_price * (
            up_factor ** np.arange(num_steps, -num_steps - 1, -1)
        )

        if params.option_type == "call":
            values = np.maximum(terminal_underlyings - strike_price, 0)
        else:
            values = np.maximum(strike_price - terminal_underlyings, 0)

        for step_idx in range(num_steps - 1, -1, -1):
            values = discount_factor * (
                prob_up * values[:-2] + prob_mid * values[1:-1] + prob_down * values[2:]
            )
            if params.is_american:
                underlyings_at_step = underlying_price * (
                    up_factor ** np.arange(step_idx, -step_idx - 1, -1)
                )
                if params.option_type == "call":
                    exercise_values = np.maximum(underlyings_at_step - strike_price, 0)
                else:
                    exercise_values = np.maximum(strike_price - underlyings_at_step, 0)
                values = np.maximum(values, exercise_values)

        exec_seconds = time.time() - start_time
        return PriceResult(
            method_type="trinomial",
            computed_price=float(values[0]),
            exec_seconds=exec_seconds,
            parameter_set={"num_steps": num_steps},
        )

    def binomial_crr_richardson(
        self, params: OptionParams, num_steps: int = 500
    ) -> PriceResult:
        """CRR with Richardson extrapolation: 2*V(2N) - V(N)."""
        res_n = self.binomial_crr(params, num_steps)
        res_2n = self.binomial_crr(params, 2 * num_steps)

        richardson_price = 2 * res_2n.computed_price - res_n.computed_price
        return PriceResult(
            method_type="binomial_crr_richardson",
            computed_price=float(richardson_price),
            exec_seconds=res_n.exec_seconds + res_2n.exec_seconds,
            parameter_set={"num_steps_base": num_steps},
        )

    def trinomial_richardson(
        self, params: OptionParams, num_steps: int = 500
    ) -> PriceResult:
        res_n = self.trinomial(params, num_steps)
        res_2n = self.trinomial(params, 2 * num_steps)

        richardson_price = 2 * res_2n.computed_price - res_n.computed_price
        return PriceResult(
            method_type="trinomial_richardson",
            computed_price=float(richardson_price),
            exec_seconds=res_n.exec_seconds + res_2n.exec_seconds,
            parameter_set={"num_steps_base": num_steps},
        )
