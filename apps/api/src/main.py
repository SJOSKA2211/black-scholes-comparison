"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

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
from src.storage.minio_client import get_minio

logger = structlog.get_logger(__name__)

# Global set to store references to long-running tasks to prevent garbage collection
background_tasks: set[asyncio.Task[Any]] = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes infrastructure and background workers."""
    logger.info("api_starting_up")
    try:
        get_minio()
    except Exception as e:
        logger.error("minio_init_failed_in_lifespan", error=str(e))
    
    task = asyncio.create_task(start_consumers())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    logger.info("api_startup_completed")
    yield
    logger.info("api_shutting_down")

app = FastAPI(
    title="Black-Scholes Research API v4",
    description="Full-stack research platform for numerical methods in finance.",
    version="4.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Instrumentation
Instrumentator().instrument(app).expose(app)

# Register Routers (Mandate Aligned)
app.include_router(pricing.router, prefix="/api/v1", tags=["Pricing"])
app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["Experiments"])
app.include_router(market_data.router, prefix="/api/v1/market-data", tags=["Market Data"])
app.include_router(scrapers.router, prefix="/api/v1/scrapers", tags=["Scrapers"])
app.include_router(downloads.router, prefix="/api/v1/download", tags=["Downloads"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(websocket.router, tags=["WebSocket"])
app.include_router(health.router, tags=["Health"])

@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Black-Scholes Research API v4 is active", "version": "4.0.0"}
