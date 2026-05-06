"""OAuth helpers for the platform."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

# Note: Supabase Auth handles the OAuth flow.
# This file can be used for any custom OAuth logic or post-login hooks.
