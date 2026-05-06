"""Main FastAPI application entry point."""

import asyncio

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.logging_config import setup_logging
from src.queue.consumer import start_consumers
from src.routers import pricing, websocket

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()

    app = FastAPI(
        title="Black-Scholes Research Platform API",
        version="1.0.0",
        description="Full-stack research system for option pricing numerical methods.",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to Vercel domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(pricing.router, prefix="/api/v1")
    app.include_router(websocket.router)

    # Store background tasks to avoid garbage collection
    background_tasks = set()

    @app.on_event("startup")
    async def startup_event() -> None:
        """Lifecycle hook: run on application start."""
        logger.info("application_startup")
        # Start background consumers
        task = asyncio.create_task(start_consumers())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Basic health check endpoint."""
        return {"status": "ok", "db": "connected"}  # DB check logic can be added

    # Prometheus Instrumentation
    Instrumentator().instrument(app).expose(app)

    return app


app = create_app()
