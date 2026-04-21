from typing import Any, Literal

from pydantic import BaseModel, Field

MethodType = Literal[
    "analytical",
    "explicit_fdm",
    "implicit_fdm",
    "crank_nicolson",
    "standard_mc",
    "antithetic_mc",
    "control_variate_mc",
    "quasi_mc",
    "binomial_crr",
    "trinomial",
    "binomial_crr_richardson",
    "trinomial_richardson",
]

OptionType = Literal["call", "put"]
MarketSource = Literal["synthetic", "spy", "nse"]


class OptionParams(BaseModel):
    underlying_price: float = Field(gt=0)
    strike_price: float = Field(gt=0)
    maturity_years: float = Field(gt=0)
    volatility: float = Field(gt=0)
    risk_free_rate: float = Field(ge=0)
    option_type: OptionType
    is_american: bool = False
    market_source: MarketSource = "synthetic"


class PriceResult(BaseModel):
    method_type: MethodType
    computed_price: float
    exec_seconds: float
    converged: bool = True
    replications: int = 1
    parameter_set: dict[str, Any] = Field(default_factory=dict)
    confidence_interval: tuple[float, float] | None = None
