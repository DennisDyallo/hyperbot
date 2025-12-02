"""Position display orchestrator - Complete position monitoring views.

Manages position list and detail views with risk assessment, performance metrics,
and scenario analysis.
"""

from typing import Any

from src.bot.components.cards import InfoCard
from src.bot.components.formatters import (
    format_coin_size,
    format_currency,
    format_pnl,
)
from src.bot.components.lists import SortOption, build_position_list_text
from src.bot.components.risk import (
    RISK_EMOJIS,
    RiskLevel,
    calculate_risk_level,
)


class PositionDisplay:
    """Orchestrate position list and detail displays.

    Provides two view modes:
    - List view: All positions with sorting/filtering
    - Detail view: Single position with full risk analysis

    Example:
        >>> display = PositionDisplay()
        >>> message = display.build_list_view(positions, sort_by=SortOption.RISK)
    """

    @staticmethod
    def build_list_view(
        positions: list[dict[str, Any]],
        sort_by: SortOption = SortOption.RISK,
    ) -> str:
        """Build list view of all positions.

        Shows header with totals, position list, and risk summary footer.

        Args:
            positions: List of position dictionaries
            sort_by: Sort option (RISK, SIZE, PNL, NAME)

        Returns:
            Formatted position list message
        """
        # Calculate summary metrics
        total_value = sum(abs(p["position_value"]) for p in positions)
        total_pnl = sum(p["unrealized_pnl"] for p in positions)
        total_pnl_pct = (total_pnl / total_value * 100) if total_value > 0 else 0

        # Count risk factors
        high_risk_count = sum(
            1
            for p in positions
            if calculate_risk_level(p["liquidation_distance_pct"], p.get("leverage", 1), False)
            in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EXTREME]
        )
        no_sl_count = sum(1 for p in positions if not p.get("has_stop_loss", False))

        # Build header
        header = [
            "📊 **Your Positions**",
            f"Total Value: {format_currency(total_value)}",
            f"Total PnL: {format_pnl(total_pnl, total_pnl_pct)[0]}",
            "",
        ]

        # Build position list (using Level 2 preset)
        position_list = build_position_list_text(positions, sort_by=sort_by)

        # Build footer with risk warnings
        footer: list[str] = []
        if high_risk_count > 0 or no_sl_count > 0:
            footer.append("\n━━━━━━━━━━━━━━━━━")
            footer.append("⚠️ **Risk Summary:**")
            if no_sl_count > 0:
                footer.append(f"• {no_sl_count} position(s) without stop loss")
            if high_risk_count > 0:
                footer.append(f"• {high_risk_count} position(s) with HIGH risk")

        return "\n".join(header) + "\n" + position_list + "\n".join(footer)

    @staticmethod
    def build_detail_view(position: dict[str, Any]) -> str:
        """Build detailed view for single position.

        Includes position info, performance metrics, leverage details,
        risk assessment, stop loss status, and scenario analysis.

        Args:
            position: Position dictionary with all details

        Returns:
            Formatted detailed position view
        """
        # Position Info Card
        info_card = InfoCard("POSITION INFO", "💰")
        info_card.add_field("Coin", position["coin"])
        side_emoji = "🟢" if position["size"] > 0 else "🔴"
        info_card.add_field("Side", f"{position['side']} {side_emoji}")
        info_card.add_field("Size", format_coin_size(abs(position["size"]), position["coin"]))
        info_card.add_field("Entry Price", format_currency(position["entry_price"]))
        info_card.add_field("Current Price", format_currency(position["current_price"]))
        info_card.add_field("Position Value", format_currency(position["position_value"]))

        # Performance Card
        pnl_result = format_pnl(position["unrealized_pnl"], position["pnl_pct"])
        pnl_str = pnl_result[0]
        pnl_emoji = pnl_result[1]
        perf_card = InfoCard("PERFORMANCE", "📈")
        perf_card.add_field("Unrealized PnL", pnl_str, pnl_emoji)
        perf_card.add_field("ROI", f"{position['roi']:.1f}%")
        perf_card.add_field("Price Change", f"{position['price_change_pct']:.1f}%")

        # Leverage & Margin Card
        lev_card = InfoCard("LEVERAGE & MARGIN", "⚡")
        lev_card.add_field("Leverage", f"{position['leverage']}x")
        lev_card.add_field("Margin Used", format_currency(position["margin_used"]))
        lev_card.add_field("Margin Type", position["margin_type"].title())

        # Risk Metrics Card
        risk_level = calculate_risk_level(
            position["liquidation_distance_pct"], position["leverage"], False
        )
        risk_emoji = RISK_EMOJIS[risk_level]
        risk_card = InfoCard("RISK METRICS", "🎯")
        risk_card.add_field("Liquidation Price", format_currency(position["liquidation_price"]))
        risk_card.add_field(
            "Distance",
            f"{position['liquidation_distance_pct']:.1f}% (from current)",
        )
        price_buffer = abs(position["current_price"] - position["liquidation_price"])
        risk_card.add_field("Safety Buffer", f"{format_currency(price_buffer)} price drop")
        risk_card.add_field("Risk Level", f"{risk_level.name} {risk_emoji}")

        # Stop Loss Card
        sl_card = InfoCard("STOP LOSS", "🛡️")
        if position.get("has_stop_loss"):
            sl_card.add_field("Active SL", f"{format_currency(position['stop_loss_price'])} ✅")
            sl_card.add_field("Trigger", f"{position['stop_loss_distance_pct']:.1f}% from current")
            sl_card.add_field("Potential Loss", format_currency(position["potential_loss_at_sl"]))
            sl_card.add_field("Order ID", f"#{position['stop_loss_order_id']}")
        else:
            sl_card.add_field("Status", "No stop loss set ❌")

        # Scenarios
        scenarios = PositionDisplay._build_scenarios(position)

        # Combine all parts
        parts = [
            f"📊 **{position['coin']} {position['side']} Position Details**\n",
            info_card.render(),
            perf_card.render(),
            lev_card.render(),
            risk_card.render(),
            sl_card.render(),
            scenarios,
        ]

        return "\n\n".join(parts)

    @staticmethod
    def _build_scenarios(position: dict[str, Any]) -> str:
        """Build scenario analysis for position.

        Calculates PnL at various price targets (+/-5%, +/-10%, liquidation).

        Args:
            position: Position dictionary

        Returns:
            Formatted scenario analysis card
        """
        scenarios = InfoCard("SCENARIOS", "💡")

        # Price points
        current = position["current_price"]
        entry = position["entry_price"]
        liq = position["liquidation_price"]

        # Calculate scenarios
        up_5 = current * 1.05
        up_10 = current * 1.10
        down_5 = current * 0.95
        down_10 = current * 0.90

        position_size = abs(position["size"])
        side_multiplier = 1 if position["side"].upper() == "LONG" else -1

        # Build scenario text
        scenario_text = (
            f"If {position['coin']} reaches:\n"
            f"• {format_currency(up_5)} (+5%): "
            f"{format_currency((up_5 - entry) * position_size * side_multiplier)} PnL\n"
            f"• {format_currency(up_10)} (+10%): "
            f"{format_currency((up_10 - entry) * position_size * side_multiplier)} PnL\n"
            f"• {format_currency(down_5)} (-5%): "
            f"{format_currency((down_5 - entry) * position_size * side_multiplier)} PnL\n"
            f"• {format_currency(down_10)} (-10%): "
            f"{format_currency((down_10 - entry) * position_size * side_multiplier)} PnL\n"
            f"• {format_currency(liq)} (liq): 💀 LIQUIDATED"
        )

        scenarios.add_field("", scenario_text)

        return scenarios.render()
