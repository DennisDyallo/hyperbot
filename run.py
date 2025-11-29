#!/usr/bin/env python3
"""
Run script for Hyperbot API server.
"""

import os

import uvicorn

if __name__ == "__main__":
    # Use reload only in development
    is_dev = os.getenv("ENVIRONMENT", "development").lower() == "development"

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=is_dev,  # Only reload in development
        log_level="info",
        workers=1 if is_dev else 4,  # Multiple workers in production
    )
