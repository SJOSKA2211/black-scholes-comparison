"""Main FastAPI Application Entrypoint."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import get_settings
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

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handle application startup and shutdown events.
    Boot background workers and initialize infrastructure clients.
    """
    settings = get_settings()
    logger.info("app_starting", env=settings.env, step="init")

    # 1. Initialize infrastructure singletons
    from src.cache.redis_client import get_redis
    from src.storage.minio_client import get_minio

    # Eager initialization
    get_redis()
    get_minio()

    # 2. Start RabbitMQ consumers (Section 8.4)
    # Background workers consume tasks from bs.scrape and bs.experiment
    try:
        await start_consumers()
        logger.info("consumers_started", step="init")
    except Exception as error:
        logger.error("consumers_start_failed", error=str(error), step="init")

    logger.info("app_ready", step="init")

    yield

    # Shutdown logic
    logger.info("app_shutting_down", step="shutdown")
    # Add any cleanup logic here (e.g. closing DB connections if managed locally)


def create_app() -> FastAPI:
    """Initialize and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Black-Scholes Research Platform",
        version="4.0.0",
        description="Production-grade full-stack options pricing research system.",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Prometheus Instrumentation (Section 12.1)
    # Exposes /metrics for Prometheus scraping
    Instrumentator().instrument(app).expose(app)

    # Include routers (Section 17.2)
    # Health check is exposed at /health for infrastructure probes
    app.include_router(health.router)

    # API v1 routes
    api_v1_prefix = "/api/v1"
    app.include_router(market_data.router, prefix=api_v1_prefix)
    app.include_router(pricing.router, prefix=api_v1_prefix)
    app.include_router(experiments.router, prefix=api_v1_prefix)
    app.include_router(scrapers.router, prefix=api_v1_prefix)
    app.include_router(downloads.router, prefix=api_v1_prefix)
    app.include_router(notifications.router, prefix=api_v1_prefix)
    app.include_router(websocket.router, prefix=api_v1_prefix)

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint with project identification."""
        return {"message": "Black-Scholes Research API v4. Production Stable."}

    return app


app = create_app()
