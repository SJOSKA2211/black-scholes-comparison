"""WebSocket channel definitions and permissions."""

from __future__ import annotations

ALLOWED_CHANNELS = frozenset(
    [
        "experiments",  # Real-time experiment results
        "scrapers",  # Scraper progress and logs
        "notifications",  # User-specific notifications
        "metrics",  # Live performance metrics
        "market_data",  # Live market data updates
    ]
)
