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
    health,
    pricing,
    websocket,
    experiments,
    market_data,
    scrapers,
    downloads,
    notifications,
)

# 1. Initialize logging
configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    settings = get_settings()
    logger.info("application_startup", environment=settings.environment)
    # Start RabbitMQ consumers in the background and store reference
    app.state.consumer_task = asyncio.create_task(start_consumers())
    yield
    logger.info("application_shutdown")
    app.state.consumer_task.cancel()
    try:
        await app.state.consumer_task
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

# 4. Routers
app.include_router(pricing.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(experiments.router, prefix="/api/v1")
app.include_router(market_data.router, prefix="/api/v1")
app.include_router(scrapers.router, prefix="/api/v1")
app.include_router(downloads.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(websocket.router)

# 5. Observability
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
