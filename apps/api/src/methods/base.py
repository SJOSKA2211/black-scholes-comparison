"""Base classes for numerical option pricing methods."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MethodType(str, Enum):
    ANALYTICAL = "analytical"
    CRANK_NICOLSON = "crank_nicolson"
    QUASI_MC = "quasi_mc"
    BINOMIAL_CRR_RICHARDSON = "binomial_crr_richardson"


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


class OptionParams(BaseModel):
    """Standard parameters for Black-Scholes option pricing."""

    underlying_price: float = Field(..., gt=0, description="S")
    strike_price: float = Field(..., gt=0, description="K")
    maturity_years: float = Field(..., gt=0, description="T")
    volatility: float = Field(..., gt=0, description="sigma")
    risk_free_rate: float = Field(..., ge=0, description="r")
    option_type: OptionType
    is_american: bool = False


class PriceResult(BaseModel):
    """Result of an option pricing computation."""

    price: float
    exec_seconds: float
    converged: bool = True
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


class NumericalMethod(ABC):
    """Abstract base class for all pricing methods."""

    @abstractmethod
    async def price(self, params: OptionParams) -> PriceResult:
        """Compute the price of the option."""
        pass
