"""
Risk assessment utilities for position and order evaluation.

Provides standardized risk levels, emojis, and calculation logic to ensure
consistent risk communication across all bot interactions.
"""

from enum import Enum
from typing import Final


class RiskLevel(str, Enum):
    """
    Standardized risk levels for positions and orders.

    Used throughout the bot to communicate risk in a consistent way.
    Each level has an associated emoji and color scheme.
    """

    SAFE = "SAFE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EXTREME = "EXTREME"


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

# Emoji mapping for each risk level
RISK_EMOJIS: Final[dict[RiskLevel, str]] = {
    RiskLevel.SAFE: "🟢",
    RiskLevel.LOW: "🟢",
    RiskLevel.MODERATE: "🟡",
    RiskLevel.HIGH: "🟠",
    RiskLevel.CRITICAL: "🔴",
    RiskLevel.EXTREME: "💀",
}


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
    """
    Get the emoji representation for a risk level.

    Args:
        level: The risk level.

    Returns:
        Emoji string (e.g., "🟢", "🔴", "💀").

    Examples:
        >>> get_risk_emoji(RiskLevel.SAFE)
        '🟢'
        >>> get_risk_emoji(RiskLevel.MODERATE)
        '🟡'
        >>> get_risk_emoji(RiskLevel.EXTREME)
        '💀'
    """
    return RISK_EMOJIS[level]


def format_risk_indicator(level: RiskLevel, include_emoji: bool = True) -> str:
    """
    Format a complete risk indicator with emoji and text.

    Args:
        level: The risk level.
        include_emoji: Whether to include the emoji (default: True).

    Returns:
        Formatted string like "MODERATE 🟡" or "EXTREME 💀".

    Examples:
        >>> format_risk_indicator(RiskLevel.MODERATE)
        'MODERATE 🟡'
        >>> format_risk_indicator(RiskLevel.EXTREME)
        'EXTREME 💀'
        >>> format_risk_indicator(RiskLevel.SAFE, include_emoji=False)
        'SAFE'
    """
    text = level.value

    if include_emoji:
        emoji = get_risk_emoji(level)
        return f"{text} {emoji}"

    return text
