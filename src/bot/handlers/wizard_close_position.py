"""
Close Position Flow - Simple callback handlers for closing positions.

Flow:
1. User selects position to close (from menu)
2. Shows confirmation with position details
3. Executes market order to close

Note: This is not a full ConversationHandler wizard, just callback handlers.
"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.bot.menus import build_confirm_cancel, build_main_menu, build_positions_menu
from src.bot.middleware import authorized_only
from src.bot.utils import (
    format_coin_amount,
    format_usd_amount,
    send_error_and_end,
    send_success_and_end,
)
from src.config import logger, settings
from src.services.position_service import position_service
from src.use_cases.trading import (
    ClosePositionRequest,
    ClosePositionUseCase,
)

# Initialize use case
close_position_use_case = ClosePositionUseCase()


# ============================================================================
# Close Position Handlers
# ============================================================================


@authorized_only
async def close_position_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle position selection for closing."""
    query = update.callback_query
    assert query is not None
    assert query.data is not None

    query = update.callback_query
    await query.answer()  # type: ignore

    # Extract coin from callback data
    coin = query.data.split(":")[1]  # type: ignore

    try:
        # Show loading
        await query.edit_message_text(f"⏳ Fetching {coin} position details...")  # type: ignore

        # Get position details
        position_data = position_service.get_position(coin)
        p = position_data["position"]  # type: ignore
        size = p["size"]
        side = "LONG" if size > 0 else "SHORT"
        entry_price = p["entry_price"]
        position_value = abs(p["position_value"])
        pnl = p["unrealized_pnl"]
        pnl_pct = p["return_on_equity"] * 100

        # Format PnL
        if pnl >= 0:
            pnl_str = f"+${pnl:.2f} (+{pnl_pct:.2f}%)"
            pnl_emoji = "🟢"
        else:
            pnl_str = f"${pnl:.2f} ({pnl_pct:.2f}%)"
            pnl_emoji = "🔴"

        # Show confirmation
        coin_amount_str = format_coin_amount(abs(size), coin)
        usd_value_str = format_usd_amount(position_value)

        confirmation_msg = (
            f"🎯 **Close Position Confirmation**\n\n"
            f"**Coin**: {coin}\n"
            f"**Side**: {side}\n"
            f"**Position Size**: {coin_amount_str}\n"
            f"**USD Value**: {usd_value_str}\n"
            f"**Entry Price**: ${entry_price:,.2f}\n"
            f"**PnL**: {pnl_emoji} {pnl_str}\n\n"
            f"⚠️ This will place a market order to close the entire position.\n\n"
            f"_Environment: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}_"
        )

        await query.edit_message_text(  # type: ignore
            confirmation_msg,
            parse_mode="Markdown",
            reply_markup=build_confirm_cancel("close_pos", coin),
        )

    except ValueError as e:
        await query.edit_message_text(f"❌ {str(e)}", reply_markup=build_main_menu())  # type: ignore
    except Exception as e:
        logger.exception(f"Failed to get position details for {coin}")
        await query.edit_message_text(  # type: ignore
            f"❌ Error: `{str(e)}`", parse_mode="Markdown", reply_markup=build_main_menu()
        )


@authorized_only
async def close_position_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the close position order."""
    query = update.callback_query
    assert query is not None
    assert query.data is not None

    query = update.callback_query
    await query.answer()  # type: ignore

    # Extract coin from callback data
    coin = query.data.split(":")[1]  # type: ignore

    try:
        # Show processing
        await query.edit_message_text(f"⏳ Closing {coin} position...")  # type: ignore

        # Create use case request
        request = ClosePositionRequest(coin=coin)  # type: ignore

        # Execute use case
        response = await close_position_use_case.execute(request)

        # Format response details
        usd_str = f"\n**USD Value**: {format_usd_amount(response.usd_value)}"

        # Show result
        success_msg = (
            f"✅ **Position Closed**\n\n"
            f"**Coin**: {coin}\n"
            f"**Status**: {response.status}\n"
            f"**Size Closed**: {format_coin_amount(response.size_closed, coin)}{usd_str}\n\n"
            f"Market order has been placed to close the position."
        )

        # Use utility function - automatically shows main menu!
        return await send_success_and_end(update, success_msg)

    except Exception as e:
        logger.exception(f"Failed to close position {coin}")
        # Use utility function - automatically shows main menu!
        return await send_error_and_end(update, f"❌ Failed to close position:\n`{str(e)}`")


@authorized_only
async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /close command with optional coin or percentage arguments."""
    assert update.message is not None

    args = context.args if context.args else []

    # No args: show positions selection menu
    if not args:
        try:
            positions = position_service.list_positions()

            if not positions:
                await update.message.reply_text("📭 No open positions to close.")
                return

            prompt = (
                "🎯 **Close Position**\n\n"
                "Select a position to close or use `/close <coin>` for quick close:\n"
            )

            await update.message.reply_text(
                prompt,
                parse_mode="Markdown",
                reply_markup=build_positions_menu(positions),
            )
            return

        except Exception as e:
            logger.exception("Failed to list positions for /close")
            await update.message.reply_text(
                f"❌ Failed to fetch positions:\n`{str(e)}`", parse_mode="Markdown"
            )
            return

    coin = args[0].upper()
    size = None
    percentage = None

    if len(args) > 1:
        raw_value = args[1]
        try:
            if raw_value.endswith("%"):
                percentage = float(raw_value.rstrip("%"))
            else:
                numeric = float(raw_value)
                if 0 < numeric <= 100 and len(args) == 2:
                    percentage = numeric
                else:
                    size = numeric
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Use `/close BTC`, `/close BTC 50%`, or `/close BTC 0.1`.",
                parse_mode="Markdown",
            )
            return

    try:
        request = ClosePositionRequest(coin=coin, size=size, percentage=percentage, slippage=0.05)
        response = await close_position_use_case.execute(request)

        usd_str = format_usd_amount(response.usd_value)
        remaining = format_coin_amount(response.remaining_size, coin)

        message = (
            f"✅ **Position Closed**\n\n"
            f"**Coin**: {response.coin}\n"
            f"**Closed**: {format_coin_amount(response.size_closed, coin)} ({usd_str})\n"
            f"**Remaining**: {remaining}\n"
            f"**Type**: {response.close_type.capitalize()}\n"
            f"{response.message}"
        )

        await update.message.reply_text(
            message, parse_mode="Markdown", reply_markup=build_main_menu()
        )

    except Exception as e:
        logger.exception("/close command failed")
        await update.message.reply_text(
            f"❌ Failed to close position:\n`{str(e)}`",
            parse_mode="Markdown",
            reply_markup=build_main_menu(),
        )


# ============================================================================
# Handler Registration
# ============================================================================


def get_close_position_handlers():
    """Return list of callback handlers for close position flow."""
    return [
        CommandHandler("close", close_command),
        CallbackQueryHandler(close_position_selected, pattern="^select_position:"),
        CallbackQueryHandler(close_position_execute, pattern="^confirm_close_pos:"),
    ]
