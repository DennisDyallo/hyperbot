"""Info card components for consistent data presentation.

This module provides reusable card components for displaying structured
information in Telegram messages with consistent formatting and visual hierarchy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .formatters import format_currency, format_percentage
from .risk import RiskLevel, calculate_risk_level


@dataclass(frozen=True)
class InfoField:
    """Single field in an info card.

    Attributes:
        label: Field label/name
        value: Formatted value to display
        emoji: Optional emoji prefix for the field
    """

    label: str
    value: str
    emoji: str = ""


class InfoCard:
    """Build formatted info cards with consistent styling.

    Cards use a header + field list pattern with separators for visual clarity.
    All cards follow consistent spacing and formatting rules.

    Example:
        >>> card = InfoCard("CAPITAL IMPACT", "💰")
        >>> card.add_field("Margin Required", "$200.00")
        >>> card.add_field("Margin Available", "$5,200.00")
        >>> print(card.render())
        ━━━━━━━━━━━━━━━━━
        💰 CAPITAL IMPACT
        ━━━━━━━━━━━━━━━━━
        Margin Required: $200.00
        Margin Available: $5,200.00
    """

    # Visual constants
    SEPARATOR: Final[str] = "━" * 25

    def __init__(self, title: str, title_emoji: str = "") -> None:
        """Initialize info card with title.

        Args:
            title: Card title (will be uppercased)
            title_emoji: Optional emoji to prefix title
        """
        self.title = f"{title_emoji} {title}".strip() if title_emoji else title
        self.fields: list[InfoField] = []

    def add_field(self, label: str, value: str, emoji: str = "") -> InfoCard:
        """Add a field to the card.

        Args:
            label: Field label
            value: Formatted value
            emoji: Optional emoji prefix

        Returns:
            Self for method chaining
        """
        self.fields.append(InfoField(label=label, value=value, emoji=emoji))
        return self

    def render(self, include_separator: bool = True) -> str:
        """Render the card as formatted text.

        Args:
            include_separator: Whether to include top/bottom separators

        Returns:
            Formatted card text
        """
        lines: list[str] = []

        if include_separator:
            lines.append(self.SEPARATOR)

        lines.append(f"**{self.title}**")

        if include_separator:
            lines.append(self.SEPARATOR)

        for field in self.fields:
            emoji_prefix = f"{field.emoji} " if field.emoji else ""
            lines.append(f"{emoji_prefix}{field.label}: {field.value}")

        return "\n".join(lines)


# Preset card builders for common use cases


def build_capital_impact_card(
    margin_required: float, margin_available: float, buying_power_used_pct: float
) -> InfoCard:
    """Build standard capital impact card.

    Displays margin usage and available capital for an order.

    Args:
        margin_required: Margin needed for the order
        margin_available: Total margin available in account
        buying_power_used_pct: Percentage of buying power used

    Returns:
        Formatted capital impact card

    Example:
        >>> card = build_capital_impact_card(200.0, 5200.0, 3.8)
        >>> print(card.render())
        ━━━━━━━━━━━━━━━━━━━━━━━━━
        💰 CAPITAL IMPACT
        ━━━━━━━━━━━━━━━━━━━━━━━━━
        Margin Required: $200.00
        Margin Available: $5,200.00
        Buying Power Used: 3.8%
    """
    card = InfoCard("CAPITAL IMPACT", "💰")
    card.add_field("Margin Required", format_currency(margin_required))
    card.add_field("Margin Available", format_currency(margin_available))
    card.add_field("Buying Power Used", format_percentage(buying_power_used_pct, show_sign=False))
    return card


def build_risk_assessment_card(
    entry_price: float,
    liquidation_price: float,
    liquidation_distance_pct: float,
    leverage: int,
    has_stop_loss: bool = False,
) -> InfoCard:
    """Build standard risk assessment card.

    Displays entry price, liquidation risk, and calculated risk level.

    Args:
        entry_price: Expected entry price
        liquidation_price: Estimated liquidation price
        liquidation_distance_pct: Distance to liquidation (positive = safe)
        leverage: Leverage multiplier
        has_stop_loss: Whether position has stop-loss protection

    Returns:
        Formatted risk assessment card

    Example:
        >>> card = build_risk_assessment_card(50000.0, 45000.0, 10.0, 5)
        >>> print(card.render())
        ━━━━━━━━━━━━━━━━━━━━━━━━━
        ⚠️ RISK ASSESSMENT
        ━━━━━━━━━━━━━━━━━━━━━━━━━
        Entry Price: $50,000.00
        Est. Liquidation: $45,000.00
        Safety Distance: 10.0% drop
        Risk Level: CRITICAL 🔴
    """
    risk_level = calculate_risk_level(liquidation_distance_pct, leverage, has_stop_loss)

    # Map risk level to emoji
    risk_emoji_map = {
        RiskLevel.SAFE: "🟢",
        RiskLevel.LOW: "🟢",
        RiskLevel.MODERATE: "🟡",
        RiskLevel.HIGH: "🟠",
        RiskLevel.CRITICAL: "🔴",
        RiskLevel.EXTREME: "💀",
    }
    risk_emoji = risk_emoji_map.get(risk_level, "⚪")

    card = InfoCard("RISK ASSESSMENT", "⚠️")
    card.add_field("Entry Price", format_currency(entry_price))
    card.add_field("Est. Liquidation", format_currency(liquidation_price))
    card.add_field("Safety Distance", f"{liquidation_distance_pct:.1f}% drop")
    card.add_field("Risk Level", f"{risk_level.value.upper()} {risk_emoji}")

    return card


def build_position_summary_card(
    coin: str,
    side: str,
    entry_price: float,
    position_value: float,
    unrealized_pnl: float,
    unrealized_pnl_pct: float,
) -> InfoCard:
    """Build position summary card.

    Displays current position details including PnL.

    Args:
        coin: Trading pair (e.g., "BTC")
        side: Position side ("LONG" or "SHORT")
        entry_price: Average entry price
        position_value: Current position value in USD
        unrealized_pnl: Unrealized profit/loss in USD
        unrealized_pnl_pct: Unrealized PnL percentage

    Returns:
        Formatted position summary card
    """
    side_emoji = "🟢" if side == "LONG" else "🔴"
    pnl_emoji = "🟢" if unrealized_pnl > 0 else "🔴" if unrealized_pnl < 0 else "⚪"

    card = InfoCard(f"{coin} {side}", side_emoji)
    card.add_field("Entry Price", format_currency(entry_price))
    card.add_field("Position Value", format_currency(abs(position_value)))
    card.add_field(
        "Unrealized PnL",
        f"{format_currency(unrealized_pnl)} ({format_percentage(unrealized_pnl_pct)})",
        pnl_emoji,
    )

    return card
