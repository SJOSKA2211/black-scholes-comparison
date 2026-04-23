from typing import Any


class BlackScholesError(Exception):
    """Base exception for the Black-Scholes Research Platform."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NumericalMethodError(BlackScholesError):
    """Raised when a numerical method fails to compute a valid price."""

    pass


class CFLViolationError(NumericalMethodError):
    """Raised when the CFL stability condition is violated in FDM."""

    def __init__(
        self,
        cfl_actual: float,
        cfl_bound: float = 0.5,
        suggested_dt: float | None = None,
    ) -> None:
        message = f"CFL stability condition failed: {cfl_actual:.4f} > {cfl_bound:.4f}"
        details = {
            "cfl_actual": cfl_actual,
            "cfl_bound": cfl_bound,
            "suggested_dt": suggested_dt,
        }
        super().__init__(message, details=details)


class RepositoryError(BlackScholesError):
    """Raised when a database operation fails."""

    pass


class ScraperError(BlackScholesError):
    """Raised when a market data scraper fails."""

    pass


class NotificationError(BlackScholesError):
    """Raised when sending a notification fails."""

    pass


class AuthenticationError(BlackScholesError):
    """Raised when JWT validation or OAuth flow fails."""

    pass
