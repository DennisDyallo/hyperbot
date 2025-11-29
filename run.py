#!/usr/bin/env python3
"""
Run script for Hyperbot API server + Telegram bot.
"""

import os

import uvicorn

if __name__ == "__main__":
    # Get port from environment (Cloud Run uses $PORT)
    port = int(os.getenv("PORT", "8000"))

    # Use reload only in development
    is_dev = os.getenv("ENVIRONMENT", "development").lower() == "development"

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=is_dev,  # Only reload in development
        log_level="info",
        workers=1,  # Must use 1 worker when running bot alongside API
    )
