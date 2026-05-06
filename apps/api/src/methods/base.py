"""Base class for all Black-Scholes numerical methods."""
from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import time
from src.metrics import PRICE_COMPUTATIONS_TOTAL, PRICE_DURATION_SECONDS
import structlog

logger = structlog.get_logger(__name__)

class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"

class OptionParameters(BaseModel):
    """Input parameters for option pricing."""
    underlying_price: float = Field(..., gt=0)
    strike_price: float = Field(..., gt=0)
    maturity_years: float = Field(..., gt=0)
    volatility: float = Field(..., gt=0)
    risk_free_rate: float = Field(..., ge=0)
    option_type: OptionType
    is_american: bool = False

    @field_validator("volatility")
    @classmethod
    def validate_volatility(cls, value: float) -> float:
        """Ensure volatility is within reasonable bounds."""
        if value > 5.0:  # 500% vol limit
            raise ValueError("Volatility too high")
        return value

class PricingResult(BaseModel):
    """Output result from a pricing method."""
    computed_price: float
    exec_seconds: float
    converged: bool = True
    method_type: str
    parameter_set: dict[str, Any]
    replications: int | None = None

class BasePricingMethod(ABC):
    """Abstract base class for pricing methods."""
    
    def __init__(self, method_name: str) -> None:
        self.method_name = method_name

    @abstractmethod
    def _compute(self, params: OptionParameters) -> float:
        """Internal computation logic."""
        pass

    def price(self, params: OptionParameters) -> PricingResult:
        """Execute pricing and record metrics."""
        start_time = time.perf_counter()
        
        try:
            computed_value = self._compute(params)
            duration = time.perf_counter() - start_time
            
            PRICE_COMPUTATIONS_TOTAL.labels(
                method_type=self.method_name,
                option_type=params.option_type.value,
                converged="true"
            ).inc()
            
            PRICE_DURATION_SECONDS.labels(
                method_type=self.method_name
            ).observe(duration)
            
            return PricingResult(
                computed_price=computed_value,
                exec_seconds=duration,
                method_type=self.method_name,
                parameter_set=params.model_dump()
            )
        except Exception as error:
            duration = time.perf_counter() - start_time
            PRICE_COMPUTATIONS_TOTAL.labels(
                method_type=self.method_name,
                option_type=params.option_type.value,
                converged="false"
            ).inc()
            logger.error("pricing_failed", method=self.method_name, error=str(error))
            raise

OptionParameters.model_rebuild()
PricingResult.model_rebuild()
