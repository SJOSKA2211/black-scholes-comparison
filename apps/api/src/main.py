"""Main FastAPI application entry point."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import get_settings
from src.logging_config import configure_logging
from src.queue.consumer import start_consumers
from src.routers import (
    downloads,
    experiments,
    health,
    market_data,
    notifications,
    pricing,
    scrapers,
    websocket,
)
from src.websocket.manager import ws_manager

# 1. Initialize logging
configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    settings = get_settings()
    logger.info("application_startup", environment=settings.environment)

    # 1. Start RabbitMQ consumers
    app.state.consumer_task = asyncio.create_task(start_consumers())

    # 2. Start global WebSocket manager consumer
    app.state.ws_task = asyncio.create_task(ws_manager.start_consumer())

    yield

    logger.info("application_shutdown")

    # Cancel background tasks
    app.state.consumer_task.cancel()
    app.state.ws_task.cancel()

    try:
        await asyncio.gather(app.state.consumer_task, app.state.ws_task, return_exceptions=True)
    except asyncio.CancelledError:
        pass


# 2. Create app instance
app = FastAPI(
    title="Black-Scholes Research Platform",
    description="Full-stack option pricing and research system.",
    version="1.0.0",
    lifespan=lifespan,
)

# 3. Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.get("/")
async def root():
    """Project metadata and status."""
    return {
        "message": "Black-Scholes Research API",
        "version": "1.0.0",
        "methods_supported": 12,
        "infrastructure": "Supabase, Redis, RabbitMQ, MinIO",
    }


# 4. Routers
app.include_router(pricing.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(experiments.router, prefix="/api/v1")
app.include_router(market_data.router, prefix="/api/v1")
app.include_router(scrapers.router, prefix="/api/v1")
app.include_router(downloads.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")

# 5. Observability
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
