"""Main FastAPI Application Entrypoint."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.config import get_settings
from src.logging_config import configure_logging
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
from src.task_queues.consumer import start_consumers

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
    if settings.redis_enabled:
        get_redis()
    else:
        logger.info("redis_init_skipped", step="init")

    if settings.minio_enabled:
        get_minio()
    else:
        logger.info("minio_init_skipped", step="init")

    # 2. Start RabbitMQ consumers (Section 8.4)
    # Background workers consume tasks from bs.scrape and bs.experiment
    if settings.rabbitmq_enabled:
        try:
            import asyncio
            # Wait at most 5 seconds for consumers to start
            await asyncio.wait_for(start_consumers(), timeout=5.0)
            logger.info("consumers_started", step="init")
        except TimeoutError:
            logger.warning("consumers_start_timeout", step="init")
        except Exception as error:
            logger.error("consumers_start_failed", error=str(error), step="init")
    else:
        logger.info("consumers_skipped", reason="explicitly disabled or host set to none", step="init")

    logger.info("app_ready", step="init")

    yield

    # Shutdown logic
    logger.info("app_shutting_down", step="shutdown")
    # Add any cleanup logic here (e.g. closing DB connections if managed locally)


def create_app() -> FastAPI:
    """Initialize and configure the FastAPI application."""
    configure_logging()
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

    # MinIO Proxy (Replaces Nginx /minio/ for platforms like Railway)
    @app.api_route("/minio/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def minio_proxy(path: str, request: Request) -> Response:
        """Proxies requests to the internal MinIO endpoint."""
        import httpx

        settings = get_settings()
        target_url = f"http://{settings.minio_endpoint}/{path}"
        
        # Use a long timeout for file uploads/downloads
        async with httpx.AsyncClient(timeout=120.0) as client:
            # Prepare headers (strip host)
            headers = dict(request.headers)
            headers.pop("host", None)
            
            # Proxy request
            proxy_res = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=await request.body()
            )
            
            return Response(
                content=proxy_res.content,
                status_code=proxy_res.status_code,
                headers=dict(proxy_res.headers)
            )

    return app


app = create_app()
