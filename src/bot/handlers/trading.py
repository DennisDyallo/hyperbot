"""
Trading command handlers for Telegram bot.

Reference: docs/telegram/best-practices.md - Confirmation Dialogs
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from src.bot.middleware import authorized_only
from src.bot.utils import (
    parse_usd_amount,
    convert_usd_to_coin,
    convert_coin_to_usd,
    format_coin_amount,
    format_usd_amount,
)
from src.services.position_service import position_service
from src.services.order_service import order_service
from src.config import logger, settings


@authorized_only
async def close_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /close <coin> command.
    Closes a position with confirmation.

    Reference: docs/hyperliquid/api-reference.md - Closing Positions
    """
    # Check arguments
    if not context.args:
        await update.message.reply_text(
            "❌ **Usage**: `/close <coin>`\n\n"
            "**Example**: `/close BTC`\n\n"
            "This will close your entire position in the specified coin.",
            parse_mode="Markdown"
        )
        return

    try:
        coin = context.args[0].upper()

        # Get position details
        msg = await update.message.reply_text(f"⏳ Fetching {coin} position...")

        try:
            position_data = position_service.get_position(coin)
        except ValueError as e:
            await msg.edit_text(f"❌ {str(e)}")
            return

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
            f"📊 **Close Position Confirmation**\n\n"
            f"**Coin**: {coin}\n"
            f"**Side**: {side}\n"
            f"**Position Size**: {coin_amount_str}\n"
            f"**USD Value**: {usd_value_str}\n"
            f"**Entry Price**: ${entry_price:,.2f}\n"
            f"**PnL**: {pnl_emoji} {pnl_str}\n\n"
            f"⚠️ This will place a market order to close the entire position.\n\n"
            f"_Environment: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}_"
        )

        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm Close", callback_data=f"close_confirm:{coin}"),
                InlineKeyboardButton("❌ Cancel", callback_data="close_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await msg.edit_text(
            confirmation_msg,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.exception("Failed to prepare close confirmation")
        await update.message.reply_text(
            f"❌ Error: `{str(e)}`",
            parse_mode="Markdown"
        )


async def close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle close position confirmation callback."""
    query = update.callback_query
    await query.answer()

    if query.data == "close_cancel":
        await query.edit_message_text("❌ Close position cancelled.")
        return

    # Extract coin from callback data
    _, coin = query.data.split(":")

    try:
        # Show processing
        await query.edit_message_text(f"⏳ Closing {coin} position...")

        # Close position
        result = position_service.close_position(coin)

        # Get USD value of closed position
        try:
            size_closed = abs(result['size'])
            usd_value, _ = convert_coin_to_usd(size_closed, coin)
            usd_str = f"\n**USD Value**: {format_usd_amount(usd_value)}"
        except Exception:
            usd_str = ""

        # Show result
        success_msg = (
            f"✅ **Position Closed**\n\n"
            f"**Coin**: {coin}\n"
            f"**Status**: {result['status']}\n"
            f"**Size Closed**: {format_coin_amount(abs(result['size']), coin)}{usd_str}\n\n"
            f"Market order has been placed to close the position."
        )

        await query.edit_message_text(success_msg, parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"Failed to close position {coin}")
        await query.edit_message_text(
            f"❌ Failed to close position:\n`{str(e)}`",
            parse_mode="Markdown"
        )


@authorized_only
async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /market <coin> <buy/sell> <usd_amount> command.
    Places a market order with USD-based sizing and confirmation.

    Reference: docs/hyperliquid/api-reference.md - Market Orders
    """
    # Check arguments
    if len(context.args) < 3:
        await update.message.reply_text(
            "💰 **Usage**: `/market <coin> <buy/sell> <usd_amount>`\n\n"
            "**Amount is in USD** ($ prefix optional):\n"
            "`/market BTC buy 100` - Buy $100 worth of BTC\n"
            "`/market ETH sell $50` - Sell $50 worth of ETH\n\n"
            "⚠️ Market order will execute at best available price.\n"
            "Confirmation will show exact coin amount before placing.",
            parse_mode="Markdown"
        )
        return

    try:
        coin = context.args[0].upper()
        side_str = context.args[1].lower()
        usd_amount_str = context.args[2]

        # Validate side
        if side_str not in ["buy", "sell"]:
            await update.message.reply_text(
                "❌ Invalid side. Use `buy` or `sell`.",
                parse_mode="Markdown"
            )
            return

        is_buy = side_str == "buy"
        side_emoji = "🟢" if is_buy else "🔴"
        side_label = "BUY" if is_buy else "SELL"

        # Parse USD amount
        try:
            usd_amount = parse_usd_amount(usd_amount_str)
        except ValueError as e:
            await update.message.reply_text(f"❌ {str(e)}")
            return

        # Show loading message
        msg = await update.message.reply_text(
            f"⏳ Fetching {coin} price and calculating order size..."
        )

        # Convert USD to coin size
        try:
            coin_size, current_price = convert_usd_to_coin(usd_amount, coin)
        except (ValueError, RuntimeError) as e:
            await msg.edit_text(f"❌ {str(e)}")
            return

        # Show confirmation with both USD and coin amounts
        confirmation_msg = (
            f"{side_emoji} **Market Order Confirmation**\n\n"
            f"**Coin**: {coin}\n"
            f"**Side**: {side_label}\n"
            f"**USD Amount**: {format_usd_amount(usd_amount)}\n"
            f"**Coin Size**: {format_coin_amount(coin_size, coin)}\n"
            f"**Current Price**: ${current_price:,.2f}\n\n"
            f"⚠️ Market orders execute at best available price.\n"
            f"Slippage may occur on large orders.\n\n"
            f"_Environment: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}_"
        )

        # Create inline keyboard (store coin_size in callback)
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm Order", callback_data=f"market_confirm:{coin}:{side_str}:{coin_size}"),
                InlineKeyboardButton("❌ Cancel", callback_data="market_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await msg.edit_text(
            confirmation_msg,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    except ValueError as e:
        await update.message.reply_text(f"❌ Invalid input: {str(e)}")
    except Exception as e:
        logger.exception("Failed to prepare market order confirmation")
        await update.message.reply_text(
            f"❌ Error: `{str(e)}`",
            parse_mode="Markdown"
        )


async def market_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle market order confirmation callback."""
    query = update.callback_query
    await query.answer()

    if query.data == "market_cancel":
        await query.edit_message_text("❌ Market order cancelled.")
        return

    # Extract parameters from callback data
    _, coin, side_str, size_str = query.data.split(":")
    is_buy = side_str == "buy"
    size = float(size_str)

    try:
        # Show processing
        await query.edit_message_text(f"⏳ Placing {side_str.upper()} order for {coin}...")

        # Place market order
        result = order_service.place_market_order(
            coin=coin,
            is_buy=is_buy,
            size=size
        )

        # Calculate USD value at execution
        try:
            usd_value, execution_price = convert_coin_to_usd(size, coin)
            usd_str = f"\n**USD Amount**: {format_usd_amount(usd_value)}"
            price_str = f"\n**Execution Price**: ${execution_price:,.2f}"
        except Exception:
            usd_str = ""
            price_str = ""

        # Show result
        side_emoji = "🟢" if is_buy else "🔴"
        success_msg = (
            f"{side_emoji} **Market Order Placed**\n\n"
            f"**Coin**: {coin}\n"
            f"**Side**: {side_str.upper()}\n"
            f"**Coin Size**: {format_coin_amount(size, coin)}{usd_str}{price_str}\n"
            f"**Status**: {result['status']}\n\n"
            f"Order has been submitted to the exchange."
        )

        await query.edit_message_text(success_msg, parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"Failed to place market order for {coin}")
        await query.edit_message_text(
            f"❌ Failed to place order:\n`{str(e)}`",
            parse_mode="Markdown"
        )


# Export callback handlers
def get_callback_handlers():
    """Return list of callback query handlers for trading commands."""
    return [
        CallbackQueryHandler(close_callback, pattern="^close_"),
        CallbackQueryHandler(market_callback, pattern="^market_"),
    ]
