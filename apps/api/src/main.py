"""Main FastAPI application entry point."""
from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from src.routers import (
    pricing, 
    health, 
    websocket, 
    downloads, 
    experiments, 
    market_data, 
    scrapers, 
    notifications
)
from src.queue.consumer import start_consumers
from src.logging_config import setup_logging
import structlog

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifecycle hooks for the FastAPI application."""
    setup_logging()
    logger.info("app_startup", step="init")
    
    # Start background task consumers
    try:
        await start_consumers()
    except Exception as error:
        logger.error("consumers_startup_failed", error=str(error))
        
    yield
    
    logger.info("app_shutdown", step="shutdown")

app = FastAPI(
    title="Black-Scholes Research Platform API",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument Prometheus
Instrumentator().instrument(app).expose(app)

# Register Routers
app.include_router(pricing.router)
app.include_router(health.router)
app.include_router(websocket.router)
app.include_router(downloads.router)
app.include_router(experiments.router)
app.include_router(market_data.router)
app.include_router(scrapers.router)
app.include_router(notifications.router)

@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning API metadata."""
    return {
        "name": "Black-Scholes Research Platform API",
        "version": "1.0.0",
        "status": "running"
    }
