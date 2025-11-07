"""
Risk Calculator Service for position and portfolio risk assessment.

This service calculates liquidation distance, risk levels, and health scores
for trading positions. Based on industry research (Binance, Bybit, dYdX, GMX).

See: docs/research/risk-indicators-industry-research.md
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.config import logger


class RiskLevel(str, Enum):
    """
    Risk level categories based on liquidation distance.

    Conservative thresholds for crypto volatility:
    - SAFE: > 50% from liquidation (safe through 2-3 major moves)
    - LOW: 30-50% from liquidation (safe through 1-2 major moves)
    - MODERATE: 15-30% from liquidation (vulnerable to large swing)
    - HIGH: 8-15% from liquidation (one bad day could liquidate)
    - CRITICAL: < 8% from liquidation (flash crash risk)
    """

    SAFE = "SAFE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class RiskThresholds:
    """
    Configurable risk thresholds (liquidation distance percentages).

    Default values are CONSERVATIVE for crypto markets.
    Based on research from major exchanges (see docs/research/).
    """

    safe_distance: float = 50.0  # > 50% from liquidation
    low_distance: float = 30.0  # 30-50% from liquidation
    moderate_distance: float = 15.0  # 15-30% from liquidation
    high_distance: float = 8.0  # 8-15% from liquidation
    # < 8% is CRITICAL


@dataclass
class PositionRisk:
    """Risk assessment for a single position."""

    coin: str
    risk_level: RiskLevel
    health_score: int  # 0-100, derived from risk_level

    # Liquidation metrics
    liquidation_price: float | None
    current_price: float
    liquidation_distance_pct: float | None  # % price move to liquidation
    liquidation_distance_usd: float | None  # USD distance to liquidation

    # Position details
    size: float
    entry_price: float
    position_value: float
    unrealized_pnl: float
    leverage: int
    leverage_type: str

    # Guidance
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class PortfolioRisk:
    """Risk assessment for entire portfolio."""

    overall_risk_level: RiskLevel
    overall_health_score: int  # 0-100

    # Position breakdown
    position_count: int
    positions_by_risk: dict[str, int]  # {"SAFE": 2, "CRITICAL": 1, ...}

    # Margin metrics
    account_value: float
    total_margin_used: float
    margin_utilization_pct: float
    available_margin: float

    # Risk positions
    critical_positions: list[str]  # Coins at CRITICAL risk
    high_risk_positions: list[str]  # Coins at HIGH risk

    # Warnings
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class RiskCalculator:
    """
    Calculate risk metrics for positions and portfolio.

    Primary metric: Liquidation distance (% price move to liquidation)
    Secondary metric: Health score (0-100, derived from risk_level)

    Usage:
        calculator = RiskCalculator()
        position_risk = calculator.assess_position_risk(position_data, current_price)
        portfolio_risk = calculator.assess_portfolio_risk(positions, margin_summary, prices)
    """

    def __init__(self, thresholds: RiskThresholds | None = None):
        """
        Initialize risk calculator.

        Args:
            thresholds: Custom risk thresholds (uses conservative defaults if None)
        """
        self.thresholds = thresholds or RiskThresholds()
        logger.debug(f"Risk calculator initialized with thresholds: {self.thresholds}")

    def calculate_liquidation_distance(
        self, current_price: float, liquidation_price: float | None, position_size: float
    ) -> tuple[float | None, float | None]:
        """
        Calculate distance to liquidation (percentage and USD).

        Args:
            current_price: Current market price
            liquidation_price: Liquidation price from API (None if no position)
            position_size: Signed position size (+ long, - short)

        Returns:
            Tuple of (distance_pct, distance_usd) or (None, None) if no liquidation price
        """
        if liquidation_price is None or liquidation_price == 0:
            return None, None

        if position_size > 0:  # Long position
            # Liquidation occurs when price falls below liquidation_price
            distance_pct = ((current_price - liquidation_price) / current_price) * 100
            distance_usd = (current_price - liquidation_price) * abs(position_size)
        else:  # Short position
            # Liquidation occurs when price rises above liquidation_price
            distance_pct = ((liquidation_price - current_price) / current_price) * 100
            distance_usd = (liquidation_price - current_price) * abs(position_size)

        # Ensure positive values
        distance_pct = abs(distance_pct)
        distance_usd = abs(distance_usd)

        return distance_pct, distance_usd

    def determine_risk_level_from_margin_ratio(self, cross_margin_ratio_pct: float) -> RiskLevel:
        """
        Determine risk level from Cross Margin Ratio (OFFICIAL HYPERLIQUID METRIC).

        This is the PRIMARY risk metric for cross-margin positions.
        Liquidation occurs when Cross Margin Ratio reaches 100%.

        Cross Margin Ratio = Maintenance Margin / Account Value × 100

        Args:
            cross_margin_ratio_pct: Cross margin ratio percentage (0-100+)

        Returns:
            RiskLevel enum

        Thresholds (conservative for crypto):
        - SAFE: < 30% (far from liquidation)
        - LOW: 30-50% (moderate buffer)
        - MODERATE: 50-70% (getting close)
        - HIGH: 70-90% (dangerous, one bad move)
        - CRITICAL: > 90% (liquidation imminent, 100% = liquidation!)
        """
        if cross_margin_ratio_pct >= 90:
            return RiskLevel.CRITICAL  # Approaching 100% liquidation!
        elif cross_margin_ratio_pct >= 70:
            return RiskLevel.HIGH
        elif cross_margin_ratio_pct >= 50:
            return RiskLevel.MODERATE
        elif cross_margin_ratio_pct >= 30:
            return RiskLevel.LOW
        else:
            return RiskLevel.SAFE

    def determine_risk_level(
        self, liquidation_distance_pct: float | None,  # noqa: ARG002 margin_utilization_pct: float = 0
    ) -> RiskLevel:
        """
        Determine risk level from liquidation distance.

        NOTE: For cross-margin positions, use determine_risk_level_from_margin_ratio()
        instead, as it's the official Hyperliquid metric.

        Args:
            liquidation_distance_pct: % distance to liquidation (None if no liq price)
            margin_utilization_pct: % of account margin used (optional, elevates risk)

        Returns:
            RiskLevel enum
        """
        if liquidation_distance_pct is None:
            # No liquidation price (spot position or very low leverage)
            return RiskLevel.SAFE

        # Primary metric: liquidation distance
        if liquidation_distance_pct < self.thresholds.high_distance:
            risk = RiskLevel.CRITICAL
        elif liquidation_distance_pct < self.thresholds.moderate_distance:
            risk = RiskLevel.HIGH
        elif liquidation_distance_pct < self.thresholds.low_distance:
            risk = RiskLevel.MODERATE
        elif liquidation_distance_pct < self.thresholds.safe_distance:
            risk = RiskLevel.LOW
        else:
            risk = RiskLevel.SAFE

        # Elevate risk if margin usage very high
        if margin_utilization_pct > 85 and risk == RiskLevel.LOW:
            risk = RiskLevel.MODERATE

        return risk

    def derive_health_score(self, risk_level: RiskLevel) -> int:
        """
        Derive health score (0-100) from risk level.

        Simplified approach: health_score is derived from risk_level,
        not a complex composite. Single source of truth.

        Args:
            risk_level: The risk level enum

        Returns:
            Health score (0-100):
            - SAFE: 90-100 (randomly in range for visual variety)
            - LOW: 70-89
            - MODERATE: 50-69
            - HIGH: 25-49
            - CRITICAL: 0-24
        """

        ranges = {
            RiskLevel.SAFE: (90, 100),
            RiskLevel.LOW: (70, 89),
            RiskLevel.MODERATE: (50, 69),
            RiskLevel.HIGH: (25, 49),
            RiskLevel.CRITICAL: (0, 24),
        }

        min_score, max_score = ranges[risk_level]
        # Use midpoint for consistency (not random, for predictability)
        health_score = (min_score + max_score) // 2

        return health_score

    def generate_warnings(
        self,
        risk_level: RiskLevel,
        liquidation_distance_pct: float | None,  # noqa: ARG002  # noqa: ARG002
        leverage: int,
        unrealized_pnl: float,
    ) -> list[str]:
        """
        Generate position-specific warnings.

        Args:
            risk_level: Current risk level
            liquidation_distance_pct: % to liquidation
            leverage: Position leverage
            unrealized_pnl: Unrealized profit/loss

        Returns:
            List of warning strings
        """
        warnings = []

        if risk_level == RiskLevel.CRITICAL:
            warnings.append("⚠️ CRITICAL RISK: Liquidation imminent (<8% away)")
            warnings.append("🚨 Immediate action required - Consider reducing position")

        elif risk_level == RiskLevel.HIGH:
            warnings.append("⚠️ HIGH RISK: Close to liquidation (8-15% away)")
            warnings.append("Consider adding margin or closing position")

        elif risk_level == RiskLevel.MODERATE:
            warnings.append("⚠️ MODERATE RISK: Vulnerable to volatility (15-30% away)")

        if leverage > 10:
            warnings.append(f"⚠️ High leverage ({leverage}x) amplifies risk")

        if unrealized_pnl < 0 and abs(unrealized_pnl) > 100:
            warnings.append(f"⚠️ Significant unrealized loss: ${unrealized_pnl:.2f}")

        return warnings

    def generate_recommendations(
        self,
        risk_level: RiskLevel,
        liquidation_distance_pct: float | None,  # noqa: ARG002
        leverage: int,  # noqa: ARG002
    ) -> list[str]:
        """
        Generate position-specific recommendations.

        Args:
            risk_level: Current risk level
            liquidation_distance_pct: % to liquidation
            leverage: Position leverage

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("💡 Close position immediately or add significant margin")
            recommendations.append("💡 Reduce leverage to increase safety buffer")

        elif risk_level == RiskLevel.HIGH:
            recommendations.append("💡 Consider partially closing position")
            recommendations.append("💡 Add margin to increase liquidation distance")
            recommendations.append("💡 Set stop-loss to limit downside")

        elif risk_level == RiskLevel.MODERATE:
            recommendations.append("💡 Monitor position closely during volatility")
            recommendations.append("💡 Consider reducing leverage if possible")

        if leverage > 15:
            recommendations.append(f"💡 Reduce leverage from {leverage}x to 5-10x for safety")

        return recommendations

    def assess_position_risk(
        self, position_data: dict[str, Any], current_price: float, margin_utilization_pct: float = 0
    ) -> PositionRisk:
        """
        Assess risk for a single position.

        Args:
            position_data: Position dict from account_service
                          (must have keys: coin, size, entry_price, position_value,
                           unrealized_pnl, leverage_value, leverage_type, liquidation_price)
            current_price: Current market price for the coin
            margin_utilization_pct: Overall account margin utilization

        Returns:
            PositionRisk dataclass with full risk assessment
        """
        coin = position_data["coin"]
        size = position_data["size"]
        liquidation_price = position_data.get("liquidation_price")

        # Calculate liquidation distance
        distance_pct, distance_usd = self.calculate_liquidation_distance(
            current_price, liquidation_price, size
        )

        # Determine risk level
        risk_level = self.determine_risk_level(distance_pct, margin_utilization_pct)

        # Derive health score from risk level
        health_score = self.derive_health_score(risk_level)

        # Generate warnings and recommendations
        warnings = self.generate_warnings(
            risk_level,
            distance_pct,
            position_data["leverage_value"],
            position_data["unrealized_pnl"],
        )

        recommendations = self.generate_recommendations(
            risk_level, distance_pct, position_data["leverage_value"]
        )

        # Format liquidation distance safely (can be None)
        liq_dist_str = f"{distance_pct:.1f}%" if distance_pct is not None else "N/A"
        logger.debug(
            f"Position risk for {coin}: {risk_level.value} "
            f"(health: {health_score}, liq distance: {liq_dist_str})"
        )

        return PositionRisk(
            coin=coin,
            risk_level=risk_level,
            health_score=health_score,
            liquidation_price=liquidation_price,
            current_price=current_price,
            liquidation_distance_pct=distance_pct,
            liquidation_distance_usd=distance_usd,
            size=size,
            entry_price=position_data["entry_price"],
            position_value=position_data["position_value"],
            unrealized_pnl=position_data["unrealized_pnl"],
            leverage=position_data["leverage_value"],
            leverage_type=position_data["leverage_type"],
            warnings=warnings,
            recommendations=recommendations,
        )

    def assess_portfolio_risk(
        self,
        positions: list[dict[str, Any]],
        margin_summary: dict[str, float],
        prices: dict[str, float],
    ) -> PortfolioRisk:
        """
        Assess risk for entire portfolio.

        Args:
            positions: List of position dicts from account_service
            margin_summary: Margin summary from account_service
            prices: Dict of {coin: current_price}

        Returns:
            PortfolioRisk dataclass with portfolio-wide assessment
        """
        account_value = margin_summary["account_value"]
        total_margin_used = margin_summary["total_margin_used"]
        margin_utilization_pct = (
            (total_margin_used / account_value * 100) if account_value > 0 else 0
        )
        available_margin = account_value - total_margin_used

        # Assess each position
        position_risks = []
        for pos in positions:
            position_data = pos["position"]
            coin = position_data["coin"]
            current_price = prices.get(coin, position_data.get("entry_price", 0))

            risk = self.assess_position_risk(position_data, current_price, margin_utilization_pct)
            position_risks.append(risk)

        # Count positions by risk level
        positions_by_risk = {
            "SAFE": 0,
            "LOW": 0,
            "MODERATE": 0,
            "HIGH": 0,
            "CRITICAL": 0,
        }
        critical_positions = []
        high_risk_positions = []

        for risk in position_risks:
            positions_by_risk[risk.risk_level.value] += 1

            if risk.risk_level == RiskLevel.CRITICAL:
                critical_positions.append(risk.coin)
            elif risk.risk_level == RiskLevel.HIGH:
                high_risk_positions.append(risk.coin)

        # Determine overall risk level
        # For CROSS MARGIN positions, use Cross Margin Ratio (official Hyperliquid metric)
        cross_margin_ratio_pct = margin_summary.get("cross_margin_ratio_pct")

        if cross_margin_ratio_pct is not None:
            # Use Cross Margin Ratio as PRIMARY risk metric for cross positions
            # This is the official Hyperliquid metric (liquidation at 100%)
            overall_risk = self.determine_risk_level_from_margin_ratio(cross_margin_ratio_pct)
            logger.debug(
                f"Using Cross Margin Ratio for overall risk: {cross_margin_ratio_pct:.2f}% "
                f"→ {overall_risk.value}"
            )
        else:
            # Fallback: use worst position risk (for isolated margin or no data)
            if positions_by_risk["CRITICAL"] > 0:
                overall_risk = RiskLevel.CRITICAL
            elif positions_by_risk["HIGH"] > 0:
                overall_risk = RiskLevel.HIGH
            elif positions_by_risk["MODERATE"] > 0:
                overall_risk = RiskLevel.MODERATE
            elif positions_by_risk["LOW"] > 0:
                overall_risk = RiskLevel.LOW
            else:
                overall_risk = RiskLevel.SAFE

        # Derive overall health score
        overall_health = self.derive_health_score(overall_risk)

        # Generate portfolio warnings
        warnings = []

        # Cross Margin Ratio warnings (official Hyperliquid metric)
        if cross_margin_ratio_pct is not None:
            if cross_margin_ratio_pct >= 90:
                warnings.append(
                    f"🚨 CRITICAL: Cross Margin Ratio at {cross_margin_ratio_pct:.1f}% "
                    f"(Liquidation at 100%!)"
                )
            elif cross_margin_ratio_pct >= 70:
                warnings.append(
                    f"⚠️ HIGH RISK: Cross Margin Ratio at {cross_margin_ratio_pct:.1f}% "
                    f"(Liquidation at 100%)"
                )
            elif cross_margin_ratio_pct >= 50:
                warnings.append(f"⚠️ MODERATE: Cross Margin Ratio at {cross_margin_ratio_pct:.1f}%")

        if critical_positions:
            warnings.append(
                f"🚨 {len(critical_positions)} position(s) at CRITICAL risk: {', '.join(critical_positions)}"
            )
        if high_risk_positions:
            warnings.append(
                f"⚠️ {len(high_risk_positions)} position(s) at HIGH risk: {', '.join(high_risk_positions)}"
            )
        if margin_utilization_pct > 85:
            warnings.append(f"⚠️ High margin utilization: {margin_utilization_pct:.1f}%")

        # Generate portfolio recommendations
        recommendations = []
        if critical_positions:
            recommendations.append("💡 Immediately close or reduce CRITICAL positions")
        if high_risk_positions:
            recommendations.append("💡 Monitor HIGH risk positions closely")
        if margin_utilization_pct > 70:
            recommendations.append("💡 Consider reducing overall position sizes")

        logger.info(
            f"Portfolio risk: {overall_risk.value} "
            f"({len(positions)} positions, {margin_utilization_pct:.1f}% margin used)"
        )

        return PortfolioRisk(
            overall_risk_level=overall_risk,
            overall_health_score=overall_health,
            position_count=len(positions),
            positions_by_risk=positions_by_risk,
            account_value=account_value,
            total_margin_used=total_margin_used,
            margin_utilization_pct=margin_utilization_pct,
            available_margin=available_margin,
            critical_positions=critical_positions,
            high_risk_positions=high_risk_positions,
            warnings=warnings,
            recommendations=recommendations,
        )


# Singleton instance
risk_calculator = RiskCalculator()
