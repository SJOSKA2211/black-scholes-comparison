"""Custom exceptions for the Black-Scholes Research Platform."""


class BasePlatformError(Exception):
    """Base class for all platform exceptions."""

    pass


class PricingError(BasePlatformError):
    """Raised when a pricing calculation fails."""

    pass


class CFLViolationError(PricingError):
    """Raised when the CFL condition is violated in FDM."""

    pass


class ValidationError(BasePlatformError):
    """Raised when input validation fails."""

    pass


class InfrastructureError(BasePlatformError):
    """Base class for infrastructure-related errors."""

    pass


class RedisError(InfrastructureError):
    """Raised when Redis operations fail."""

    pass


class RabbitMQError(InfrastructureError):
    """Raised when RabbitMQ operations fail."""

    pass


class MinIOError(InfrastructureError):
    """Raised when MinIO operations fail."""

    pass


class SupabaseError(InfrastructureError):
    """Raised when Supabase operations fail."""

    pass


class ScraperError(BasePlatformError):
    """Raised when a scraper fails."""

    pass
