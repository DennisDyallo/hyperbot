"""Risk assessment utilities for consistent risk messaging."""

from dataclasses import dataclass
from enum import Enum
from typing import Final


class RiskLevel(str, Enum):
    """Standardized risk levels for positions and orders."""

    SAFE = "SAFE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EXTREME = "EXTREME"


@dataclass(frozen=True)
class RiskDescriptor:
    """Descriptor metadata for a risk level."""

    level: RiskLevel
    name: str
    emoji: str
    severity: int  # 1 (safest) to 6 (extreme)
    summary: str
    tooltip: str


# Risk level thresholds (liquidation distance in percentage)
RISK_THRESHOLDS: Final[dict[str, float]] = {
    "EXTREME": 5.0,  # < 5% to liquidation
    "CRITICAL": 10.0,  # < 10% to liquidation
    "HIGH": 15.0,  # < 15% to liquidation
    "MODERATE": 25.0,  # < 25% to liquidation
    "LOW": 40.0,  # < 40% to liquidation
    # >= 40% is SAFE
}

# Leverage multipliers for risk calculation
LEVERAGE_RISK_MULTIPLIERS: Final[dict[int, float]] = {
    1: 1.0,
    3: 1.2,
    5: 1.5,
    10: 2.0,
    20: 3.0,
}

RISK_DESCRIPTORS: Final[dict[RiskLevel, RiskDescriptor]] = {
    RiskLevel.SAFE: RiskDescriptor(
        level=RiskLevel.SAFE,
        name="Safe",
        emoji="🟢",
        severity=1,
        summary="Large buffer – minimal liquidation risk.",
        tooltip="Liquidation more than 40% away. Comfortable margin headroom.",
    ),
    RiskLevel.LOW: RiskDescriptor(
        level=RiskLevel.LOW,
        name="Low",
        emoji="🟢",
        severity=2,
        summary="Healthy distance with room for volatility.",
        tooltip="Liquidation 25-40% away. Typical for conservative leverage.",
    ),
    RiskLevel.MODERATE: RiskDescriptor(
        level=RiskLevel.MODERATE,
        name="Moderate",
        emoji="🟡",
        severity=3,
        summary="Balanced risk – monitor if volatility rises.",
        tooltip="Liquidation 15-25% away. Normal for 3-5x leverage; consider stop-loss protection.",
    ),
    RiskLevel.HIGH: RiskDescriptor(
        level=RiskLevel.HIGH,
        name="High",
        emoji="🟠",
        severity=4,
        summary="Tight buffer – size or leverage may be aggressive.",
        tooltip="Liquidation 10-15% away. Elevated risk; reduce position or add margin.",
    ),
    RiskLevel.CRITICAL: RiskDescriptor(
        level=RiskLevel.CRITICAL,
        name="Critical",
        emoji="🔴",
        severity=5,
        summary="Liquidation nearby – action recommended immediately.",
        tooltip="Liquidation 5-10% away. One swift move can trigger liquidation.",
    ),
    RiskLevel.EXTREME: RiskDescriptor(
        level=RiskLevel.EXTREME,
        name="Extreme",
        emoji="💀",
        severity=6,
        summary="Liquidation imminent – intervene now.",
        tooltip="<5% to liquidation. Immediate intervention required.",
    ),
}

# Emoji mapping for each risk level
RISK_EMOJIS: Final[dict[RiskLevel, str]] = {
    level: descriptor.emoji for level, descriptor in RISK_DESCRIPTORS.items()
}


def get_risk_descriptor(level: RiskLevel) -> RiskDescriptor:
    """Return descriptor metadata for a risk level."""

    return RISK_DESCRIPTORS[level]


def calculate_risk_level(
    liquidation_distance_pct: float,
    leverage: int,
    has_stop_loss: bool = False,
) -> RiskLevel:
    """
    Calculate risk level based on liquidation distance and leverage.

    Risk increases with:
        - Closer liquidation price (lower distance %)
        - Higher leverage
        - No stop loss protection

    Args:
        liquidation_distance_pct: Distance to liquidation as positive percentage
            (e.g., 20.0 means 20% away from liquidation).
        leverage: The leverage multiplier (1x, 3x, 5x, etc.).
        has_stop_loss: Whether position has stop loss protection.

    Returns:
        RiskLevel enum value.

    Examples:
        >>> calculate_risk_level(3.0, 10)  # 3% away, 10x leverage
        <RiskLevel.EXTREME: 'EXTREME'>
        >>> calculate_risk_level(8.0, 5)  # 8% away, 5x leverage
        <RiskLevel.CRITICAL: 'CRITICAL'>
        >>> calculate_risk_level(22.0, 3)  # 22% away, 3x leverage
        <RiskLevel.MODERATE: 'MODERATE'>
        >>> calculate_risk_level(45.0, 1)  # 45% away, 1x leverage
        <RiskLevel.SAFE: 'SAFE'>
    """
    # Get leverage multiplier (default to 1.5x if not in map)
    leverage_multiplier = LEVERAGE_RISK_MULTIPLIERS.get(leverage, 1.5)

    # Adjust distance by leverage (higher leverage = effectively closer to liq)
    adjusted_distance = liquidation_distance_pct / leverage_multiplier

    # Determine base risk level
    if adjusted_distance < RISK_THRESHOLDS["EXTREME"]:
        risk = RiskLevel.EXTREME
    elif adjusted_distance < RISK_THRESHOLDS["CRITICAL"]:
        risk = RiskLevel.CRITICAL
    elif adjusted_distance < RISK_THRESHOLDS["HIGH"]:
        risk = RiskLevel.HIGH
    elif adjusted_distance < RISK_THRESHOLDS["MODERATE"]:
        risk = RiskLevel.MODERATE
    elif adjusted_distance < RISK_THRESHOLDS["LOW"]:
        risk = RiskLevel.LOW
    else:
        risk = RiskLevel.SAFE

    # Upgrade risk if no stop loss protection (except SAFE positions)
    if not has_stop_loss and risk != RiskLevel.SAFE:
        risk_order = [
            RiskLevel.SAFE,
            RiskLevel.LOW,
            RiskLevel.MODERATE,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
            RiskLevel.EXTREME,
        ]
        current_index = risk_order.index(risk)
        # Move up one level (e.g., LOW -> MODERATE)
        if current_index < len(risk_order) - 1:
            risk = risk_order[current_index + 1]

    return risk


def get_risk_emoji(level: RiskLevel) -> str:
    """Return emoji representation for a risk level."""

    return RISK_DESCRIPTORS[level].emoji


def format_risk_indicator(level: RiskLevel, include_emoji: bool = True) -> str:
    """Format a risk indicator using descriptor metadata."""

    descriptor = get_risk_descriptor(level)
    text = descriptor.name.upper()

    if include_emoji:
        return f"{text} {descriptor.emoji}"

    return text


def build_risk_summary(level: RiskLevel) -> str:
    """Return the short summary string for a risk level."""

    return get_risk_descriptor(level).summary


def build_risk_tooltip(level: RiskLevel) -> str:
    """Return the tooltip string for a risk level."""

    return get_risk_descriptor(level).tooltip
