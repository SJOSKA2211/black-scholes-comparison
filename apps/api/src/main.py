from ddtrace import patch_all; patch_all()   # Must be FIRST import for APM
 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from src.logging_config import configure_logging
from src.routers import pricing, experiments, market_data, scrapers, downloads, notifications, health
 
configure_logging()   # structlog JSON + Datadog log handler
 
app = FastAPI(
    title="Black-Scholes Research API",
    version="1.0.0",
    description="Numerical methods for option pricing — MATH499",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
 
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://black-scholes-comparison.vercel.app",
                   "http://localhost:3000"],   # local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
app.include_router(health.router, tags=["health"])
app.include_router(pricing.router, prefix="/api/v1", tags=["pricing"])
app.include_router(experiments.router, prefix="/api/v1", tags=["experiments"])
app.include_router(market_data.router, prefix="/api/v1", tags=["market-data"])
app.include_router(scrapers.router, prefix="/api/v1", tags=["scrapers"])
app.include_router(downloads.router, prefix="/api/v1", tags=["downloads"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])

@app.get("/")
async def root():
    return {"message": "Black-Scholes Research API is running"}
