"""
Positions API routes.
Handles position management and closing.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from src.services import position_service
from src.services.risk_calculator import risk_calculator
from src.services.market_data_service import market_data_service
from src.services.account_service import account_service
from src.api.models import Position, PositionSummary, ClosePositionResponse
from src.config import logger

router = APIRouter(prefix="/api/positions", tags=["Positions"])
templates = Jinja2Templates(directory="src/api/templates")


class ClosePositionRequest(BaseModel):
    """Request body for closing a position."""

    size: Optional[float] = Field(None, description="Size to close (None = close full position)")
    slippage: float = Field(0.05, description="Maximum acceptable slippage (default 5%)")


class BulkCloseRequest(BaseModel):
    """Request body for bulk closing positions."""

    percentage: int = Field(..., description="Percentage of positions to close (33, 66, or 100)", ge=1, le=100)
    slippage: float = Field(0.05, description="Maximum acceptable slippage (default 5%)")


@router.get("/")
async def list_positions(request: Request):
    """
    List all open positions with risk indicators.
    Returns HTML partial if requested by HTMX, otherwise JSON.

    Returns:
        List of open positions with details and risk assessment
    """
    try:
        positions = position_service.list_positions()

        # Calculate risk for each position if we have positions
        if positions:
            try:
                # Get current prices and account data for risk calculation
                prices = market_data_service.get_all_prices()
                account_info = account_service.get_account_info()
                margin_summary = account_info["margin_summary"]

                # Calculate overall margin utilization percentage
                margin_util_pct = (
                    (margin_summary["total_margin_used"] / margin_summary["account_value"] * 100)
                    if margin_summary["account_value"] > 0 else 0
                )

                # Assess risk for each position
                for pos_item in positions:
                    pos = pos_item["position"]
                    coin = pos["coin"]

                    # Get current price (fallback to entry price if not available)
                    current_price = prices.get(coin, pos["entry_price"])

                    # Calculate risk assessment
                    risk = risk_calculator.assess_position_risk(
                        position_data=pos,
                        current_price=current_price,
                        margin_utilization_pct=margin_util_pct
                    )

                    # Add risk data to position item
                    pos_item["risk"] = {
                        "level": risk.risk_level.value,
                        "health_score": risk.health_score,
                        "liquidation_price": risk.liquidation_price,
                        "liquidation_distance_pct": risk.liquidation_distance_pct,
                        "warnings": risk.warnings
                    }

                    liq_price_str = f"${risk.liquidation_price:.2f}" if risk.liquidation_price is not None else "N/A"
                    liq_dist_str = f"{risk.liquidation_distance_pct:.1f}%" if risk.liquidation_distance_pct is not None else "N/A"
                    logger.debug(
                        f"{coin} risk: {risk.risk_level.value}, "
                        f"liq price: {liq_price_str}, "
                        f"distance: {liq_dist_str}"
                    )

            except Exception as e:
                # Log error but don't fail the whole request
                logger.error(f"Failed to calculate risk for positions: {e}")
                # Risk data won't be available in template

        # Check if request is from HTMX
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                "partials/positions_table.html",
                {"request": request, "positions": positions},
                headers={"Content-Type": "text/html"}
            )

        return positions
    except Exception as e:
        logger.error(f"Failed to list positions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch positions")


@router.get("/summary")
async def get_position_summary(request: Request):
    """
    Get summary of all positions.
    Returns HTML partial if requested by HTMX, otherwise JSON.

    Returns:
        Summary with position counts, values, and PnL
    """
    try:
        summary = position_service.get_position_summary()

        # Check if request is from HTMX
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(
                "partials/position_summary.html",
                {"request": request, "summary": summary},
                headers={"Content-Type": "text/html"}
            )

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


@router.post("/bulk-close")
async def bulk_close_positions(request: BulkCloseRequest = Body(...)):
    """
    Close a percentage of each open position.

    Args:
        request: Bulk close request with percentage and slippage

    Returns:
        Summary of close operations (success count, failed count, errors)

    Raises:
        500: Exchange API error
    """
    try:
        # Get all positions
        positions = position_service.list_positions()

        if not positions:
            return {
                "success": 0,
                "failed": 0,
                "total": 0,
                "errors": [],
                "message": "No positions to close"
            }

        total_positions = len(positions)
        success_count = 0
        failed_count = 0
        errors = []

        # Close percentage of each position
        for item in positions:
            pos = item["position"]
            coin = pos["coin"]
            position_size = abs(pos["size"])

            # Calculate size to close (percentage of current position)
            if request.percentage == 100:
                # Close full position
                size_to_close = None
            else:
                # Close percentage of position
                size_to_close = position_size * (request.percentage / 100)

            try:
                position_service.close_position(
                    coin=coin,
                    size=size_to_close,
                    slippage=request.slippage
                )
                success_count += 1
                logger.info(f"Successfully closed {request.percentage}% of {coin} position (bulk close)")

            except Exception as e:
                failed_count += 1
                error_msg = f"{coin}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to close {coin} in bulk operation: {e}")

        # Build message based on results
        message_parts = []
        if success_count > 0:
            message_parts.append(f"Closed {request.percentage}% of {success_count} position(s)")
        if failed_count > 0:
            message_parts.append(f"{failed_count} failed (too small or invalid)")

        return {
            "success": success_count,
            "failed": failed_count,
            "total": total_positions,
            "errors": errors,
            "message": ", ".join(message_parts) if message_parts else "No positions affected"
        }

    except Exception as e:
        logger.error(f"Bulk close operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk close failed: {str(e)}")
