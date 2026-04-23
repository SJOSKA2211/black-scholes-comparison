from typing import Any, Literal, Protocol

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
    "analytical_asian",
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
    # Greeks (explicitly typed for production visibility)
    delta: float | None = None
    gamma: float | None = None
    theta: float | None = None
    vega: float | None = None
    rho: float | None = None


class MethodMetadata(BaseModel):
    name: str
    complexity: str
    type: str
    convergence_rate: str
    id: MethodType


class NumericalMethod(Protocol):
    """Protocol for all numerical pricing methods."""

    def price(self, params: OptionParams) -> PriceResult: ...
