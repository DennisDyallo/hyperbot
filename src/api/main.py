"""
FastAPI application for Hyperbot.
"""

import asyncio
from contextlib import asynccontextmanager, suppress

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

# Global bot application instance
_bot_app = None
_bot_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    global _bot_app, _bot_task

    # Startup
    logger.info("Starting Hyperbot API...")
    try:
        hyperliquid_service.initialize()
        logger.info("Hyperliquid service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Hyperliquid service: {e}")
        logger.warning("API will start but Hyperliquid features may not work")

    # Start Telegram bot if in production/cloud
    if settings.is_cloud_environment():
        logger.info("Starting Telegram bot alongside API...")
        try:
            from src.bot.main import create_application

            _bot_app = create_application()
            await _bot_app.initialize()

            # Start bot in background task
            _bot_task = asyncio.create_task(_bot_app.start())
            if _bot_app.updater:
                await _bot_app.updater.start_polling()
            logger.info("Telegram bot started successfully")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            logger.warning("API will continue without bot")

    yield

    # Shutdown
    logger.info("Shutting down Hyperbot API...")

    # Stop Telegram bot if running
    if _bot_app:
        logger.info("Stopping Telegram bot...")
        try:
            if _bot_app.updater:
                await _bot_app.updater.stop()
            await _bot_app.stop()
            await _bot_app.shutdown()
            if _bot_task:
                _bot_task.cancel()
                with suppress(asyncio.CancelledError):
                    await _bot_task
            logger.info("Telegram bot stopped")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")


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
        health_data["hyperliquid"] = hl_health  # type: ignore
    except Exception as e:
        logger.error(f"Hyperliquid health check failed: {e}")
        health_data["hyperliquid"] = {"status": "error", "message": str(e)}  # type: ignore

    # Determine overall status
    hl_status = health_data.get("hyperliquid", {}).get("status", "error")  # type: ignore
    if hl_status == "unhealthy" or hl_status == "error":
        health_data["api"] = "degraded"

    return health_data
