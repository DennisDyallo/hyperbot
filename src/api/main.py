"""
FastAPI application for Hyperbot.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.routes import (
    account_router,
    leverage_router,
    market_data_router,
    orders_router,
    positions_router,
    rebalance_router,
    scale_orders_router,
    web_router,
)
from src.config import logger, settings
from src.services import hyperliquid_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting Hyperbot API...")
    try:
        hyperliquid_service.initialize()
        logger.info("Hyperliquid service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Hyperliquid service: {e}")
        logger.warning("API will start but Hyperliquid features may not work")

    yield

    # Shutdown
    logger.info("Shutting down Hyperbot API...")


app = FastAPI(
    title="Hyperbot API",
    description="Trading bot API for Hyperliquid",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# Register routers
app.include_router(web_router)  # Web UI routes (no prefix, takes priority)
app.include_router(account_router)
app.include_router(positions_router)
app.include_router(orders_router)
app.include_router(market_data_router)
app.include_router(rebalance_router)
app.include_router(scale_orders_router)
app.include_router(leverage_router)


@app.get("/api/health")
async def health():
    """
    Health check endpoint.
    Returns overall API health and Hyperliquid service status.
    """
    health_data = {
        "api": "healthy",
        "environment": settings.ENVIRONMENT,
    }

    # Check Hyperliquid service
    try:
        hl_health = hyperliquid_service.health_check()
        health_data["hyperliquid"] = hl_health
    except Exception as e:
        logger.error(f"Hyperliquid health check failed: {e}")
        health_data["hyperliquid"] = {"status": "error", "message": str(e)}

    # Determine overall status
    hl_status = health_data.get("hyperliquid", {}).get("status", "error")
    if hl_status == "unhealthy" or hl_status == "error":
        health_data["api"] = "degraded"

    return health_data
