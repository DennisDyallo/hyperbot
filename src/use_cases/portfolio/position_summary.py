"""
Position Summary Use Case.

Unified position summary logic for both API and Bot interfaces.
Aggregates position data, calculates PnL, and includes risk metrics.
"""

from pydantic import BaseModel, Field

from src.config import logger
from src.services.account_service import account_service
from src.services.market_data_service import market_data_service
from src.services.position_service import position_service
from src.services.risk_calculator import RiskLevel, risk_calculator
from src.use_cases.base import BaseUseCase


class PositionSummaryRequest(BaseModel):
    """Request model for position summary."""

    include_risk_metrics: bool = Field(
        True, description="Include risk assessment for each position"
    )
    include_spot_balances: bool = Field(False, description="Include spot token balances in summary")

    class Config:
        json_schema_extra = {
            "example": {"include_risk_metrics": True, "include_spot_balances": False}
        }


class PositionDetail(BaseModel):
    """Detailed information for a single position."""

    coin: str
    size: float
    side: str  # "LONG" or "SHORT"
    entry_price: float
    current_price: float
    position_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    leverage: int
    leverage_type: str

    # Risk metrics (optional)
    risk_level: str | None = None
    health_score: int | None = None
    liquidation_price: float | None = None
    liquidation_distance_pct: float | None = None
    warnings: list[str] = Field(default_factory=list)


class PositionSummaryResponse(BaseModel):
    """Response model for position summary."""

    # Overall metrics
    total_positions: int
    long_positions: int
    short_positions: int
    total_position_value: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float

    # Account metrics
    account_value: float
    available_balance: float
    margin_used: float
    margin_utilization_pct: float

    # Position list
    positions: list[PositionDetail]

    # Optional spot balances
    spot_balances: dict[str, float] | None = None
    num_spot_balances: int = 0

    # Risk summary (if enabled)
    overall_risk_level: str | None = None
    critical_positions: int = 0
    high_risk_positions: int = 0


class PositionSummaryUseCase(BaseUseCase[PositionSummaryRequest, PositionSummaryResponse]):
    """
    Use case for getting position summary with unified logic for API and Bot.

    Features:
    - Aggregates all open positions
    - Calculates total PnL and position values
    - Includes account metrics (balance, margin)
    - Optional risk assessment for each position
    - Optional spot token balances

    Example:
        >>> request = PositionSummaryRequest(include_risk_metrics=True)
        >>> use_case = PositionSummaryUseCase()
        >>> response = await use_case.execute(request)
        >>> print(f"Total PnL: ${response.total_unrealized_pnl:.2f}")
    """

    def __init__(self):
        """Initialize use case with required services."""
        self.position_service = position_service
        self.account_service = account_service
        self.market_data = market_data_service
        self.risk_calculator = risk_calculator

    async def execute(self, request: PositionSummaryRequest) -> PositionSummaryResponse:
        """
        Execute position summary use case.

        Args:
            request: Position summary request

        Returns:
            Position summary response with aggregated data

        Raises:
            RuntimeError: If data fetch fails
        """
        try:
            # Get positions and account data
            positions = self.position_service.list_positions()
            account_info = self.account_service.get_account_info()
            margin_summary = account_info["margin_summary"]

            # Get current prices for risk calculation
            prices = self.market_data.get_all_prices() if request.include_risk_metrics else {}

            # Calculate margin utilization
            margin_util_pct = (
                (margin_summary["total_margin_used"] / margin_summary["account_value"] * 100)
                if margin_summary["account_value"] > 0
                else 0
            )

            # Process each position
            position_details = []
            total_pnl = 0.0
            total_value = 0.0
            long_count = 0
            short_count = 0
            critical_count = 0
            high_risk_count = 0

            for pos_item in positions:
                pos = pos_item["position"]
                coin = pos["coin"]
                size = float(pos["size"])
                entry_price = float(pos["entry_price"])
                position_value = float(pos["position_value"])
                unrealized_pnl = float(pos["unrealized_pnl"])

                # Determine side
                side = "LONG" if size > 0 else "SHORT"
                if size > 0:
                    long_count += 1
                else:
                    short_count += 1

                # Get current price
                current_price = prices.get(coin, entry_price)

                # Calculate PnL percentage
                pnl_pct = (
                    (unrealized_pnl / abs(position_value) * 100) if position_value != 0 else 0.0
                )

                # Aggregate totals
                total_pnl += unrealized_pnl
                total_value += abs(position_value)

                # Build position detail
                detail = PositionDetail(
                    coin=coin,
                    size=abs(size),
                    side=side,
                    entry_price=entry_price,
                    current_price=current_price,
                    position_value=abs(position_value),
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_pct=pnl_pct,
                    leverage=pos["leverage_value"],
                    leverage_type=pos["leverage_type"],
                )

                # Add risk metrics if requested
                if request.include_risk_metrics:
                    try:
                        risk = self.risk_calculator.assess_position_risk(
                            position_data=pos,
                            current_price=current_price,
                            margin_utilization_pct=margin_util_pct,
                        )

                        detail.risk_level = risk.risk_level.value
                        detail.health_score = risk.health_score
                        detail.liquidation_price = risk.liquidation_price
                        detail.liquidation_distance_pct = risk.liquidation_distance_pct
                        detail.warnings = risk.warnings

                        # Count risk levels
                        if risk.risk_level == RiskLevel.CRITICAL:
                            critical_count += 1
                        elif risk.risk_level == RiskLevel.HIGH:
                            high_risk_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to calculate risk for {coin}: {e}")

                position_details.append(detail)

            # Calculate overall PnL percentage
            total_pnl_pct = (
                (total_pnl / margin_summary["account_value"] * 100)
                if margin_summary["account_value"] > 0
                else 0.0
            )

            # Determine overall risk level
            overall_risk = None
            if request.include_risk_metrics and position_details:
                if critical_count > 0:
                    overall_risk = "CRITICAL"
                elif high_risk_count > 0:
                    overall_risk = "HIGH"
                elif any(p.risk_level == "MODERATE" for p in position_details):
                    overall_risk = "MODERATE"
                elif any(p.risk_level == "LOW" for p in position_details):
                    overall_risk = "LOW"
                else:
                    overall_risk = "SAFE"

            # Get spot balances if requested
            spot_balances = None
            num_spot = 0
            if request.include_spot_balances:
                try:
                    spot_state = self.account_service.get_spot_state()  # type: ignore
                    balances = spot_state.get("balances", [])
                    spot_balances = {
                        b["coin"]: float(b["total"]) for b in balances if float(b["total"]) > 0
                    }
                    num_spot = len(spot_balances)
                except Exception as e:
                    logger.warning(f"Failed to fetch spot balances: {e}")

            # Build response
            return PositionSummaryResponse(
                total_positions=len(positions),
                long_positions=long_count,
                short_positions=short_count,
                total_position_value=total_value,
                total_unrealized_pnl=total_pnl,
                total_unrealized_pnl_pct=total_pnl_pct,
                account_value=margin_summary["account_value"],
                available_balance=margin_summary["total_raw_usd"],
                margin_used=margin_summary["total_margin_used"],
                margin_utilization_pct=margin_util_pct,
                positions=position_details,
                spot_balances=spot_balances,
                num_spot_balances=num_spot,
                overall_risk_level=overall_risk,
                critical_positions=critical_count,
                high_risk_positions=high_risk_count,
            )

        except Exception as e:
            logger.error(f"Position summary failed: {e}")
            raise RuntimeError(f"Failed to get position summary: {str(e)}") from e
