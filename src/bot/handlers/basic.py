"""
Basic command handlers for Telegram bot.
"""
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from src.bot.middleware import authorized_only
from src.bot.menus import build_main_menu, build_back_button, build_positions_menu
from src.services.account_service import account_service
from src.services.position_service import position_service
from src.config import logger, settings


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
            welcome_msg,
            parse_mode="Markdown",
            reply_markup=build_main_menu()
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


# ============================================================================
# Menu Navigation Callbacks
# ============================================================================

@authorized_only
async def menu_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu."""
    query = update.callback_query
    await query.answer()

    text = (
        "🏠 **Main Menu**\n\n"
        f"**Environment**: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}\n\n"
        "Select an action:"
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=build_main_menu()
    )


@authorized_only
async def menu_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show account summary via menu."""
    query = update.callback_query
    await query.answer()

    try:
        # Show loading
        await query.edit_message_text("⏳ Fetching account information...")

        # Get account summary
        summary = account_service.get_account_summary()

        # Format account message (using correct field names)
        account_msg = (
            "💰 **Account Summary**\n\n"
            f"**Total Value**: ${summary['total_account_value']:.2f}\n"
            f"├─ Perps: ${summary['perps_account_value']:.2f}\n"
            f"└─ Spot: ${summary['spot_account_value']:.2f}\n\n"
            f"**Available Balance**: ${summary['available_balance']:.2f}\n"
            f"**Margin Used**: ${summary['margin_used']:.2f}\n\n"
            f"**Perp Positions**: {summary['num_perp_positions']}\n"
            f"**Spot Balances**: {summary['num_spot_balances']}\n\n"
            f"**Total PnL**: ${summary['total_unrealized_pnl']:.2f}\n\n"
            f"**Cross Margin Ratio**: {summary['cross_margin_ratio_pct']:.2f}%\n"
            f"**Account Leverage**: {summary['cross_account_leverage']:.2f}x"
        )

        await query.edit_message_text(
            account_msg,
            parse_mode="Markdown",
            reply_markup=build_back_button()
        )

    except Exception as e:
        logger.exception("Failed to fetch account summary")
        await query.edit_message_text(
            f"❌ Failed to fetch account information:\n`{str(e)}`",
            parse_mode="Markdown",
            reply_markup=build_back_button()
        )


@authorized_only
async def menu_positions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show positions via menu."""
    query = update.callback_query
    await query.answer()

    try:
        # Show loading
        await query.edit_message_text("⏳ Fetching positions...")

        # Get positions
        positions = position_service.list_positions()

        if not positions:
            await query.edit_message_text(
                "📭 No open positions.",
                reply_markup=build_back_button()
            )
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

        positions_msg += f"_Use 🎯 Close Position menu to close_"

        await query.edit_message_text(
            positions_msg,
            parse_mode="Markdown",
            reply_markup=build_back_button()
        )

    except Exception as e:
        logger.exception("Failed to fetch positions")
        await query.edit_message_text(
            f"❌ Failed to fetch positions:\n`{str(e)}`",
            parse_mode="Markdown",
            reply_markup=build_back_button()
        )


@authorized_only
async def menu_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help via menu."""
    query = update.callback_query
    await query.answer()

    help_text = (
        "📚 **Help & Commands**\n\n"
        "**Navigation:**\n"
        "Use the menu buttons to navigate.\n"
        "Tap 🏠 Main Menu to return anytime.\n\n"
        "**Features:**\n"
        "• 📊 Account - View balance & stats\n"
        "• 📈 Positions - See open positions\n"
        "• 💰 Market Order - Quick buy/sell\n"
        "• 🎯 Close Position - Close trades\n"
        "• ⚖️ Rebalance - Portfolio rebalancing\n"
        "• 📊 Scale Order - Ladder orders\n\n"
        "**Amounts:**\n"
        "All trading uses USD amounts.\n"
        "Example: Buy $100 worth of BTC\n\n"
        f"**Environment**: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}"
    )

    await query.edit_message_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=build_back_button()
    )


@authorized_only
async def menu_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show status via menu."""
    query = update.callback_query
    await query.answer()

    status_msg = (
        "🤖 **Bot Status**\n\n"
        f"**Status**: ✅ Online\n"
        f"**Version**: {settings.VERSION}\n"
        f"**Environment**: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}\n"
        f"**Wallet**: `{settings.HYPERLIQUID_WALLET_ADDRESS[:8]}...{settings.HYPERLIQUID_WALLET_ADDRESS[-6:]}`\n"
        f"**Authorized Users**: {len(settings.TELEGRAM_AUTHORIZED_USERS)}\n\n"
        f"_Bot is running and connected to Hyperliquid._"
    )

    await query.edit_message_text(
        status_msg,
        parse_mode="Markdown",
        reply_markup=build_back_button()
    )


@authorized_only
async def menu_close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show close position menu with position selection."""
    query = update.callback_query
    await query.answer()

    try:
        # Show loading
        await query.edit_message_text("⏳ Fetching positions...")

        # Get positions
        positions = position_service.list_positions()

        if not positions:
            await query.edit_message_text(
                "📭 No open positions to close.",
                reply_markup=build_back_button()
            )
            return

        text = (
            "🎯 **Close Position**\n\n"
            f"Select a position to close ({len(positions)} open):\n"
        )

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=build_positions_menu(positions)
        )

    except Exception as e:
        logger.exception("Failed to fetch positions for close menu")
        await query.edit_message_text(
            f"❌ Failed to fetch positions:\n`{str(e)}`",
            parse_mode="Markdown",
            reply_markup=build_back_button()
        )


@authorized_only
async def menu_rebalance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rebalance menu button."""
    query = update.callback_query
    await query.answer()

    # Import here to avoid circular import
    from src.bot.handlers.advanced import rebalance_command

    # Call the rebalance command handler
    await rebalance_command(update, context)


@authorized_only
async def menu_scale_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle scale order menu button - directs to scale order wizard."""
    query = update.callback_query
    await query.answer()

    # ConversationHandler requires command entry, so redirect user to use /scale
    await query.edit_message_text(
        "📊 *Scale Order Wizard*\n\n"
        "Use the `/scale` command to start the interactive scale order wizard.\n\n"
        "*What is a scale order?*\n"
        "A scale order places multiple limit orders at different price levels, "
        "allowing you to gradually enter or exit a position.\n\n"
        "*Perfect for:*\n"
        "• 📈 *DCA In* - Buy as price drops (accumulate)\n"
        "• 📉 *DCA Out* - Sell as price rises (take profits)\n\n"
        "Type `/scale` to get started!",
        parse_mode="Markdown"
    )


# ============================================================================
# Callback Handler Exports
# ============================================================================

def get_menu_callback_handlers():
    """Return list of callback query handlers for menu navigation."""
    return [
        CallbackQueryHandler(menu_main_callback, pattern="^menu_main$"),
        CallbackQueryHandler(menu_account_callback, pattern="^menu_account$"),
        CallbackQueryHandler(menu_positions_callback, pattern="^menu_positions$"),
        CallbackQueryHandler(menu_help_callback, pattern="^menu_help$"),
        CallbackQueryHandler(menu_status_callback, pattern="^menu_status$"),
        CallbackQueryHandler(menu_close_callback, pattern="^menu_close$"),
        CallbackQueryHandler(menu_rebalance_callback, pattern="^menu_rebalance$"),
        CallbackQueryHandler(menu_scale_callback, pattern="^menu_scale$"),
    ]
