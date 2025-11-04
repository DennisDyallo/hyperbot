"""
Basic command handlers for Telegram bot.
"""
from telegram import Update
from telegram.ext import ContextTypes
from src.bot.middleware import authorized_only
from src.services.account_service import account_service
from src.services.position_service import position_service
from src.config import logger, settings


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /start command.
    Shows welcome message and authorization status.
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
            f"Use /help to see available commands."
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
        "/scale - Place scale order\n\n"
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
        pnl = summary['total_unrealized_pnl']
        if pnl >= 0:
            account_msg += f"🟢 +${pnl:.2f}\n\n"
        else:
            account_msg += f"🔴 ${pnl:.2f}\n\n"

        # Add risk metrics
        margin_ratio = summary['cross_margin_ratio_pct']
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
            parse_mode="Markdown"
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

            # Format PnL
            if pnl >= 0:
                pnl_str = f"+${pnl:.2f} (+{pnl_pct:.2f}%)"
                pnl_emoji = "🟢"
            else:
                pnl_str = f"${pnl:.2f} ({pnl_pct:.2f}%)"
                pnl_emoji = "🔴"

            positions_msg += (
                f"{side_emoji} **{coin}** {side}\n"
                f"├─ Size: {abs(size):.4f}\n"
                f"├─ Entry: ${entry_price:.2f}\n"
                f"├─ Value: ${position_value:.2f}\n"
                f"├─ PnL: {pnl_emoji} {pnl_str}\n"
                f"└─ Leverage: {leverage}x\n\n"
            )

        positions_msg += f"_Use /close <coin> to close a position_"

        await msg.edit_text(positions_msg, parse_mode="Markdown")

    except Exception as e:
        logger.exception("Failed to fetch positions")
        await update.message.reply_text(
            f"❌ Failed to fetch positions:\n`{str(e)}`",
            parse_mode="Markdown"
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
