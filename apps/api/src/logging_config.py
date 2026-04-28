import logging
import os
import structlog


def configure_logging() -> None:
    """Configure structlog with JSON renderer for structured logging."""
    # Standard library logging configuration
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # In production/cloud (Railway, Render, etc), use JSON for machine readability
    # Locally or if not specified, use a more human-friendly format if possible
    # but the mandate usually implies machine readable logs for production.
    if os.getenv("ENVIRONMENT") == "production" or os.getenv("RAILWAY_STATIC_URL"):
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Default to JSON for consistency in this project, but we can switch to ConsoleRenderer
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
