"""
Risk Analysis Use Case.

Unified risk assessment logic for both API and Bot interfaces.
Calculates portfolio and position-level risk metrics.
"""

from pydantic import BaseModel, Field

from src.config import logger
from src.services.account_service import account_service
from src.services.market_data_service import market_data_service
from src.services.position_service import position_service
from src.services.risk_calculator import risk_calculator
from src.use_cases.base import BaseUseCase


class RiskAnalysisRequest(BaseModel):
    """Request model for risk analysis."""

    coins: list[str] | None = Field(
        None, description="Specific coins to analyze. If None, analyze all positions."
    )
    include_cross_margin_ratio: bool = Field(
        True, description="Include cross margin ratio (official Hyperliquid metric)"
    )

    class Config:
        json_schema_extra = {"example": {"coins": None, "include_cross_margin_ratio": True}}


class PositionRiskDetail(BaseModel):
    """Risk details for a single position."""

    coin: str
    size: float
    side: str
    entry_price: float
    current_price: float
    leverage: int
    leverage_type: str

    # Risk metrics
    risk_level: str
    health_score: int
    liquidation_price: float
    liquidation_distance_pct: float
    warnings: list[str]


class RiskAnalysisResponse(BaseModel):
    """Response model for risk analysis."""

    # Overall portfolio risk
    overall_risk_level: str
    portfolio_health_score: int

    # Cross Margin Ratio (Hyperliquid official metric)
    cross_margin_ratio_pct: float | None = None
    cross_maintenance_margin: float | None = None
    cross_account_value: float | None = None

    # Risk breakdown
    critical_positions: int
    high_risk_positions: int
    moderate_risk_positions: int
    low_risk_positions: int
    safe_positions: int

    # Account metrics
    margin_utilization_pct: float
    available_margin: float
    total_margin_used: float
    account_value: float

    # Position-level risks
    positions: list[PositionRiskDetail]

    # Portfolio-level warnings
    portfolio_warnings: list[str] = Field(default_factory=list)


class RiskAnalysisUseCase(BaseUseCase[RiskAnalysisRequest, RiskAnalysisResponse]):
    """
    Use case for portfolio risk analysis with unified logic for API and Bot.

    Features:
    - Portfolio-level risk assessment
    - Position-level risk metrics
    - Cross Margin Ratio (Hyperliquid's official metric)
    - Liquidation distance calculations
    - Health scores and risk levels
    - Actionable warnings

    Example:
        >>> request = RiskAnalysisRequest(include_cross_margin_ratio=True)
        >>> use_case = RiskAnalysisUseCase()
        >>> response = await use_case.execute(request)
        >>> print(f"Overall Risk: {response.overall_risk_level}")
        >>> print(f"Cross Margin Ratio: {response.cross_margin_ratio_pct:.2f}%")
    """

    def __init__(self):
        """Initialize use case with required services."""
        self.risk_calculator = risk_calculator
        self.position_service = position_service
        self.account_service = account_service
        self.market_data = market_data_service

    async def execute(self, request: RiskAnalysisRequest) -> RiskAnalysisResponse:
        """
        Execute risk analysis use case.

        Args:
            request: Risk analysis request

        Returns:
            Risk analysis response with comprehensive metrics

        Raises:
            RuntimeError: If risk calculation fails
        """
        try:
            # Get account data and positions
            account_info = self.account_service.get_account_info()
            all_positions = self.position_service.list_positions()
            margin_summary = account_info["margin_summary"]

            # Filter positions if specific coins requested
            if request.coins:
                all_positions = [p for p in all_positions if p["position"]["coin"] in request.coins]

            # Get current prices
            prices = self.market_data.get_all_prices()

            # Calculate margin utilization
            margin_util_pct = (
                (margin_summary["total_margin_used"] / margin_summary["account_value"] * 100)
                if margin_summary["account_value"] > 0
                else 0
            )

            # Get Cross Margin Ratio if requested (Hyperliquid official metric)
            cross_margin_ratio = None
            cross_maintenance_margin = None
            cross_account_value = None

            if request.include_cross_margin_ratio:
                try:
                    cross_data = account_info.get("crossMarginSummary")
                    if cross_data:
                        cross_maintenance_margin = float(
                            cross_data.get("crossMaintenanceMarginUsed", 0)
                        )
                        cross_account_value = float(
                            cross_data.get("accountValue", margin_summary["account_value"])
                        )
                        if cross_account_value > 0:
                            cross_margin_ratio = (
                                cross_maintenance_margin / cross_account_value
                            ) * 100
                except Exception as e:
                    logger.warning(f"Failed to get cross margin ratio: {e}")

            # Analyze each position
            position_risks = []
            risk_counts = {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "LOW": 0, "SAFE": 0}

            for pos_item in all_positions:
                pos = pos_item["position"]
                coin = pos["coin"]
                current_price = prices.get(coin, float(pos.get("mark_price", pos["entry_price"])))

                # Assess position risk
                try:
                    risk = self.risk_calculator.assess_position_risk(
                        position_data=pos,
                        current_price=current_price,
                        margin_utilization_pct=margin_util_pct,
                    )

                    # Count risk levels
                    risk_counts[risk.risk_level.value] += 1

                    # Build position risk detail
                    position_risks.append(
                        PositionRiskDetail(
                            coin=coin,
                            size=abs(float(pos["size"])),
                            side="LONG" if float(pos["size"]) > 0 else "SHORT",
                            entry_price=float(pos["entry_price"]),
                            current_price=current_price,
                            leverage=pos["leverage_value"],
                            leverage_type=pos["leverage_type"],
                            risk_level=risk.risk_level.value,
                            health_score=risk.health_score,
                            liquidation_price=risk.liquidation_price,
                            liquidation_distance_pct=risk.liquidation_distance_pct,
                            warnings=risk.warnings,
                        )
                    )

                except Exception as e:
                    logger.error(f"Failed to assess risk for {coin}: {e}")
                    continue

            # Assess overall portfolio risk
            portfolio_risk_result = self.risk_calculator.assess_portfolio_risk(
                all_positions, margin_summary, prices
            )

            # Build response
            return RiskAnalysisResponse(
                overall_risk_level=portfolio_risk_result.overall_risk_level.value,
                portfolio_health_score=portfolio_risk_result.overall_health_score,
                cross_margin_ratio_pct=cross_margin_ratio,
                cross_maintenance_margin=cross_maintenance_margin,
                cross_account_value=cross_account_value,
                critical_positions=risk_counts["CRITICAL"],
                high_risk_positions=risk_counts["HIGH"],
                moderate_risk_positions=risk_counts["MODERATE"],
                low_risk_positions=risk_counts["LOW"],
                safe_positions=risk_counts["SAFE"],
                margin_utilization_pct=margin_util_pct,
                available_margin=margin_summary["total_raw_usd"],
                total_margin_used=margin_summary["total_margin_used"],
                account_value=margin_summary["account_value"],
                positions=position_risks,
                portfolio_warnings=portfolio_risk_result.warnings,
            )

        except Exception as e:
            logger.error(f"Risk analysis failed: {e}")
            raise RuntimeError(f"Failed to analyze risk: {str(e)}") from e
