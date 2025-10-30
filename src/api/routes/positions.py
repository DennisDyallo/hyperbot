"""
Positions API routes.
Handles position management and closing.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from src.services import position_service
from src.api.models import Position, PositionSummary, ClosePositionResponse
from src.config import logger

router = APIRouter(prefix="/api/positions", tags=["Positions"])


class ClosePositionRequest(BaseModel):
    """Request body for closing a position."""

    size: Optional[float] = Field(None, description="Size to close (None = close full position)")
    slippage: float = Field(0.05, description="Maximum acceptable slippage (default 5%)")


@router.get("/", response_model=List[Position])
async def list_positions():
    """
    List all open positions.

    Returns:
        List of open positions with details
    """
    try:
        positions = position_service.list_positions()
        return positions
    except Exception as e:
        logger.error(f"Failed to list positions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch positions")


@router.get("/summary", response_model=PositionSummary)
async def get_position_summary():
    """
    Get summary of all positions.

    Returns:
        Summary with position counts, values, and PnL
    """
    try:
        summary = position_service.get_position_summary()
        return summary
    except Exception as e:
        logger.error(f"Failed to get position summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch position summary")


@router.get("/{coin}", response_model=Position)
async def get_position(coin: str):
    """
    Get details for a specific position.

    Args:
        coin: Trading pair symbol (e.g., BTC, ETH)

    Returns:
        Position details if found

    Raises:
        404: Position not found
    """
    try:
        position = position_service.get_position(coin)
        if not position:
            raise HTTPException(
                status_code=404, detail=f"No open position found for {coin}"
            )
        return position
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get position for {coin}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch position")


@router.post("/{coin}/close", response_model=ClosePositionResponse)
async def close_position(coin: str, request: ClosePositionRequest = Body(...)):
    """
    Close a position (fully or partially).

    Args:
        coin: Trading pair symbol to close
        request: Close request with optional size and slippage

    Returns:
        Close operation result

    Raises:
        400: Invalid request (e.g., size too large)
        404: Position not found
        500: Exchange API error
    """
    try:
        result = position_service.close_position(
            coin=coin, size=request.size, slippage=request.slippage
        )
        return result
    except ValueError as e:
        logger.error(f"Validation error closing {coin}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Runtime error closing {coin}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to close position for {coin}: {e}")
        raise HTTPException(status_code=500, detail="Failed to close position")
