"""
Menu navigation callback handlers for Telegram bot.

Handles all inline keyboard menu navigation including account views,
positions, help, and routing to command handlers.
"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from src.bot.menus import build_back_button, build_main_menu, build_positions_menu
from src.bot.middleware import authorized_only
from src.config import logger, settings
from src.services.market_data_service import market_data_service
from src.services.position_service import position_service


@authorized_only
async def menu_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu."""
    query = update.callback_query
    assert query is not None
    user_data = context.user_data
    assert user_data is not None

    query = update.callback_query
    await query.answer()  # type: ignore

    text = (
        "🏠 **Main Menu**\n\n"
        f"**Environment**: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}\n\n"
        "Select an action:"
    )

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=build_main_menu())  # type: ignore


@authorized_only
async def menu_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show account health via menu - delegates to account_command.

    Design Reference: docs/preliminary-ux-plan.md
    """
    query = update.callback_query
    assert query is not None
    user_data = context.user_data
    assert user_data is not None

    query = update.callback_query
    await query.answer()  # type: ignore

    try:
        # Show loading
        msg = await query.edit_message_text("⏳ Loading account health...")  # type: ignore

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

        # Update message with back button
        await msg.edit_text(message, parse_mode="HTML", reply_markup=build_back_button())  # type: ignore

        # Store message_id for auto-refresh
        user_data["account_message_id"] = msg.message_id  # type: ignore
        user_data["account_chat_id"] = msg.chat_id  # type: ignore

    except Exception as e:
        logger.exception("Account menu callback failed")
        await query.edit_message_text(  # type: ignore
            f"❌ Failed to fetch account health:\n{str(e)}",
            reply_markup=build_back_button(),
        )


@authorized_only
async def menu_positions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show positions via menu."""
    query = update.callback_query
    assert query is not None

    query = update.callback_query
    await query.answer()  # type: ignore

    try:
        # Show loading
        await query.edit_message_text("⏳ Fetching positions...")  # type: ignore

        # Get positions
        positions = position_service.list_positions()

        if not positions:
            await query.edit_message_text("📭 No open positions.", reply_markup=build_back_button())  # type: ignore
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

        await query.edit_message_text(  # type: ignore
            positions_msg, parse_mode="Markdown", reply_markup=build_back_button()
        )

    except Exception as e:
        logger.exception("Failed to fetch positions")
        await query.edit_message_text(  # type: ignore
            f"❌ Failed to fetch positions:\n`{str(e)}`",
            parse_mode="Markdown",
            reply_markup=build_back_button(),
        )


@authorized_only
async def menu_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help via menu."""
    query = update.callback_query
    assert query is not None

    query = update.callback_query
    await query.answer()  # type: ignore

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

    await query.edit_message_text(  # type: ignore
        help_text, parse_mode="Markdown", reply_markup=build_back_button()
    )


@authorized_only
async def menu_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show status via menu."""
    query = update.callback_query
    assert query is not None

    query = update.callback_query
    await query.answer()  # type: ignore

    status_msg = (
        "🤖 **Bot Status**\n\n"
        f"**Status**: ✅ Online\n"
        f"**Version**: {settings.VERSION}\n"
        f"**Environment**: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}\n"
        f"**Wallet**: `{settings.HYPERLIQUID_WALLET_ADDRESS[:8]}...{settings.HYPERLIQUID_WALLET_ADDRESS[-6:]}`\n"
        f"**Authorized Users**: {len(settings.TELEGRAM_AUTHORIZED_USERS)}\n\n"
        f"_Bot is running and connected to Hyperliquid._"
    )

    await query.edit_message_text(  # type: ignore
        status_msg, parse_mode="Markdown", reply_markup=build_back_button()
    )


@authorized_only
async def menu_close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show close position menu with position selection."""
    query = update.callback_query
    assert query is not None

    query = update.callback_query
    await query.answer()  # type: ignore

    try:
        # Show loading
        await query.edit_message_text("⏳ Fetching positions...")  # type: ignore

        # Get positions
        positions = position_service.list_positions()

        if not positions:
            await query.edit_message_text(  # type: ignore
                "📭 No open positions to close.", reply_markup=build_back_button()
            )
            return

        text = f"🎯 **Close Position**\n\nSelect a position to close ({len(positions)} open):\n"

        await query.edit_message_text(  # type: ignore
            text, parse_mode="Markdown", reply_markup=build_positions_menu(positions)
        )

    except Exception as e:
        logger.exception("Failed to fetch positions for close menu")
        await query.edit_message_text(  # type: ignore
            f"❌ Failed to fetch positions:\n`{str(e)}`",
            parse_mode="Markdown",
            reply_markup=build_back_button(),
        )


@authorized_only
async def menu_rebalance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rebalance menu button."""
    query = update.callback_query
    assert query is not None

    query = update.callback_query
    await query.answer()  # type: ignore

    # Import here to avoid circular import at module level
    from src.bot.handlers.commands import rebalance_command  # type: ignore

    # Call the rebalance command handler
    await rebalance_command(update, context)


@authorized_only
async def menu_scale_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle scale order menu button - directs to scale order wizard."""
    query = update.callback_query
    assert query is not None

    query = update.callback_query
    await query.answer()  # type: ignore

    # ConversationHandler requires command entry, so redirect user to use /scale
    await query.edit_message_text(  # type: ignore
        "📊 *Scale Order Wizard*\n\n"
        "Use the `/scale` command to start the interactive scale order wizard.\n\n"
        "*What is a scale order?*\n"
        "A scale order places multiple limit orders at different price levels, "
        "allowing you to gradually enter or exit a position.\n\n"
        "*Perfect for:*\n"
        "• 📈 *DCA In* - Buy as price drops (accumulate)\n"
        "• 📉 *DCA Out* - Sell as price rises (take profits)\n\n"
        "Type `/scale` to get started!",
        parse_mode="Markdown",
    )


# ============================================================================
# Callback Handler Exports
# ============================================================================


def get_menu_handlers():
    """Return list of menu navigation callback query handlers."""
    return [
        CallbackQueryHandler(menu_main_callback, pattern="^menu_main$"),
        CallbackQueryHandler(menu_account_callback, pattern="^menu_account$"),
        CallbackQueryHandler(menu_positions_callback, pattern="^menu_positions$"),
        CallbackQueryHandler(menu_help_callback, pattern="^menu_help$"),
        CallbackQueryHandler(menu_status_callback, pattern="^menu_status$"),
        CallbackQueryHandler(menu_close_callback, pattern="^menu_close$"),
        CallbackQueryHandler(menu_rebalance_callback, pattern="^menu_rebalance$"),
        # Note: menu_scale is now handled by scale_order_conversation ConversationHandler
    ]
