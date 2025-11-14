"""
Command handlers for Telegram bot.

Includes basic commands (/start, /help, /account, /positions, /status).
"""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from src.bot.menus import build_main_menu
from src.bot.middleware import authorized_only
from src.config import logger, settings
from src.services.market_data_service import market_data_service
from src.services.position_service import position_service

# ============================================================================
# Basic Commands
# ============================================================================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /start command.
    Shows welcome message and main menu.
    """
    assert update.message is not None

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
    assert update.message is not None

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
    Shows account health with risk indicators (auto-refreshes every 30s).

    Design Reference: docs/preliminary-ux-plan.md
    """
    assert update.message is not None
    user_data = context.user_data
    assert user_data is not None

    try:
        # Show loading message
        msg = await update.message.reply_text("⏳ Loading account health...")

        # Fetch risk analysis
        from src.use_cases.portfolio.risk_analysis import (
            RiskAnalysisRequest,
            RiskAnalysisUseCase,
        )

        use_case = RiskAnalysisUseCase()
        risk_data = await use_case.execute(
            RiskAnalysisRequest(coins=None, include_cross_margin_ratio=True)
        )

        # Format message
        from src.bot.formatters.account import format_account_health_message

        message = format_account_health_message(risk_data)

        # Update message (static - no keyboard)
        await msg.edit_text(message, parse_mode="HTML")

        # Store message_id for auto-refresh
        if context.user_data is not None:
            user_data["account_message_id"] = msg.message_id
            user_data["account_chat_id"] = msg.chat_id

    except Exception as e:
        logger.exception("Account command failed")
        await update.message.reply_text(f"❌ Failed to fetch account health:\n{str(e)}")


@authorized_only
async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /positions command.
    Lists all open positions with PnL and risk metrics.
    """
    assert update.message is not None

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
    assert update.message is not None

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
# Handler Registration
# ============================================================================


def get_command_handlers() -> list:
    """Return all basic command handlers."""
    return [
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("account", account_command),
        CommandHandler("positions", positions_command),
        CommandHandler("status", status_command),
    ]
