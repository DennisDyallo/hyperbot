"""
Rebalance Use Case.

Unified portfolio rebalancing logic for both API and Bot interfaces.
Wraps rebalance_service with standardized request/response models.
"""

from pydantic import BaseModel, Field

from src.config import logger
from src.services.rebalance_service import TradeAction, rebalance_service
from src.use_cases.base import BaseUseCase


class RebalanceRequest(BaseModel):
    """Request model for portfolio rebalancing."""

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

    class Config:
        json_schema_extra = {
            "example": {
                "target_weights": {"BTC": 50, "ETH": 30, "SOL": 20},
                "leverage": 3,
                "dry_run": True,
                "min_trade_usd": 10.0,
                "max_slippage": 0.05,
            }
        }


class TradeDetail(BaseModel):
    """Details for a single rebalancing trade."""

    coin: str
    action: str  # OPEN, INCREASE, DECREASE, CLOSE, SKIP
    current_allocation_pct: float
    target_allocation_pct: float
    diff_pct: float
    current_usd_value: float
    target_usd_value: float
    trade_usd_value: float
    trade_size: float | None = None

    # Execution details (only for executed trades)
    executed: bool = False
    success: bool = False
    error: str | None = None

    # Risk assessment (only for preview/execution)
    estimated_liquidation_price: float | None = None
    estimated_risk_level: str | None = None
    estimated_health_score: int | None = None


class RebalanceResponse(BaseModel):
    """Response model for portfolio rebalancing."""

    success: bool
    message: str
    dry_run: bool

    # Allocation changes
    initial_allocation: dict[str, float]
    final_allocation: dict[str, float]

    # Trade details
    planned_trades: list[TradeDetail]

    # Execution summary
    total_trades: int
    actionable_trades: int
    executed_trades: int
    successful_trades: int
    failed_trades: int
    skipped_trades: int

    # Trade volume
    total_usd_volume: float

    # Risk warnings
    high_risk_coins: list[str] = Field(default_factory=list)
    critical_risk_prevented: bool = False
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class RebalanceUseCase(BaseUseCase[RebalanceRequest, RebalanceResponse]):
    """
    Use case for portfolio rebalancing with unified logic for API and Bot.

    Features:
    - Validates target allocations
    - Calculates optimal trades
    - Sets leverage before trading
    - Monitors risk during execution
    - Supports both preview (dry_run=True) and execution (dry_run=False)
    - Blocks trades that would create CRITICAL risk

    Example:
        >>> # Preview
        >>> request = RebalanceRequest(
        ...     target_weights={"BTC": 50, "ETH": 50},
        ...     leverage=3,
        ...     dry_run=True
        ... )
        >>> use_case = RebalanceUseCase()
        >>> response = await use_case.execute(request)
        >>> print(f"Planned {response.actionable_trades} trades")
        >>>
        >>> # Execute
        >>> request.dry_run = False
        >>> response = await use_case.execute(request)
        >>> print(f"Executed {response.successful_trades}/{response.executed_trades} trades")
    """

    def __init__(self):
        """Initialize use case with rebalance service."""
        self.rebalance_service = rebalance_service

    async def execute(self, request: RebalanceRequest) -> RebalanceResponse:
        """
        Execute rebalancing use case.

        Args:
            request: Rebalance request with target weights

        Returns:
            Rebalance response with trade details and results

        Raises:
            ValueError: If target weights are invalid
            RuntimeError: If rebalancing fails
        """
        try:
            logger.info(
                f"Rebalance {'preview' if request.dry_run else 'execution'} requested: "
                f"target={request.target_weights}, leverage={request.leverage}x"
            )

            # Execute or preview rebalancing via service
            if request.dry_run:
                result = self.rebalance_service.preview_rebalance(
                    target_weights=request.target_weights,
                    leverage=request.leverage,
                    min_trade_usd=request.min_trade_usd,
                )
            else:
                result = self.rebalance_service.execute_rebalance(
                    target_weights=request.target_weights,
                    leverage=request.leverage,
                    dry_run=False,
                    min_trade_usd=request.min_trade_usd,
                    max_slippage=request.max_slippage,
                )

            # Handle validation errors
            if (
                not result.success
                and result.errors
                and any("weight" in err.lower() for err in result.errors)
            ):
                raise ValueError(result.message)

            # Convert trades to response model
            trade_details = []
            actionable_count = 0
            total_volume = 0.0
            high_risk_coins = []

            for trade in result.planned_trades:
                is_actionable = trade.action != TradeAction.SKIP
                if is_actionable:
                    actionable_count += 1
                    total_volume += abs(trade.trade_usd_value)

                # Check for high-risk trades
                if trade.estimated_risk_level and trade.estimated_risk_level.value in [
                    "HIGH",
                    "CRITICAL",
                ]:
                    high_risk_coins.append(trade.coin)

                trade_detail = TradeDetail(
                    coin=trade.coin,
                    action=trade.action.value,
                    current_allocation_pct=round(trade.current_allocation_pct, 2),
                    target_allocation_pct=round(trade.target_allocation_pct, 2),
                    diff_pct=round(trade.diff_pct, 2),
                    current_usd_value=round(trade.current_usd_value, 2),
                    target_usd_value=round(trade.target_usd_value, 2),
                    trade_usd_value=round(trade.trade_usd_value, 2),
                    trade_size=round(trade.trade_size, 6) if trade.trade_size else None,
                    executed=trade.executed,
                    success=trade.success,
                    error=trade.error,
                    estimated_liquidation_price=trade.estimated_liquidation_price,
                    estimated_risk_level=trade.estimated_risk_level.value
                    if trade.estimated_risk_level
                    else None,
                    estimated_health_score=trade.estimated_health_score,
                )

                trade_details.append(trade_detail)

            # Build response
            response = RebalanceResponse(
                success=result.success,
                message=result.message,
                dry_run=request.dry_run,
                initial_allocation=result.initial_allocation,
                final_allocation=result.final_allocation,
                planned_trades=trade_details,
                total_trades=len(result.planned_trades),
                actionable_trades=actionable_count,
                executed_trades=result.executed_trades,
                successful_trades=result.successful_trades,
                failed_trades=result.failed_trades,
                skipped_trades=result.skipped_trades,
                total_usd_volume=round(total_volume, 2),
                high_risk_coins=high_risk_coins,
                critical_risk_prevented=result.critical_risk_prevented,
                warnings=result.risk_warnings if result.risk_warnings else [],
                errors=result.errors if result.errors else [],
            )

            logger.info(
                f"Rebalance {'preview' if request.dry_run else 'execution'} complete: "
                f"{response.successful_trades} successful, {response.failed_trades} failed, "
                f"{response.skipped_trades} skipped"
            )

            return response

        except ValueError as e:
            logger.error(f"Validation error in rebalancing: {e}")
            raise
        except Exception as e:
            logger.error(f"Rebalancing failed: {e}")
            raise RuntimeError(f"Failed to execute rebalancing: {str(e)}") from e
