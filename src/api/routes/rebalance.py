"""
Rebalance API routes.
Handles portfolio rebalancing with risk management.
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from src.services.rebalance_service import rebalance_service
from src.services.risk_calculator import risk_calculator
from src.services.position_service import position_service
from src.services.account_service import account_service
from src.services.market_data_service import market_data_service
from src.config import logger

router = APIRouter(prefix="/api/rebalance", tags=["Rebalance"])


class RebalanceRequest(BaseModel):
    """Request body for rebalancing."""

    target_weights: Dict[str, float] = Field(
        description="Target allocation percentages (e.g., {'BTC': 50, 'ETH': 30, 'SOL': 20})"
    )
    leverage: int = Field(5, ge=1, le=50, description="Leverage multiplier (default 5x)")
    dry_run: bool = Field(True, description="Preview only, don't execute (default True)")
    min_trade_usd: float = Field(10.0, ge=0, description="Minimum trade size in USD (default $10)")
    max_slippage: float = Field(0.05, ge=0, le=0.5, description="Maximum acceptable slippage (default 5%)")


class RebalancePreviewResponse(BaseModel):
    """Response for rebalance preview."""

    success: bool
    message: str

    # Allocation changes
    initial_allocation: Dict[str, float]
    target_allocation: Dict[str, float]

    # Planned trades
    planned_trades: List[Dict]

    # Trade summary
    total_trades: int
    actionable_trades: int
    total_usd_volume: float

    # Risk warnings
    high_risk_coins: List[str]
    critical_risk_prevented: bool
    warnings: List[str]


@router.post("/preview", response_model=RebalancePreviewResponse)
async def preview_rebalance(request: RebalanceRequest = Body(...)):
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

        # Get preview from service
        result = rebalance_service.preview_rebalance(
            target_weights=request.target_weights,
            leverage=request.leverage,
            min_trade_usd=request.min_trade_usd
        )

        if not result.success:
            raise ValueError(result.message)

        # Calculate total USD volume
        total_volume = sum(
            abs(trade.trade_usd_value)
            for trade in result.planned_trades
            if trade.action.value not in ["SKIP"]
        )

        # Identify high-risk trades (would create HIGH or CRITICAL risk)
        high_risk_coins = []
        for trade in result.planned_trades:
            if trade.estimated_risk_level and trade.estimated_risk_level.value in ["HIGH", "CRITICAL"]:
                high_risk_coins.append(trade.coin)

        # Format trades for response
        trades_data = []
        for trade in result.planned_trades:
            trades_data.append({
                "coin": trade.coin,
                "action": trade.action.value,
                "current_allocation_pct": round(trade.current_allocation_pct, 2),
                "target_allocation_pct": round(trade.target_allocation_pct, 2),
                "diff_pct": round(trade.diff_pct, 2),
                "trade_usd_value": round(trade.trade_usd_value, 2),
                "current_usd_value": round(trade.current_usd_value, 2),
                "target_usd_value": round(trade.target_usd_value, 2),
            })

        actionable_count = sum(
            1 for trade in result.planned_trades
            if trade.action.value not in ["SKIP"]
        )

        response = RebalancePreviewResponse(
            success=True,
            message=result.message,
            initial_allocation=result.initial_allocation,
            target_allocation=request.target_weights,
            planned_trades=trades_data,
            total_trades=len(result.planned_trades),
            actionable_trades=actionable_count,
            total_usd_volume=total_volume,
            high_risk_coins=high_risk_coins,
            critical_risk_prevented=False,
            warnings=result.errors if result.errors else []
        )

        logger.info(f"Preview generated: {actionable_count} actionable trades")
        return response

    except ValueError as e:
        logger.error(f"Validation error in rebalance preview: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate rebalance preview: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate preview")


@router.post("/execute")
async def execute_rebalance(request: RebalanceRequest = Body(...)):
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

        # Execute rebalancing
        result = rebalance_service.execute_rebalance(
            target_weights=request.target_weights,
            leverage=request.leverage,
            dry_run=request.dry_run,
            min_trade_usd=request.min_trade_usd,
            max_slippage=request.max_slippage
        )

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
                "action": trade.action.value,
                "executed": trade.executed,
                "success": trade.success,
                "error": trade.error,
                "current_allocation_pct": round(trade.current_allocation_pct, 2),
                "target_allocation_pct": round(trade.target_allocation_pct, 2),
                "diff_pct": round(trade.diff_pct, 2),
                "trade_usd_value": round(trade.trade_usd_value, 2),
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
            "errors": result.errors if result.errors else []
        }

        logger.info(
            f"Rebalance {'preview' if request.dry_run else 'execution'} complete: "
            f"{result.successful_trades} successful, {result.failed_trades} failed"
        )

        return response

    except ValueError as e:
        logger.error(f"Validation error in rebalance execution: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute rebalance: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute rebalance")


@router.get("/risk-summary")
async def get_risk_summary():
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

        # Get positions and prices
        account_info = account_service.get_account_info()
        positions = account_info.get("positions", [])
        margin_summary = account_info["margin_summary"]

        if not positions:
            return {
                "success": True,
                "message": "No open positions",
                "portfolio_risk": {
                    "overall_risk_level": "SAFE",
                    "overall_health_score": 100,
                    "position_count": 0,
                    "positions_by_risk": {
                        "SAFE": 0,
                        "LOW": 0,
                        "MODERATE": 0,
                        "HIGH": 0,
                        "CRITICAL": 0
                    },
                    "margin_utilization_pct": 0.0,
                    "warnings": [],
                    "recommendations": []
                },
                "position_risks": []
            }

        # Get current prices
        prices = market_data_service.get_all_prices()

        # Assess portfolio risk
        portfolio_risk = risk_calculator.assess_portfolio_risk(
            positions=positions,
            margin_summary=margin_summary,
            prices=prices
        )

        # Assess individual positions
        position_risks = []
        for pos in positions:
            position_data = pos["position"]
            coin = position_data["coin"]
            current_price = prices.get(coin, position_data.get("entry_price", 0))

            margin_util = (
                margin_summary["total_margin_used"] / margin_summary["account_value"] * 100
                if margin_summary["account_value"] > 0
                else 0
            )

            risk = risk_calculator.assess_position_risk(
                position_data=position_data,
                current_price=current_price,
                margin_utilization_pct=margin_util
            )

            position_risks.append({
                "coin": risk.coin,
                "risk_level": risk.risk_level.value,
                "health_score": risk.health_score,
                "current_price": round(risk.current_price, 2),
                "liquidation_price": round(risk.liquidation_price, 2) if risk.liquidation_price else None,
                "liquidation_distance_pct": round(risk.liquidation_distance_pct, 2) if risk.liquidation_distance_pct else None,
                "liquidation_distance_usd": round(risk.liquidation_distance_usd, 2) if risk.liquidation_distance_usd else None,
                "size": round(risk.size, 6),
                "entry_price": round(risk.entry_price, 2),
                "position_value": round(risk.position_value, 2),
                "unrealized_pnl": round(risk.unrealized_pnl, 2),
                "leverage": risk.leverage,
                "leverage_type": risk.leverage_type,
                "warnings": risk.warnings,
                "recommendations": risk.recommendations
            })

        response = {
            "success": True,
            "message": f"Risk assessed for {portfolio_risk.position_count} positions",
            "portfolio_risk": {
                "overall_risk_level": portfolio_risk.overall_risk_level.value,
                "overall_health_score": portfolio_risk.overall_health_score,
                "position_count": portfolio_risk.position_count,
                "positions_by_risk": portfolio_risk.positions_by_risk,
                "account_value": round(portfolio_risk.account_value, 2),
                "total_margin_used": round(portfolio_risk.total_margin_used, 2),
                "margin_utilization_pct": round(portfolio_risk.margin_utilization_pct, 2),
                "available_margin": round(portfolio_risk.available_margin, 2),
                "critical_positions": portfolio_risk.critical_positions,
                "high_risk_positions": portfolio_risk.high_risk_positions,
                "warnings": portfolio_risk.warnings,
                "recommendations": portfolio_risk.recommendations
            },
            "position_risks": position_risks
        }

        logger.debug(
            f"Risk summary generated: {portfolio_risk.overall_risk_level.value} "
            f"({portfolio_risk.position_count} positions)"
        )

        return response

    except Exception as e:
        logger.error(f"Failed to get risk summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk summary")
