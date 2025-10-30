"""
Minimal FastAPI application - starting small.
"""
from fastapi import FastAPI

app = FastAPI(
    title="Hyperbot API",
    description="Trading bot API for Hyperliquid",
    version="0.1.0"
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Hyperbot API",
        "version": "0.1.0",
        "status": "online"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy"
    }
