import logging
import structlog
from datadog import initialize, statsd
from ddtrace import tracer
from typing import Any

def _add_datadog_trace_context(logger: Any, method: str, event_dict: dict) -> dict:
    """Inject active Datadog trace and span IDs into every log entry."""
    span = tracer.current_span()
    if span:
        event_dict["dd.trace_id"] = str(span.trace_id)
        event_dict["dd.span_id"] = str(span.span_id)
        event_dict["dd.service"] = "black-scholes-api"
        event_dict["dd.env"] = "production"
    return event_dict

def configure_logging() -> None:
    """Configure structlog with JSON renderer and Datadog log forwarding."""
    # Standard library logging configuration
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _add_datadog_trace_context,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Initialize Datadog statsd
    initialize(statsd_host="datadog-agent", statsd_port=8125)
