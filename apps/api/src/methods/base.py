"""Base interface for all Black-Scholes pricing methods."""
from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel, Field


class MethodType(str, Enum):
    """Supported numerical pricing methods."""
    ANALYTICAL = "analytical"
    CRANK_NICOLSON = "crank_nicolson"
    QUASI_MC = "quasi_mc"
    BINOMIAL_CRR_RICHARDSON = "binomial_crr_richardson"


class OptionParams(BaseModel):
    """
    Standardized parameters for option pricing.
    Uses descriptive names as per Section 17.4 of the mandate.
    """
    underlying_price: float = Field(..., gt=0)
    strike_price: float = Field(..., gt=0)
    maturity_years: float = Field(..., gt=0)
    volatility: float = Field(..., gt=0)
    risk_free_rate: float = Field(..., ge=0)
    option_type: str = Field("call")
    is_american: bool = Field(False)

    @property
    def is_call(self) -> bool:
        return self.option_type.lower() == "call"


class PriceResult(BaseModel):
    """Result container for pricing calculations."""
    method_type: str
    computed_price: float
    exec_seconds: float
    converged: bool = True
    delta: float | None = None
    gamma: float | None = None
    vega: float | None = None
    metadata: dict[str, float | str | int | bool] = Field(default_factory=dict)


class NumericalMethod(ABC):
    """Abstract base class for all pricing method implementations."""

    @abstractmethod
    def price(self, params: OptionParams) -> PriceResult:
        """Compute the option price given parameters."""
