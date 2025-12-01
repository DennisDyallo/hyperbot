"""Two-tier preview components for order confirmation flows.

This module provides quick and full preview builders following the two-tier
pattern: quick preview for mobile-first scannability, full preview for comprehensive analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from .cards import build_capital_impact_card, build_risk_assessment_card
from .formatters import format_coin_size, format_currency
from .risk import RiskLevel, calculate_risk_level


@dataclass
class PreviewData:
    """Data container for order preview.

    Attributes:
        coin: Trading pair (e.g., "BTC", "ETH")
        side: Order side ("BUY" or "SELL")
        amount_usd: Order size in USD
        leverage: Leverage multiplier
        entry_price: Expected entry price

        # Capital metrics
        margin_required: Required margin for order
        margin_available: Available margin in account
        buying_power_used_pct: Percentage of buying power used

        # Risk metrics
        liquidation_price: Estimated liquidation price
        liquidation_distance_pct: Distance to liquidation (positive = safe)

        # Optional fields
        size_coin: Position size in coin units
        has_stop_loss: Whether stop-loss is set
        warnings: List of warning messages
    """

    # Required fields
    coin: str
    side: str
    amount_usd: float
    leverage: int
    entry_price: float

    # Capital
    margin_required: float
    margin_available: float
    buying_power_used_pct: float

    # Risk
    liquidation_price: float
    liquidation_distance_pct: float

    # Optional
    size_coin: float | None = None
    has_stop_loss: bool = False
    warnings: list[str] = field(default_factory=list)


class PreviewBuilder:
    """Build two-tier previews (quick + full).

    Quick preview: Mobile-optimized, fits on one screen, essential info only
    Full preview: Comprehensive analysis with cards, scenarios, and warnings
    """

    # Visual constants
    HEADER_EMOJI: Final[dict[str, str]] = {"BUY": "🟢", "SELL": "🔴"}

    @staticmethod
    def build_quick_preview(data: PreviewData) -> str:
        """Build mobile-optimized quick preview.

        Shows only essential information in compact format.
        Goal: User can make informed decision without scrolling.

        Args:
            data: Preview data container

        Returns:
            Formatted quick preview text

        Example:
            >>> data = PreviewData(...)
            >>> preview = PreviewBuilder.build_quick_preview(data)
            >>> print(preview)
            📋 **Order Preview**

            💰 BTC BUY 🟢: $1,000.00 @ market
            ⚡ Leverage: 5x
            📊 Margin: $200.00 / $5,200.00 available
            🎯 Liquidation: $45,000.00 (10.0% away)
            ⚠️ Risk: CRITICAL 🔴
        """
        side_emoji = PreviewBuilder.HEADER_EMOJI.get(data.side, "⚪")
        risk_level = calculate_risk_level(
            data.liquidation_distance_pct, data.leverage, data.has_stop_loss
        )

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

        lines = [
            "📋 **Order Preview**\n",
            f"💰 {data.coin} {data.side} {side_emoji}: {format_currency(data.amount_usd)} @ market",
            f"⚡ Leverage: {data.leverage}x",
            f"📊 Margin: {format_currency(data.margin_required)} / {format_currency(data.margin_available)} available",
            f"🎯 Liquidation: {format_currency(data.liquidation_price)} ({abs(data.liquidation_distance_pct):.1f}% away)",
            f"⚠️ Risk: {risk_level.value.upper()} {risk_emoji}",
        ]

        return "\n".join(lines)

    @staticmethod
    def build_full_preview(data: PreviewData) -> str:
        """Build comprehensive preview with all details.

        Includes header, capital impact card, risk assessment card,
        additional details, and warnings.

        Args:
            data: Preview data container

        Returns:
            Formatted full preview text

        Example:
            >>> data = PreviewData(...)
            >>> preview = PreviewBuilder.build_full_preview(data)
            # Returns multi-section comprehensive analysis
        """
        side_emoji = PreviewBuilder.HEADER_EMOJI.get(data.side, "⚪")

        # Header section
        header = [
            "📋 **Complete Order Analysis**\n",
            f"Coin: {data.coin}",
            f"Side: {data.side} {side_emoji}",
            f"Amount: {format_currency(data.amount_usd)}",
            f"Leverage: {data.leverage}x ⚡\n",
        ]

        # Capital Impact Card
        capital_card = build_capital_impact_card(
            data.margin_required, data.margin_available, data.buying_power_used_pct
        )

        # Risk Assessment Card
        risk_card = build_risk_assessment_card(
            data.entry_price,
            data.liquidation_price,
            data.liquidation_distance_pct,
            data.leverage,
            data.has_stop_loss,
        )

        # Additional Information
        additional = []
        if data.size_coin is not None:
            additional.append(f"Position Size: {format_coin_size(data.size_coin, data.coin)}")
        additional.append(f"Total Exposure: {format_currency(data.amount_usd)}")

        # Warnings section
        warning_lines = []
        if data.warnings:
            warning_lines.append("\n⚠️ **Warnings**:")
            for warning in data.warnings:
                warning_lines.append(f"• {warning}")

        # Combine all sections
        parts = [
            "\n".join(header),
            capital_card.render(),
            risk_card.render(),
            "\n".join(additional),
        ]

        if warning_lines:
            parts.append("\n".join(warning_lines))

        return "\n\n".join(parts)


def build_order_preview(data: PreviewData, tier: str = "quick") -> str:
    """Convenience function to build preview by tier.

    Args:
        data: Preview data container
        tier: "quick" for mobile-optimized or "full" for comprehensive

    Returns:
        Formatted preview text

    Raises:
        ValueError: If tier is not "quick" or "full"
    """
    if tier == "quick":
        return PreviewBuilder.build_quick_preview(data)
    elif tier == "full":
        return PreviewBuilder.build_full_preview(data)
    else:
        raise ValueError(f"Invalid tier: {tier}. Must be 'quick' or 'full'")
