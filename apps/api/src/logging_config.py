"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Any

import structlog


def setup_logging() -> None:
    """Configure structlog for structured JSON logging in production and pretty logging in dev."""

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if sys.stderr.isatty():
        # Pretty printing for interactive terminals
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        # JSON logging for production (Docker/Cloud)
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Bridge standard logging to structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
