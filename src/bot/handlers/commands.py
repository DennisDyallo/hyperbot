"""
Command handlers for Telegram bot.

Includes basic commands (/start, /help, /account, /positions, /status)
and rebalancing commands (/rebalance).
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot.menus import build_main_menu
from src.bot.middleware import authorized_only
from src.config import logger, settings
from src.services.account_service import account_service
from src.services.market_data_service import market_data_service
from src.services.position_service import position_service
from src.services.rebalance_service import rebalance_service

# ============================================================================
# Basic Commands
# ============================================================================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /start command.
    Shows welcome message and main menu.
    """
    user = update.effective_user
    user_id = user.id if user else None

    is_authorized = user_id in settings.TELEGRAM_AUTHORIZED_USERS if user_id else False

    if is_authorized:
        welcome_msg = (
            f"👋 Welcome to **{settings.PROJECT_NAME}**!\n\n"
            f"✅ You are authorized to use this bot.\n\n"
            f"**Environment**: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}\n"
            f"**Wallet**: `{settings.HYPERLIQUID_WALLET_ADDRESS[:8]}...{settings.HYPERLIQUID_WALLET_ADDRESS[-6:]}`\n\n"
            f"Select an action from the menu below:"
        )

        await update.message.reply_text(
            welcome_msg, parse_mode="Markdown", reply_markup=build_main_menu()
        )
    else:
        welcome_msg = (
            f"👋 Hello! This is **{settings.PROJECT_NAME}**.\n\n"
            f"🚫 You are not authorized to use this bot.\n\n"
            f"Your user ID: `{user_id}`\n"
            f"Contact the bot owner to request access."
        )

        await update.message.reply_text(welcome_msg, parse_mode="Markdown")


@authorized_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /help command.
    Shows list of available commands.
    """
    help_text = (
        "📚 **Available Commands**\n\n"
        "**Account & Positions:**\n"
        "/account - View account summary\n"
        "/positions - List all open positions\n"
        "/balance - View balance details\n\n"
        "**Trading:**\n"
        "/close - Close a position\n"
        "/market - Place market order\n\n"
        "**Advanced:**\n"
        "/rebalance - Rebalance portfolio\n"
        "/scale - Scale order wizard (DCA in/out)\n\n"
        "**Information:**\n"
        "/help - Show this help message\n"
        "/status - Bot status\n\n"
        f"**Environment**: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}"
    )

    await update.message.reply_text(help_text, parse_mode="Markdown")


@authorized_only
async def account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /account command.
    Shows account summary including balance, positions, and risk metrics.
    """
    try:
        # Show loading message
        msg = await update.message.reply_text("⏳ Fetching account information...")

        # Get account summary
        summary = account_service.get_account_summary()

        # Format account message
        account_msg = (
            "💰 **Account Summary**\n\n"
            f"**Total Value**: ${summary['total_account_value']:.2f}\n"
            f"├─ Perps: ${summary['perps_account_value']:.2f}\n"
            f"└─ Spot: ${summary['spot_account_value']:.2f}\n\n"
            f"**Available Balance**: ${summary['available_balance']:.2f}\n"
            f"**Margin Used**: ${summary['margin_used']:.2f}\n\n"
            f"**Positions**:\n"
            f"├─ Perps: {summary['num_perp_positions']}\n"
            f"└─ Spot Balances: {summary['num_spot_balances']}\n\n"
            f"**Total Unrealized PnL**: "
        )

        # Color code PnL
        pnl = summary["total_unrealized_pnl"]
        if pnl >= 0:
            account_msg += f"🟢 +${pnl:.2f}\n\n"
        else:
            account_msg += f"🔴 ${pnl:.2f}\n\n"

        # Add risk metrics
        margin_ratio = summary["cross_margin_ratio_pct"]
        if margin_ratio < 30:
            risk_emoji = "✅"
            risk_level = "SAFE"
        elif margin_ratio < 50:
            risk_emoji = "🟡"
            risk_level = "LOW"
        elif margin_ratio < 70:
            risk_emoji = "🟠"
            risk_level = "MODERATE"
        elif margin_ratio < 90:
            risk_emoji = "🔴"
            risk_level = "HIGH"
        else:
            risk_emoji = "🚨"
            risk_level = "CRITICAL"

        account_msg += (
            f"**Risk Metrics**:\n"
            f"Margin Ratio: {risk_emoji} {margin_ratio:.2f}% ({risk_level})\n"
            f"Maintenance Margin: ${summary['cross_maintenance_margin']:.2f}\n"
            f"Account Leverage: {summary['cross_account_leverage']:.2f}x\n\n"
            f"_Environment: {'🧪 Testnet' if summary['is_testnet'] else '🚀 Mainnet'}_"
        )

        await msg.edit_text(account_msg, parse_mode="Markdown")

    except Exception as e:
        logger.exception("Failed to fetch account summary")
        await update.message.reply_text(
            f"❌ Failed to fetch account information:\n`{str(e)}`",
            parse_mode="Markdown",
        )


@authorized_only
async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /positions command.
    Lists all open positions with PnL and risk metrics.
    """
    try:
        # Show loading message
        msg = await update.message.reply_text("⏳ Fetching positions...")

        # Get positions
        positions = position_service.list_positions()

        if not positions:
            await msg.edit_text("📭 No open positions.")
            return

        # Format positions message
        positions_msg = f"📊 **Open Positions** ({len(positions)})\n\n"

        for pos in positions:
            p = pos["position"]
            coin = p["coin"]
            size = p["size"]
            side = "LONG" if size > 0 else "SHORT"
            side_emoji = "🟢" if size > 0 else "🔴"

            entry_price = p["entry_price"]
            position_value = abs(p["position_value"])
            pnl = p["unrealized_pnl"]
            pnl_pct = p["return_on_equity"] * 100
            leverage = p["leverage_value"]

            # Get current price
            try:
                current_price = market_data_service.get_price(coin)
            except Exception as e:
                logger.warning(f"Failed to fetch price for {coin}: {e}")
                current_price = None

            # Format PnL
            if pnl >= 0:
                pnl_str = f"+${pnl:.2f} (+{pnl_pct:.2f}%)"
                pnl_emoji = "🟢"
            else:
                pnl_str = f"${pnl:.2f} ({pnl_pct:.2f}%)"
                pnl_emoji = "🔴"

            # Build position display
            position_lines = [
                f"{side_emoji} **{coin}** {side}",
                f"├─ Size: {abs(size):.4f}",
            ]

            if current_price:
                position_lines.append(f"├─ Current: ${current_price:.2f}")

            position_lines.extend(
                [
                    f"├─ Entry: ${entry_price:.2f}",
                    f"├─ Value: ${position_value:.2f}",
                    f"├─ PnL: {pnl_emoji} {pnl_str}",
                    f"└─ Leverage: {leverage}x\n\n",
                ]
            )

            positions_msg += "\n".join(position_lines)

        positions_msg += "_Use /close <coin> to close a position_"

        await msg.edit_text(positions_msg, parse_mode="Markdown")

    except Exception as e:
        logger.exception("Failed to fetch positions")
        await update.message.reply_text(
            f"❌ Failed to fetch positions:\n`{str(e)}`", parse_mode="Markdown"
        )


@authorized_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /status command.
    Shows bot status and configuration.
    """
    status_msg = (
        "🤖 **Bot Status**\n\n"
        f"**Status**: ✅ Online\n"
        f"**Version**: {settings.VERSION}\n"
        f"**Environment**: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}\n"
        f"**Wallet**: `{settings.HYPERLIQUID_WALLET_ADDRESS[:8]}...{settings.HYPERLIQUID_WALLET_ADDRESS[-6:]}`\n"
        f"**Authorized Users**: {len(settings.TELEGRAM_AUTHORIZED_USERS)}\n\n"
        f"_Bot is running and connected to Hyperliquid._"
    )

    await update.message.reply_text(status_msg, parse_mode="Markdown")


# ============================================================================
# Rebalancing Commands
# ============================================================================


@authorized_only
async def rebalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /rebalance command or menu button.
    Rebalances portfolio with preset options.

    Reference: docs/hyperliquid/api-reference.md - Portfolio Rebalancing
    """
    try:
        # Handle both command and callback query
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            msg = await query.edit_message_text("⏳ Analyzing portfolio...")
        else:
            msg = await update.message.reply_text("⏳ Analyzing portfolio...")

        # Get current positions
        positions = position_service.list_positions()

        if not positions:
            await msg.edit_text("📭 No open positions to rebalance.")
            return

        # Show current allocation
        total_value = sum(abs(p["position"]["position_value"]) for p in positions)

        allocation_text = "📊 **Current Portfolio**\n\n"
        for pos in positions:
            p = pos["position"]
            coin = p["coin"]
            value = abs(p["position_value"])
            pct = (value / total_value * 100) if total_value > 0 else 0
            allocation_text += f"• {coin}: ${value:.2f} ({pct:.1f}%)\n"

        allocation_text += f"\n**Total Value**: ${total_value:.2f}\n\n"
        allocation_text += "**Rebalance Options**:\n"
        allocation_text += "Choose a rebalancing strategy below."

        # Create inline keyboard with preset options
        keyboard = [
            [InlineKeyboardButton("⚖️ Equal Weight", callback_data="rebalance_preview:equal")],
            [InlineKeyboardButton("📊 Custom Weights", callback_data="rebalance_custom")],
            [InlineKeyboardButton("❌ Cancel", callback_data="rebalance_cancel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await msg.edit_text(allocation_text, parse_mode="Markdown", reply_markup=reply_markup)

    except Exception as e:
        logger.exception("Failed to analyze portfolio for rebalancing")
        error_msg = f"❌ Error: `{str(e)}`"
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(error_msg, parse_mode="Markdown")


async def rebalance_preview_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rebalance preview callback."""
    query = update.callback_query
    await query.answer()

    if query.data == "rebalance_cancel":
        await query.edit_message_text("❌ Rebalancing cancelled.")
        return

    if query.data == "rebalance_custom":
        await query.edit_message_text(
            "📝 **Custom Rebalancing**\n\n"
            "Custom weight rebalancing is not yet implemented.\n"
            "Use `/rebalance` and select equal weight, or use the web dashboard for advanced options."
        )
        return

    # Extract strategy
    _, strategy = query.data.split(":")

    try:
        # Show processing
        await query.edit_message_text("⏳ Generating rebalance plan...")

        # Get positions
        positions = position_service.list_positions()

        # Build target allocations (equal weight)
        num_positions = len(positions)
        target_pct = 100.0 / num_positions if num_positions > 0 else 0

        target_allocations = {p["position"]["coin"]: target_pct for p in positions}

        # Preview rebalance (fix parameter names to match service)
        preview = rebalance_service.preview_rebalance(
            target_weights=target_allocations,  # Service expects "target_weights"
            leverage=3,  # Service expects "leverage"
        )

        # Format preview message (preview is RebalanceResult dataclass)
        preview_msg = "📊 **Rebalance Preview**\n\n"

        if not preview.planned_trades or all(
            t.action.value == "SKIP" for t in preview.planned_trades
        ):
            preview_msg += "✅ Portfolio is already balanced!\n\n"
            await query.edit_message_text(preview_msg)
            return

        preview_msg += f"**Target**: Equal weight ({target_pct:.1f}% each)\n"
        preview_msg += "**Leverage**: 3x\n\n"
        preview_msg += "**Required Trades**:\n"

        # Get actionable trades (skip SKIP actions)
        actionable_trades = [t for t in preview.planned_trades if t.action.value != "SKIP"]

        for trade in actionable_trades[:5]:  # Show first 5 trades
            action = trade.action.value
            coin = trade.coin

            if action == "CLOSE":
                preview_msg += f"🔴 Close {coin} (${abs(trade.current_usd_value):.2f})\n"
            elif action == "DECREASE":
                preview_msg += f"🟡 Reduce {coin} by ${abs(trade.trade_usd_value):.2f}\n"
            elif action == "INCREASE":
                preview_msg += f"🟢 Increase {coin} by ${abs(trade.trade_usd_value):.2f}\n"
            elif action == "OPEN":
                preview_msg += f"🆕 Open {coin} (${abs(trade.target_usd_value):.2f})\n"

        if len(actionable_trades) > 5:
            preview_msg += f"_...and {len(actionable_trades) - 5} more trades_\n"

        preview_msg += f"\n**Total Actionable Trades**: {len(actionable_trades)}\n"
        preview_msg += f"**Total Trades**: {len(preview.planned_trades)}\n\n"

        if preview.risk_warnings:
            preview_msg += "⚠️ **Warnings**:\n"
            for warning in preview.risk_warnings[:3]:
                preview_msg += f"• {warning}\n"
            preview_msg += "\n"

        preview_msg += (
            f"_Environment: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}_"
        )

        # Create confirmation keyboard
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Execute Rebalance",
                    callback_data=f"rebalance_execute:{strategy}",
                ),
                InlineKeyboardButton("❌ Cancel", callback_data="rebalance_cancel"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(preview_msg, parse_mode="Markdown", reply_markup=reply_markup)

    except Exception as e:
        logger.exception("Failed to preview rebalance")
        await query.edit_message_text(
            f"❌ Failed to generate preview:\n`{str(e)}`", parse_mode="Markdown"
        )


async def rebalance_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rebalance execution callback."""
    query = update.callback_query
    await query.answer()

    # Extract strategy
    _, strategy = query.data.split(":")

    try:
        # Show processing
        await query.edit_message_text("⏳ Executing rebalance...\n\nThis may take a few moments.")

        # Get positions and build target allocations
        positions = position_service.list_positions()
        num_positions = len(positions)
        target_pct = 100.0 / num_positions if num_positions > 0 else 0

        target_allocations = {p["position"]["coin"]: target_pct for p in positions}

        # Execute rebalance
        result = rebalance_service.execute_rebalance(
            target_weights=target_allocations,
            leverage=3,
            dry_run=False,  # Execute for real
        )

        # Format result message
        if result.success:
            total_trades = result.executed_trades
            success_msg = "✅ **Rebalance Complete**\n\n"
            success_msg += f"**Total Trades**: {total_trades}\n"
            success_msg += f"**Successful**: {result.successful_trades}\n"
            success_msg += f"**Failed**: {result.failed_trades}\n"
            success_msg += f"**Skipped**: {result.skipped_trades}\n\n"

            if result.failed_trades > 0:
                success_msg += "⚠️ Some trades failed. Check your positions.\n\n"
                if result.errors:
                    success_msg += "**Errors**:\n"
                    for error in result.errors[:3]:  # Show first 3 errors
                        success_msg += f"• {error}\n"
                    success_msg += "\n"

            success_msg += "_Use /positions to see updated portfolio_"
            await query.edit_message_text(success_msg, parse_mode="Markdown")
        else:
            error_msg = f"❌ **Rebalance Failed**\n\n{result.message}"
            if result.errors:
                error_msg += "\n\n**Errors**:\n"
                for error in result.errors[:3]:
                    error_msg += f"• {error}\n"
            await query.edit_message_text(error_msg, parse_mode="Markdown")

    except Exception as e:
        logger.exception("Failed to execute rebalance")
        await query.edit_message_text(f"❌ Rebalance failed:\n`{str(e)}`", parse_mode="Markdown")
