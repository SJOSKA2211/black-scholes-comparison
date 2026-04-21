class BlackScholesError(Exception):
    """Base exception for the Black-Scholes Research Platform."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class NumericalMethodError(BlackScholesError):
    """Raised when a numerical method fails to compute a valid price."""
    pass

class CFLViolationError(NumericalMethodError):
    """Raised when the CFL stability condition is violated in FDM."""
    def __init__(self, message: str, suggested_dt: float = None):
        details = {"suggested_dt": suggested_dt} if suggested_dt else {}
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
