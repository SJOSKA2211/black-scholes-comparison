"""Notification hierarchy and delivery orchestration."""
from __future__ import annotations
import json
from typing import Dict, Any, Optional
import structlog
from src.database.repository import insert_notification
from src.metrics import NOTIFICATIONS_SENT_TOTAL
from src.cache.redis_client import get_redis

logger = structlog.get_logger(__name__)

async def notify_user(
    user_id: str,
    title: str,
    body: str,
    severity: str = "info",
    action_url: Optional[str] = None
) -> None:
    """
    Orchestrates notification delivery across multiple tiers.
    1. Persistent DB row (In-app)
    2. WebSocket push (Real-time)
    3. Email (Transactional - if severe)
    """
    try:
        # 1. In-app notification (DB)
        await insert_notification({
            "user_id": user_id,
            "title": title,
            "body": body,
            "severity": severity,
            "action_url": action_url
        })
        
        # 2. WebSocket Push (Pub/Sub)
        redis = get_redis()
        await redis.publish("ws:notifications", json.dumps({
            "user_id": user_id,
            "title": title,
            "body": body,
            "severity": severity
        }))
        
        NOTIFICATIONS_SENT_TOTAL.labels(channel="in_app", severity=severity).inc()
        logger.info("notification_dispatched", user_id=user_id, severity=severity)
        
    except Exception as e:
        logger.error("notification_dispatch_failed", error=str(e), user_id=user_id)
