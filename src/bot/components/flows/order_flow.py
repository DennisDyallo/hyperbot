"""Order flow orchestrator - Complete market order wizard flow.

This orchestrator manages the end-to-end market order placement flow,
coordinating all Level 1 and Level 2 components into a cohesive user experience.
"""

from dataclasses import dataclass
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.components.buttons import ButtonBuilder
from src.bot.components.formatters import format_currency
from src.bot.components.loading import LoadingMessage
from src.bot.components.preview import PreviewBuilder, PreviewData
from src.bot.components.risk import (
    RISK_EMOJIS,
    RiskLevel,
    calculate_risk_level,
)


@dataclass
class OrderFlowState:
    """State container for order flow wizard.

    Tracks user selections throughout the multi-step order placement process.
    """

    coin: str | None = None
    side: str | None = None  # "buy" or "sell"
    amount_usd: float | None = None
    leverage: int | None = None
    preview_mode: str = "quick"  # "quick" or "full"


class OrderFlowOrchestrator:
    """Orchestrate complete market order placement flow.

    Manages a 6-step wizard:
    1. Coin selection
    2. Buy/Sell selection
    3. Amount entry (USD)
    4. Leverage selection (context-aware)
    5. Preview (two-tier: quick/full)
    6. Execute order

    Example:
        >>> flow = OrderFlowOrchestrator()
        >>> await flow.step_2_side_selection(update, context, "BTC")
    """

    def __init__(self) -> None:
        """Initialize order flow orchestrator."""
        self.state = OrderFlowState()

    async def step_2_side_selection(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,  # noqa: ARG002
        coin: str,
    ) -> None:
        """Step 2: Buy or Sell selection.

        Args:
            update: Telegram update
            context: Bot context
            coin: Selected trading pair (e.g., "BTC")
        """
        self.state.coin = coin

        message = f"💰 **{coin} Market Order**\n\nStep 2/5: Buy or Sell?"

        buttons = (
            ButtonBuilder()
            .action("Buy", f"order_side:buy:{coin}", style="success")
            .action("Sell", f"order_side:sell:{coin}", style="danger")
            .back()
            .cancel()
            .build()
        )

        query = update.callback_query
        if query:
            await query.edit_message_text(message, reply_markup=buttons)

    async def step_3_amount_entry(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,  # noqa: ARG002
        side: str,
    ) -> None:
        """Step 3: Enter USD amount with quick presets.

        Args:
            update: Telegram update
            context: Bot context
            side: "buy" or "sell"
        """
        self.state.side = side

        message = (
            f"💰 **{self.state.coin} {side.upper()}**\n\n"
            f"Step 3/5: Enter amount in USD\n\n"
            f"Choose a preset or enter custom:"
        )

        buttons = (
            ButtonBuilder()
            .action("$100", "amount:100")
            .action("$500", "amount:500")
            .action("$1000", "amount:1000")
            .action("Custom Amount", "amount:custom", style="secondary")
            .back()
            .cancel()
            .build()
        )

        query = update.callback_query
        if query:
            await query.edit_message_text(message, reply_markup=buttons)

    async def step_4_leverage_selection(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,  # noqa: ARG002
        amount_usd: float,
        account_value: float,
    ) -> None:
        """Step 4: Select leverage with context-aware recommendations.

        Shows buying power at each leverage level and highlights recommended options.

        Args:
            update: Telegram update
            context: Bot context
            amount_usd: Order amount in USD
            account_value: Total account value for buying power calculation
        """
        self.state.amount_usd = amount_usd

        # Show loading state
        await LoadingMessage.show(update, "account")

        # Build context-aware message
        message = (
            f"⚡ **Select Leverage for {format_currency(amount_usd)} {self.state.coin}**\n\n"
            f"Your order: {format_currency(amount_usd)}\n"
            f"Available: {format_currency(account_value)}\n\n"
        )

        # Calculate buying power at each level
        leverage_options = [
            (1, account_value, "⚪ Conservative"),
            (3, account_value * 3, "✨ Good for this size"),
            (5, account_value * 5, "🟡 Higher risk"),
            (10, account_value * 10, "🔴 Risky"),
            (20, account_value * 20, "💀 Extreme risk"),
        ]

        for lev, buying_power, label in leverage_options:
            can_afford = "✅" if buying_power >= amount_usd else "❌"
            message += f"{lev}x → {format_currency(buying_power)} max {can_afford} {label}\n"

        message += (
            f"\n💡 For {format_currency(amount_usd)} orders, 3-5x balances opportunity and safety."
        )

        # Build buttons (first 4 common options)
        builder = ButtonBuilder()
        for lev, _, _ in leverage_options[:4]:
            builder.action(f"{lev}x", f"leverage:{lev}")

        builder.action("Custom Leverage", "leverage:custom", style="secondary").back().cancel()

        query = update.callback_query
        if query:
            await query.edit_message_text(message, reply_markup=builder.build())

    async def step_5_preview(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,  # noqa: ARG002
        leverage: int,
        entry_price: float,
        liquidation_price: float,
        margin_available: float,
    ) -> None:
        """Step 5: Show order preview (two-tier pattern).

        Displays quick preview by default with option to see full details.

        Args:
            update: Telegram update
            context: Bot context
            leverage: Selected leverage multiplier
            entry_price: Expected entry price
            liquidation_price: Calculated liquidation price
            margin_available: Total margin available in account
        """
        self.state.leverage = leverage

        # Show loading state
        await LoadingMessage.show(update, "preview")

        # Calculate preview data
        preview_data = self._build_preview_data(
            entry_price=entry_price,
            liquidation_price=liquidation_price,
            margin_available=margin_available,
        )

        # Build tier-appropriate preview
        if self.state.preview_mode == "quick":
            message = PreviewBuilder.build_quick_preview(preview_data)
            buttons = self._build_quick_preview_buttons()
        else:
            message = PreviewBuilder.build_full_preview(preview_data)
            buttons = self._build_full_preview_buttons()

        query = update.callback_query
        if query:
            await query.edit_message_text(message, parse_mode="Markdown", reply_markup=buttons)

    async def step_6_execute(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,  # noqa: ARG002
        execution_result: dict[str, Any],
    ) -> None:
        """Step 6: Execute order and show success message.

        Args:
            update: Telegram update
            context: Bot context
            execution_result: Order execution details from exchange
        """
        # Show loading state
        await LoadingMessage.show(update, "order")

        # Build success message
        success_msg = self._build_success_message(execution_result)

        # Next action buttons
        buttons = (
            ButtonBuilder()
            .action("Set Stop Loss", f"set_sl:{self.state.coin}", style="primary")
            .action("View Position", f"view_pos:{self.state.coin}", style="secondary")
            .action("Main Menu", "menu_main", style="secondary")
            .build()
        )

        query = update.callback_query
        if query:
            await query.edit_message_text(success_msg, parse_mode="Markdown", reply_markup=buttons)

    def toggle_preview_mode(self) -> None:
        """Toggle between quick and full preview modes."""
        self.state.preview_mode = "full" if self.state.preview_mode == "quick" else "quick"

    def _build_preview_data(
        self,
        entry_price: float,
        liquidation_price: float,
        margin_available: float,
    ) -> PreviewData:
        """Build preview data from current state.

        Args:
            entry_price: Expected entry price
            liquidation_price: Calculated liquidation price
            margin_available: Total margin available

        Returns:
            Complete preview data structure
        """
        if not all([self.state.coin, self.state.side, self.state.amount_usd, self.state.leverage]):
            raise ValueError("Incomplete order state for preview")

        # Type assertions after validation
        coin = self.state.coin
        side = self.state.side
        amount_usd = self.state.amount_usd
        leverage = self.state.leverage

        assert coin is not None
        assert side is not None
        assert amount_usd is not None
        assert leverage is not None

        # Calculate derived values
        margin_required = amount_usd / leverage
        buying_power_used_pct = (margin_required / margin_available) * 100
        liquidation_distance_pct = abs((entry_price - liquidation_price) / entry_price) * 100
        size_coin = amount_usd / entry_price

        # Build warnings list
        warnings: list[str] = []
        risk_level = calculate_risk_level(liquidation_distance_pct, leverage, False)

        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EXTREME]:
            risk_emoji = RISK_EMOJIS[risk_level]
            warnings.append(f"{risk_emoji} High risk: Consider lower leverage or stop-loss")

        if buying_power_used_pct > 50:
            warnings.append("⚠️ Using >50% of buying power - limited margin for other positions")

        return PreviewData(
            coin=coin,
            side=side,
            amount_usd=amount_usd,
            leverage=leverage,
            entry_price=entry_price,
            margin_required=margin_required,
            margin_available=margin_available,
            buying_power_used_pct=buying_power_used_pct,
            liquidation_price=liquidation_price,
            liquidation_distance_pct=liquidation_distance_pct,
            size_coin=size_coin,
            has_stop_loss=False,
            warnings=warnings if warnings else [],
        )

    def _build_quick_preview_buttons(self) -> Any:
        """Build buttons for quick preview mode.

        Returns:
            InlineKeyboardMarkup with confirm + details options
        """
        # Type assertions
        assert self.state.side is not None
        assert self.state.amount_usd is not None
        assert self.state.coin is not None

        action_text = (
            f"{self.state.side.title()} {format_currency(self.state.amount_usd)} {self.state.coin}"
        )

        return (
            ButtonBuilder()
            .action(f"✅ Confirm {action_text}", "confirm_order", style="success")
            .action("📋 Full Details", "preview_full", style="secondary")
            .back()
            .cancel()
            .build()
        )

    def _build_full_preview_buttons(self) -> Any:
        """Build buttons for full preview mode.

        Returns:
            InlineKeyboardMarkup with confirm + cancel
        """
        # Type assertions
        assert self.state.side is not None
        assert self.state.amount_usd is not None
        assert self.state.coin is not None

        action_text = (
            f"{self.state.side.title()} {format_currency(self.state.amount_usd)} {self.state.coin}"
        )

        return (
            ButtonBuilder()
            .action(f"✅ Confirm {action_text}", "confirm_order", style="success")
            .back()
            .cancel()
            .build()
        )

    def _build_success_message(self, execution_result: dict[str, Any]) -> str:
        """Build success message after order execution.

        Args:
            execution_result: Order execution details

        Returns:
            Formatted success message
        """
        # Type assertions
        assert self.state.leverage is not None
        assert self.state.coin is not None
        assert self.state.side is not None
        assert self.state.amount_usd is not None

        liq_distance = execution_result.get("liquidation_distance_pct", 0)
        avg_price = execution_result.get("avg_fill_price", 0)

        return f"""
✅ **Order Executed!**

⚡ Leverage set to {self.state.leverage}x for {self.state.coin}
📈 Market {self.state.side.upper()} executed
   Value: {format_currency(self.state.amount_usd)}
   Avg Price: {format_currency(avg_price)}

💰 New Position created
   Liquidation: ~{liq_distance:.1f}% away

━━━━━━━━━━━━━━━━━
**What's next?**
"""
