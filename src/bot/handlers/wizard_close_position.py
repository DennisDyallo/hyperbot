"""
Close Position Flow - Simple callback handlers for closing positions.

Flow:
1. User selects position to close (from menu)
2. Shows confirmation with position details
3. Executes market order to close

Note: This is not a full ConversationHandler wizard, just callback handlers.
"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from src.bot.menus import build_confirm_cancel, build_main_menu
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
    await query.answer()

    # Extract coin from callback data
    coin = query.data.split(":")[1]

    try:
        # Show loading
        await query.edit_message_text(f"⏳ Fetching {coin} position details...")

        # Get position details
        position_data = position_service.get_position(coin)
        p = position_data["position"]
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

        await query.edit_message_text(
            confirmation_msg,
            parse_mode="Markdown",
            reply_markup=build_confirm_cancel("close_pos", coin),
        )

    except ValueError as e:
        await query.edit_message_text(f"❌ {str(e)}", reply_markup=build_main_menu())
    except Exception as e:
        logger.exception(f"Failed to get position details for {coin}")
        await query.edit_message_text(
            f"❌ Error: `{str(e)}`", parse_mode="Markdown", reply_markup=build_main_menu()
        )


@authorized_only
async def close_position_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the close position order."""
    query = update.callback_query
    await query.answer()

    # Extract coin from callback data
    coin = query.data.split(":")[1]

    try:
        # Show processing
        await query.edit_message_text(f"⏳ Closing {coin} position...")

        # Create use case request
        request = ClosePositionRequest(coin=coin)

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


# ============================================================================
# Handler Registration
# ============================================================================


def get_close_position_handlers():
    """Return list of callback handlers for close position flow."""
    return [
        CallbackQueryHandler(close_position_selected, pattern="^select_position:"),
        CallbackQueryHandler(close_position_execute, pattern="^confirm_close_pos:"),
    ]
