"""WebSocket channel definitions and message routing."""

from enum import Enum


class ChannelName(str, Enum):
    EXPERIMENTS = "experiments"
    SCRAPERS = "scrapers"
    NOTIFICATIONS = "notifications"
    METRICS = "metrics"


ALLOWED_CHANNELS = frozenset([c.value for c in ChannelName])
