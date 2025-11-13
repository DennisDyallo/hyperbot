"""
Account health message formatter for Telegram bot.

Formats comprehensive account health information following the UX design
specified in docs/preliminary-ux-plan.md.
"""

from datetime import UTC, datetime

from src.bot.formatters.progress_bar import build_progress_bar, get_risk_emoji
from src.use_cases.portfolio.risk_analysis import RiskAnalysisResponse


def format_account_health_message(risk_data: RiskAnalysisResponse) -> str:
    """
    Format account health message with risk indicators.

    Follows the 4-section layout from preliminary-ux-plan.md:
    1. Critical Alert Banner (conditional)
    2. Health Overview
    3. Margin Breakdown
    4. Position Risk Summary

    Args:
        risk_data: Risk analysis response from use case

    Returns:
        HTML-formatted message string

    Design Reference:
        docs/preliminary-ux-plan.md - Sections 4-7
    """
    # Get emoji for risk level
    risk_emoji = get_risk_emoji(risk_data.overall_risk_level)

    # Build health score bar
    health_bar = build_progress_bar(risk_data.portfolio_health_score)

    # Build cross margin ratio bar (handle None case)
    margin_bar = (
        build_progress_bar(risk_data.cross_margin_ratio_pct)
        if risk_data.cross_margin_ratio_pct is not None
        else build_progress_bar(0)
    )

    # Start building message
    message_parts = []

    # Section 1: Critical Alert Banner (conditional)
    # Handle None case for cross_margin_ratio_pct in comparison
    if (risk_data.cross_margin_ratio_pct or 0) >= 50 or risk_data.critical_positions > 0:
        message_parts.append(_build_critical_alert(risk_data))

    # Section 2: Health Overview
    message_parts.append(_build_health_overview(risk_data, health_bar, risk_emoji))

    # Section 3: Margin Breakdown
    message_parts.append(_build_margin_breakdown(risk_data, margin_bar, risk_emoji))

    # Section 4: Position Risk Summary
    message_parts.append(_build_position_summary(risk_data))

    # Footer
    message_parts.append(_build_footer())

    return "\n".join(message_parts)


def _build_critical_alert(risk_data: RiskAnalysisResponse) -> str:
    """Build critical alert banner section."""
    alert = "🚨 <b>CRITICAL ALERT</b> 🚨\n\n"

    # Handle None case for cross_margin_ratio_pct formatting
    margin_ratio = risk_data.cross_margin_ratio_pct or 0.0
    alert += f"Cross Margin Ratio: <b>{margin_ratio:.1f}%</b>\n"
    alert += "⚠️ Liquidation occurs at 100%!\n"

    if risk_data.critical_positions > 0:
        alert += f"\n📍 {risk_data.critical_positions} position(s) at CRITICAL risk\n"

        # List first 3 critical positions
        critical_count = 0
        for pos in risk_data.positions:
            if pos.risk_level == "CRITICAL" and critical_count < 3:
                # Handle None case for liquidation_distance_pct
                liq_dist = pos.liquidation_distance_pct or 0.0
                alert += f"• {pos.coin}: {liq_dist:.1f}% from liquidation\n"
                critical_count += 1

    alert += "\n💡 <b>Immediate action required:</b>\n"
    alert += "→ Close positions or add margin NOW\n"
    alert += "→ Reduce leverage to avoid liquidation\n"
    alert += "\n───────────────────────────\n"

    return alert


def _build_health_overview(
    risk_data: RiskAnalysisResponse, health_bar: str, risk_emoji: str
) -> str:
    """Build health overview section."""
    section = "📊 <b>Account Health</b>\n\n"
    section += f"<b>Health Score: {risk_data.portfolio_health_score}/100</b> {risk_emoji}\n"
    section += f"Risk Level: <b>{risk_data.overall_risk_level}</b>\n\n"
    section += f"{health_bar} {risk_data.portfolio_health_score}%\n\n"

    section += "<b>Total Account Value</b>\n"
    section += f"💰 ${risk_data.account_value:,.2f}\n"
    section += f"├─ Perps: ${risk_data.perps_value:,.2f}\n"
    section += f"└─ Spot: ${risk_data.spot_value:,.2f}\n\n"
    section += "───────────────────────────\n"

    return section


def _build_margin_breakdown(
    risk_data: RiskAnalysisResponse, margin_bar: str, risk_emoji: str
) -> str:
    """Build margin breakdown section."""
    section = "📊 <b>Margin & Leverage</b>\n\n"

    # Handle None case for cross margin ratio
    margin_ratio = risk_data.cross_margin_ratio_pct or 0.0

    section += f"<b>Cross Margin Ratio:</b> <code>{margin_ratio:.1f}%</code> {risk_emoji}\n"
    section += f"{margin_bar} {margin_ratio:.1f}%\n"

    # Add warning based on margin ratio
    if margin_ratio >= 70:
        section += "🚨 DANGER: Liquidation at 100%!\n"
    elif margin_ratio >= 50:
        section += "⚠️ Warning: Approaching danger zone (70%)\n"

    section += "\n<b>Margin Usage</b>\n"
    section += f"• Used: <code>${risk_data.total_margin_used:,.2f}</code>\n"
    section += f"• Available: <code>${risk_data.available_margin:,.2f}</code>\n"
    section += f"• Total: <code>${risk_data.account_value:,.2f}</code>\n\n"

    section += "───────────────────────────\n"

    return section


def _build_position_summary(risk_data: RiskAnalysisResponse) -> str:
    """Build position risk summary section."""
    section = "📊 <b>Position Risk Breakdown</b>\n\n"

    num_positions = len(risk_data.positions)
    section += f"<b>{num_positions} Active Position(s)</b>\n\n"

    section += "Risk Distribution:\n"

    # Count positions by risk level
    risk_counts = {"SAFE": 0, "LOW": 0, "MODERATE": 0, "HIGH": 0, "CRITICAL": 0}
    for pos in risk_data.positions:
        if pos.risk_level in risk_counts:
            risk_counts[pos.risk_level] += 1

    # Show distribution with emphasis on critical
    if risk_counts["CRITICAL"] > 0:
        section += f"🔴 Critical: <b>{risk_counts['CRITICAL']} position(s)</b>\n"
    else:
        section += f"🔴 Critical: {risk_counts['CRITICAL']} positions\n"

    section += f"🟠 High: {risk_counts['HIGH']} position(s)\n"
    section += f"💛 Moderate: {risk_counts['MODERATE']} position(s)\n"
    section += f"💚 Low: {risk_counts['LOW']} position(s)\n"
    section += f"✅ Safe: {risk_counts['SAFE']} position(s)\n"

    # List critical positions with details
    if risk_counts["CRITICAL"] > 0:
        section += "\n<b>Critical Positions:</b>\n"
        for pos in risk_data.positions:
            if pos.risk_level == "CRITICAL":
                # Handle None case for liquidation_distance_pct
                liq_dist = pos.liquidation_distance_pct or 0.0
                section += f"🔴 {pos.coin} - {pos.leverage}x leverage, "
                section += f"{liq_dist:.1f}% to liq\n"

    # Add recommendations if portfolio has warnings
    if risk_data.portfolio_warnings:
        section += "\n💡 <b>Recommendations:</b>\n"
        for warning in risk_data.portfolio_warnings[:3]:  # First 3 warnings
            section += f"• {warning}\n"
    elif num_positions > 0 and risk_counts["CRITICAL"] == 0 and risk_counts["HIGH"] == 0:
        section += "\n💡 Your account is healthy!\n"

    section += "\n───────────────────────────\n"

    return section


def _build_footer() -> str:
    """Build footer with auto-refresh notice and timestamp."""
    timestamp = datetime.now(UTC).strftime("%H:%M:%S UTC")
    footer = "🔄 Auto-refreshes every 30s\n"
    footer += f"Last updated: {timestamp}"
    return footer
