import asyncio
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.logging_config import configure_logging
from src.routers import (
    pricing,
    experiments,
    market_data,
    scrapers,
    downloads,
    notifications,
    websocket,
    health,
)
from src.queue.consumer import start_consumers

logger = structlog.get_logger(__name__)
configure_logging()

app = FastAPI(
    title="Black-Scholes Research API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://black-scholes-comparison.vercel.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Prometheus instrumentation ───────────────────────────────────────────
Instrumentator(
    should_group_status_codes=True,
    excluded_handlers=["/health", "/metrics"],
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# ── Routers ──────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(pricing.router, prefix="/api/v1")
app.include_router(experiments.router, prefix="/api/v1")
app.include_router(market_data.router, prefix="/api/v1")
app.include_router(scrapers.router, prefix="/api/v1")
app.include_router(downloads.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(websocket.router) # No prefix for /ws

# ── Startup Tasks ────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks and clients."""
    logger.info("api_startup", status="initializing")
    # Start RabbitMQ consumers in the background
    asyncio.create_task(start_consumers())
    logger.info("api_startup", status="consumers_started")

@app.get("/")
async def root():
    return {"message": "Black-Scholes Research API v4 is running"}
