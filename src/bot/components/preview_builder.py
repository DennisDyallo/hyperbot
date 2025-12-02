"""
Preview message builders for order confirmations.

This module provides helper functions that build formatted preview messages
for order confirmations. These are building blocks that return text strings,
not orchestrators that control message flow.

Design Philosophy:
- Return formatted text, don't edit messages
- Accept all parameters explicitly (no context access)
- Pure functions for easy testing
- Support multiple preview modes (quick vs full)
"""

from src.bot.utils import format_coin_amount, format_usd_amount
from src.config import settings


def build_order_preview(
    *,
    coin: str,
    side: str,  # "BUY" or "SELL"
    usd_amount: float,
    coin_size: float,
    price: float,
    order_type: str = "Market",  # "Market" or "Limit"
    leverage: int | None = None,
    margin_required: float | None = None,
    liquidation_price: float | None = None,
    risk_level: str | None = None,
    limit_price: float | None = None,
) -> str:
    """
    Build order preview message with all relevant details.

    This replaces the duplicated confirmation message that appears in both
    amount_selected and amount_text_input handlers.

    Args:
        coin: Trading pair symbol (e.g., "BTC", "ETH")
        side: Order side ("BUY" or "SELL")
        usd_amount: USD value of the order
        coin_size: Size of the order in coin units
        price: Current or entry price
        order_type: "Market" or "Limit"
        leverage: Leverage multiplier (e.g., 5 for 5x)
        margin_required: Margin required for leveraged position
        liquidation_price: Estimated liquidation price
        risk_level: Risk assessment ("LOW", "MODERATE", "HIGH", "EXTREME")
        limit_price: Limit order price (if order_type == "Limit")

    Returns:
        Formatted preview message text

    Example:
        >>> preview = build_order_preview(
        ...     coin="BTC",
        ...     side="BUY",
        ...     usd_amount=1000.0,
        ...     coin_size=0.01015,
        ...     price=98500.0,
        ...     leverage=5,
        ...     margin_required=200.0,
        ...     liquidation_price=78800.0,
        ...     risk_level="MODERATE"
        ... )
    """
    side_emoji = "🟢" if side == "BUY" else "🔴"

    # Header
    text_lines = [
        f"{side_emoji} **Confirm {order_type} Order**\n",
        f"**Coin**: {coin}",
        f"**Side**: {side}",
        f"**USD Amount**: {format_usd_amount(usd_amount)}",
        f"**Coin Size**: {format_coin_amount(coin_size, coin)}",
    ]

    # Price info
    if limit_price is not None:
        text_lines.append(f"**Limit Price**: ${limit_price:,.2f}")
        text_lines.append(f"**Current Price**: ${price:,.2f}")
        pct_diff = ((limit_price - price) / price) * 100
        text_lines.append(f"**Difference**: {pct_diff:+.2f}%")
    else:
        text_lines.append(f"**Current Price**: ${price:,.2f}")

    # Leverage and risk info (if provided)
    if leverage is not None:
        text_lines.append(f"\n**⚡ Leverage**: {leverage}x")

        if margin_required is not None:
            text_lines.append(f"**📊 Margin Required**: {format_usd_amount(margin_required)}")

        if liquidation_price is not None:
            liq_distance = ((liquidation_price - price) / price) * 100
            text_lines.append(
                f"**🎯 Est. Liquidation**: ${liquidation_price:,.2f} ({liq_distance:+.1f}%)"
            )

        if risk_level is not None:
            risk_emoji = {"LOW": "🟢", "MODERATE": "🟡", "HIGH": "🟠", "EXTREME": "🔴"}.get(
                risk_level, "⚪"
            )
            text_lines.append(f"**⚠️ Risk Level**: {risk_level} {risk_emoji}")

    # Warnings
    text_lines.append("")
    if order_type == "Market":
        text_lines.append("⚠️ Market order will execute at best available price.")
        text_lines.append("Slippage may occur.")
    elif order_type == "Limit":
        text_lines.append("⚠️ Limit order will only fill at specified price or better.")
        text_lines.append("Order may not fill if price is not reached.")

    # Environment indicator
    env_text = "🧪 Testnet" if settings.HYPERLIQUID_TESTNET else "🚀 Mainnet"
    text_lines.append(f"\n_Environment: {env_text}_")

    return "\n".join(text_lines)


def build_quick_order_preview(
    *,
    coin: str,
    side: str,  # "BUY" or "SELL"
    usd_amount: float,
    price: float,
    order_type: str = "Market",  # "Market" or "Limit"
    leverage: int | None = None,
    margin_required: float | None = None,
    margin_available: float | None = None,
    liquidation_price: float | None = None,
    risk_level: str | None = None,
    limit_price: float | None = None,
) -> str:
    """
    Build mobile-optimized quick preview (Phase 7 two-tier preview system).

    This is the default preview shown to users - fits on one screen without
    scrolling. Users can optionally expand to full details.

    Args:
        coin: Trading pair symbol
        side: "BUY" or "SELL"
        usd_amount: USD value
        price: Current or limit price
        order_type: "Market" or "Limit"
        leverage: Leverage multiplier
        margin_required: Margin needed
        margin_available: Total margin available
        liquidation_price: Estimated liquidation price
        risk_level: "LOW", "MODERATE", "HIGH", "EXTREME"
        limit_price: Limit price (for limit orders)

    Returns:
        Compact, mobile-friendly preview text

    Example:
        Quick Preview:
        📋 Order Preview

        💰 BTC BUY: $1,000 @ market
        ⚡ Leverage: 5x
        📊 Margin: $200 / $5,200 available
        🎯 Liquidation: $78,800 (-20%)
        ⚠️ Risk: MODERATE 🟡
    """
    text_lines = ["📋 Order Preview\n"]

    # Order summary (one line)
    if limit_price is not None:
        text_lines.append(
            f"💰 {coin} {side}: {format_usd_amount(usd_amount)} @ ${limit_price:,.0f}"
        )
    else:
        text_lines.append(f"💰 {coin} {side}: {format_usd_amount(usd_amount)} @ market")

    # Leverage info (if provided)
    if leverage is not None:
        text_lines.append(f"⚡ Leverage: {leverage}x")

        if margin_required is not None and margin_available is not None:
            text_lines.append(
                f"📊 Margin: {format_usd_amount(margin_required)} / "
                f"{format_usd_amount(margin_available)} available"
            )

        if liquidation_price is not None:
            liq_distance = ((liquidation_price - price) / price) * 100
            text_lines.append(f"🎯 Liquidation: ${liquidation_price:,.0f} ({liq_distance:+.0f}%)")

        if risk_level is not None:
            risk_emoji = {"LOW": "🟢", "MODERATE": "🟡", "HIGH": "🟠", "EXTREME": "🔴"}.get(
                risk_level, "⚪"
            )
            text_lines.append(f"⚠️ Risk: {risk_level} {risk_emoji}")

    return "\n".join(text_lines)


def build_leverage_selection_message(
    *,
    coin: str,
    side: str,
    usd_amount: float,
    available_margin: float,
    leverage_levels: list[int] | None = None,
    recommended_leverage: int | None = None,
) -> str:
    """
    Build leverage selection message with buying power at each level.

    Shows context-aware recommendations based on order size and available capital.

    Args:
        coin: Trading pair symbol
        side: "BUY" or "SELL"
        usd_amount: Order size in USD
        available_margin: Total available margin
        leverage_levels: List of leverage options (default: [1, 3, 5, 10, 20])
        recommended_leverage: Suggested leverage for this order size

    Returns:
        Formatted leverage selection message

    Example:
        ⚡ Select Leverage for $1,000 BTC

        Your order: $1,000
        Available: $5,200

        1x  → $5,200 max ⚪ Conservative
        3x  → $15,600 max ✨ Good for this size
        5x  → $26,000 max 🟡 Higher risk
        10x → $52,000 max 🔴 Risky
        20x → $104,000 max 🔥 Extreme risk
    """
    if leverage_levels is None:
        leverage_levels = [1, 3, 5, 10, 20]

    text_lines = [
        f"⚡ **Select Leverage for {format_usd_amount(usd_amount)} {coin}**\n",
        f"Your order: {format_usd_amount(usd_amount)}",
        f"Available: {format_usd_amount(available_margin)}\n",
    ]

    for lev in leverage_levels:
        max_buy_power = available_margin * lev

        # Determine risk label and emoji
        if lev == 1:
            risk_label = "Conservative"
            emoji = "⚪"
        elif lev <= 3:
            risk_label = "Balanced"
            emoji = "✨" if lev == recommended_leverage else "🟢"
        elif lev <= 5:
            risk_label = "Moderate risk"
            emoji = "✨" if lev == recommended_leverage else "🟡"
        elif lev <= 10:
            risk_label = "Risky"
            emoji = "✨" if lev == recommended_leverage else "🔴"
        else:
            risk_label = "Extreme risk"
            emoji = "✨" if lev == recommended_leverage else "🔥"

        text_lines.append(f"{lev}x  → {format_usd_amount(max_buy_power)} max {emoji} {risk_label}")

    # Add context-aware tip
    if recommended_leverage:
        text_lines.append(
            f"\n💡 For {format_usd_amount(usd_amount)} orders, "
            f"{recommended_leverage}x balances opportunity and safety."
        )

    return "\n".join(text_lines)
