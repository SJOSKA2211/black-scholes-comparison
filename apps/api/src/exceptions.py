"""Custom exceptions for the Black-Scholes Research Platform."""

from typing import Any


class BaseAppError(Exception):
    """Base class for all application-specific exceptions."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NumericalError(BaseAppError):
    """Raised when a numerical method fails to converge or produces invalid results."""


class CFLViolationError(NumericalError):
    """Raised when the Courant-Friedrichs-Lewy condition is violated in FDM."""


class InfrastructureError(BaseAppError):
    """Base class for infrastructure-related errors (DB, Redis, RabbitMQ, MinIO)."""


class DatabaseError(InfrastructureError):
    """Raised when a database operation fails."""


class CacheError(InfrastructureError):
    """Raised when a cache operation fails."""


class QueueError(InfrastructureError):
    """Raised when a message queue operation fails."""


class StorageError(InfrastructureError):
    """Raised when an object storage operation fails."""


class ValidationError(BaseAppError):
    """Raised when data validation fails."""


class AuthenticationError(BaseAppError):
    """Raised when authentication fails."""


class AuthorizationError(BaseAppError):
    """Raised when a user lacks permission for an action."""
