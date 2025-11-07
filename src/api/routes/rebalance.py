"""
Rebalance API routes.
Handles portfolio rebalancing with risk management.
"""

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from src.config import logger
from src.use_cases.portfolio import RebalanceRequest as UseCaseRebalanceRequest
from src.use_cases.portfolio import RebalanceUseCase, RiskAnalysisRequest, RiskAnalysisUseCase

router = APIRouter(prefix="/api/rebalance", tags=["Rebalance"])

# Initialize use cases
rebalance_use_case = RebalanceUseCase()
risk_analysis_use_case = RiskAnalysisUseCase()


class RebalanceRequest(BaseModel):
    """Request body for rebalancing."""

    target_weights: dict[str, float] = Field(
        description="Target allocation percentages (e.g., {'BTC': 50, 'ETH': 30, 'SOL': 20})"
    )
    leverage: int = Field(
        3, ge=1, le=50, description="Leverage multiplier (default 3x, conservative)"
    )
    dry_run: bool = Field(True, description="Preview only, don't execute (default True)")
    min_trade_usd: float = Field(10.0, ge=0, description="Minimum trade size in USD (default $10)")
    max_slippage: float = Field(
        0.05, ge=0, le=0.5, description="Maximum acceptable slippage (default 5%)"
    )


class RebalancePreviewResponse(BaseModel):
    """Response for rebalance preview."""

    success: bool
    message: str

    # Allocation changes
    initial_allocation: dict[str, float]
    target_allocation: dict[str, float]

    # Planned trades
    planned_trades: list[dict]

    # Trade summary
    total_trades: int
    actionable_trades: int
    total_usd_volume: float

    # Risk warnings
    high_risk_coins: list[str]
    critical_risk_prevented: bool
    warnings: list[str]


@router.post("/preview", response_model=RebalancePreviewResponse)
async def preview_rebalance(request: RebalanceRequest = Body(...)):  # noqa: B008
    """
    Preview rebalancing without executing trades.

    Shows planned trades, allocation changes, and risk assessment.

    Args:
        request: Rebalance parameters

    Returns:
        Preview with planned trades and risk analysis

    Raises:
        400: Invalid target weights or parameters
        500: Service error
    """
    try:
        logger.info(f"Rebalance preview requested: {request.target_weights}")

        # Use RebalanceUseCase for unified logic
        use_case_request = UseCaseRebalanceRequest(
            target_weights=request.target_weights,
            leverage=request.leverage,
            dry_run=True,
            min_trade_usd=request.min_trade_usd,
            max_slippage=request.max_slippage,
        )

        result = await rebalance_use_case.execute(use_case_request)

        if not result.success:
            raise ValueError(result.message)

        # Format trades for response
        trades_data = []
        for trade in result.planned_trades:
            trades_data.append(
                {
                    "coin": trade.coin,
                    "action": trade.action,
                    "current_allocation_pct": trade.current_allocation_pct,
                    "target_allocation_pct": trade.target_allocation_pct,
                    "diff_pct": trade.diff_pct,
                    "trade_usd_value": trade.trade_usd_value,
                    "current_usd_value": trade.current_usd_value,
                    "target_usd_value": trade.target_usd_value,
                }
            )

        response = RebalancePreviewResponse(
            success=True,
            message=result.message,
            initial_allocation=result.initial_allocation,
            target_allocation=request.target_weights,
            planned_trades=trades_data,
            total_trades=result.total_trades,
            actionable_trades=result.actionable_trades,
            total_usd_volume=result.total_usd_volume,
            high_risk_coins=result.high_risk_coins,
            critical_risk_prevented=result.critical_risk_prevented,
            warnings=result.warnings,
        )

        logger.info(f"Preview generated: {result.actionable_trades} actionable trades")
        return response

    except ValueError as e:
        logger.error(f"Validation error in rebalance preview: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to generate rebalance preview: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate preview") from e


@router.post("/execute")
async def execute_rebalance(request: RebalanceRequest = Body(...)):  # noqa: B008
    """
    Execute portfolio rebalancing.

    IMPORTANT: This endpoint modifies positions. Set dry_run=False to execute.

    Steps:
    1. Validate target weights
    2. Set leverage for all coins
    3. Execute trades (close/reduce first, then open/increase)
    4. Monitor risk during execution
    5. Return results

    Args:
        request: Rebalance parameters (dry_run defaults to True for safety)

    Returns:
        Execution results with trade details

    Raises:
        400: Invalid parameters or would create CRITICAL risk
        500: Service error
    """
    try:
        logger.info(
            f"Rebalance execution requested: dry_run={request.dry_run}, "
            f"leverage={request.leverage}x, target={request.target_weights}"
        )

        # Use RebalanceUseCase for unified logic
        use_case_request = UseCaseRebalanceRequest(
            target_weights=request.target_weights,
            leverage=request.leverage,
            dry_run=request.dry_run,
            min_trade_usd=request.min_trade_usd,
            max_slippage=request.max_slippage,
        )

        result = await rebalance_use_case.execute(use_case_request)

        if not result.success:
            # If validation failed, return 400
            if result.errors and any("weight" in err.lower() for err in result.errors):
                raise ValueError(result.message)
            # Otherwise, partial execution (some trades failed) - still return 200
            logger.warning(f"Rebalance partial success: {result.message}")

        # Format response
        trades_data = []
        for trade in result.planned_trades:
            trade_dict = {
                "coin": trade.coin,
                "action": trade.action,
                "executed": trade.executed,
                "success": trade.success,
                "error": trade.error,
                "current_allocation_pct": trade.current_allocation_pct,
                "target_allocation_pct": trade.target_allocation_pct,
                "diff_pct": trade.diff_pct,
                "trade_usd_value": trade.trade_usd_value,
            }

            if trade.trade_size is not None:
                trade_dict["trade_size"] = round(trade.trade_size, 6)

            trades_data.append(trade_dict)

        response = {
            "success": result.success,
            "message": result.message,
            "dry_run": request.dry_run,
            "initial_allocation": result.initial_allocation,
            "final_allocation": result.final_allocation,
            "trades": trades_data,
            "summary": {
                "executed": result.executed_trades,
                "successful": result.successful_trades,
                "failed": result.failed_trades,
                "skipped": result.skipped_trades,
            },
            "errors": result.errors,
        }

        logger.info(
            f"Rebalance {'preview' if request.dry_run else 'execution'} complete: "
            f"{result.successful_trades} successful, {result.failed_trades} failed"
        )

        return response

    except ValueError as e:
        logger.error(f"Validation error in rebalance execution: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to execute rebalance: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute rebalance") from e


@router.get("/risk-summary")
async def get_risk_summary(
    include_cross_margin_ratio: bool = Query(
        True, description="Include Hyperliquid's cross margin ratio metric"
    ),
):
    """
    Get current portfolio risk assessment.

    Returns risk levels for all open positions and overall portfolio health.

    Returns:
        Dict with portfolio risk summary and per-position risk details

    Raises:
        500: Service error
    """
    try:
        logger.debug("Risk summary requested")

        # Use RiskAnalysisUseCase for unified logic
        use_case_request = RiskAnalysisRequest(
            coins=None,  # Analyze all positions
            include_cross_margin_ratio=include_cross_margin_ratio,
        )

        result = await risk_analysis_use_case.execute(use_case_request)

        # Format position risks
        position_risks = []
        for pos in result.positions:
            position_risks.append(
                {
                    "coin": pos.coin,
                    "size": round(pos.size, 6),
                    "side": pos.side,
                    "entry_price": round(pos.entry_price, 2),
                    "current_price": round(pos.current_price, 2),
                    "leverage": pos.leverage,
                    "leverage_type": pos.leverage_type,
                    "risk_level": pos.risk_level,
                    "health_score": pos.health_score,
                    "liquidation_price": round(pos.liquidation_price, 2)
                    if pos.liquidation_price
                    else None,
                    "liquidation_distance_pct": round(pos.liquidation_distance_pct, 2)
                    if pos.liquidation_distance_pct
                    else None,
                    "warnings": pos.warnings,
                }
            )

        # Build response
        response = {
            "success": True,
            "message": f"Risk assessed for {len(result.positions)} positions",
            "portfolio_risk": {
                "overall_risk_level": result.overall_risk_level,
                "overall_health_score": result.portfolio_health_score,
                "position_count": len(result.positions),
                "positions_by_risk": {
                    "SAFE": result.safe_positions,
                    "LOW": result.low_risk_positions,
                    "MODERATE": result.moderate_risk_positions,
                    "HIGH": result.high_risk_positions,
                    "CRITICAL": result.critical_positions,
                },
                "account_value": round(result.account_value, 2),
                "total_margin_used": round(result.total_margin_used, 2),
                "margin_utilization_pct": round(result.margin_utilization_pct, 2),
                "available_margin": round(result.available_margin, 2),
                "critical_positions": result.critical_positions,
                "high_risk_positions": result.high_risk_positions,
                "warnings": result.portfolio_warnings,
            },
            "position_risks": position_risks,
        }

        # Add cross margin ratio if available
        if result.cross_margin_ratio_pct is not None:
            response["portfolio_risk"]["cross_margin_ratio_pct"] = round(
                result.cross_margin_ratio_pct, 2
            )
            response["portfolio_risk"]["cross_maintenance_margin"] = round(
                result.cross_maintenance_margin, 2
            )
            response["portfolio_risk"]["cross_account_value"] = round(result.cross_account_value, 2)

        logger.debug(
            f"Risk summary generated: {result.overall_risk_level} "
            f"({len(result.positions)} positions)"
        )

        return response

    except Exception as e:
        logger.error(f"Failed to get risk summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk summary") from e
