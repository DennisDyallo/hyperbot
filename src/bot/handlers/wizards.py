"""
Interactive wizard handlers using ConversationHandler.

Implements multi-step flows for trading operations.
"""
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from src.bot.middleware import authorized_only
from src.bot.menus import (
    build_main_menu,
    build_coin_selection_menu,
    build_buy_sell_menu,
    build_quick_amounts_menu,
    build_confirm_cancel,
    build_num_orders_menu,
    build_back_button,
)
from src.bot.utils import (
    parse_usd_amount,
    convert_usd_to_coin,
    convert_coin_to_usd,
    format_coin_amount,
    format_usd_amount,
)
from src.services.order_service import order_service
from src.services.position_service import position_service
from src.services.scale_order_service import scale_order_service
from src.use_cases.trading import (
    PlaceOrderUseCase,
    PlaceOrderRequest,
    ClosePositionUseCase,
    ClosePositionRequest,
)
from src.config import logger, settings

# Initialize use cases
place_order_use_case = PlaceOrderUseCase()
close_position_use_case = ClosePositionUseCase()


# Conversation states for market order wizard
MARKET_COIN, MARKET_SIDE, MARKET_AMOUNT, MARKET_CONFIRM = range(4)

# Conversation states for scale order wizard
SCALE_COIN, SCALE_SIDE, SCALE_AMOUNT, SCALE_NUM_ORDERS, SCALE_START_PRICE, SCALE_END_PRICE, SCALE_CONFIRM = range(7)


# ============================================================================
# Market Order Wizard
# ============================================================================

@authorized_only
async def market_wizard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start market order wizard - select coin."""
    query = update.callback_query
    await query.answer()

    text = (
        "💰 **Market Order**\n\n"
        "Step 1/3: Select coin to trade\n\n"
        "Choose from popular coins or enter custom symbol:"
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=build_coin_selection_menu()
    )

    return MARKET_COIN


async def market_coin_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle coin selection - ask for buy/sell."""
    query = update.callback_query
    await query.answer()

    # Extract coin from callback data
    coin = query.data.split(":")[1]
    context.user_data['market_coin'] = coin

    text = (
        f"💰 **Market Order: {coin}**\n\n"
        f"Step 2/3: Buy or Sell?\n\n"
        f"Select order side:"
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=build_buy_sell_menu(coin)
    )

    return MARKET_SIDE


async def market_side_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buy/sell selection - ask for amount."""
    query = update.callback_query
    await query.answer()

    # Extract side and coin from callback data (format: "side_buy:ETH")
    parts = query.data.split(":")
    side_str = parts[0].split("_")[1]  # "side_buy" -> "buy"
    coin = parts[1]
    is_buy = side_str == "buy"

    context.user_data['market_is_buy'] = is_buy
    context.user_data['market_side_str'] = side_str.upper()

    side_emoji = "🟢" if is_buy else "🔴"

    text = (
        f"{side_emoji} **{side_str.upper()} {coin}**\n\n"
        f"Step 3/3: Enter amount in USD\n\n"
        f"Choose a preset amount or enter custom:"
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=build_quick_amounts_menu()
    )

    return MARKET_AMOUNT


async def market_amount_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount selection - show confirmation."""
    query = update.callback_query
    await query.answer()

    # Extract amount from callback data
    amount_str = query.data.split(":")[1]

    try:
        usd_amount = parse_usd_amount(amount_str)
    except ValueError as e:
        await query.edit_message_text(
            f"❌ Invalid amount: {str(e)}\n\nReturning to main menu.",
            reply_markup=build_back_button()
        )
        return ConversationHandler.END

    coin = context.user_data['market_coin']
    is_buy = context.user_data['market_is_buy']
    side_str = context.user_data['market_side_str']

    # Show loading
    await query.edit_message_text(f"⏳ Fetching {coin} price...")

    # Convert USD to coin size
    try:
        coin_size, current_price = convert_usd_to_coin(usd_amount, coin)
    except (ValueError, RuntimeError) as e:
        await query.edit_message_text(
            f"❌ {str(e)}\n\nReturning to main menu.",
            reply_markup=build_back_button()
        )
        return ConversationHandler.END

    # Store for confirmation
    context.user_data['market_usd'] = usd_amount
    context.user_data['market_coin_size'] = coin_size
    context.user_data['market_price'] = current_price

    # Show confirmation
    side_emoji = "🟢" if is_buy else "🔴"
    text = (
        f"{side_emoji} **Confirm Market Order**\n\n"
        f"**Coin**: {coin}\n"
        f"**Side**: {side_str}\n"
        f"**USD Amount**: {format_usd_amount(usd_amount)}\n"
        f"**Coin Size**: {format_coin_amount(coin_size, coin)}\n"
        f"**Current Price**: ${current_price:,.2f}\n\n"
        f"⚠️ Market order will execute at best available price.\n"
        f"Slippage may occur.\n\n"
        f"_Environment: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}_"
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=build_confirm_cancel("market", "")
    )

    return MARKET_CONFIRM


async def market_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom amount input request."""
    query = update.callback_query
    await query.answer()

    coin = context.user_data['market_coin']
    side_str = context.user_data['market_side_str']

    text = (
        f"✏️ **{side_str} {coin}**\n\n"
        f"Enter USD amount:\n\n"
        f"Example: `100` or `$50.25`\n\n"
        f"Type the amount and send it."
    )

    await query.edit_message_text(text, parse_mode="Markdown")

    return MARKET_AMOUNT


async def market_amount_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for custom amount."""
    amount_str = update.message.text

    try:
        usd_amount = parse_usd_amount(amount_str)
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid amount: {str(e)}\n\nPlease try again or /cancel"
        )
        return MARKET_AMOUNT

    coin = context.user_data['market_coin']
    is_buy = context.user_data['market_is_buy']
    side_str = context.user_data['market_side_str']

    # Show loading
    msg = await update.message.reply_text(f"⏳ Fetching {coin} price...")

    # Convert USD to coin size
    try:
        coin_size, current_price = convert_usd_to_coin(usd_amount, coin)
    except (ValueError, RuntimeError) as e:
        await msg.edit_text(
            f"❌ {str(e)}\n\nReturning to main menu.",
            reply_markup=build_back_button()
        )
        return ConversationHandler.END

    # Store for confirmation
    context.user_data['market_usd'] = usd_amount
    context.user_data['market_coin_size'] = coin_size
    context.user_data['market_price'] = current_price

    # Show confirmation
    side_emoji = "🟢" if is_buy else "🔴"
    text = (
        f"{side_emoji} **Confirm Market Order**\n\n"
        f"**Coin**: {coin}\n"
        f"**Side**: {side_str}\n"
        f"**USD Amount**: {format_usd_amount(usd_amount)}\n"
        f"**Coin Size**: {format_coin_amount(coin_size, coin)}\n"
        f"**Current Price**: ${current_price:,.2f}\n\n"
        f"⚠️ Market order will execute at best available price.\n"
        f"Slippage may occur.\n\n"
        f"_Environment: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}_"
    )

    await msg.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=build_confirm_cancel("market", "")
    )

    return MARKET_CONFIRM


async def market_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the market order."""
    query = update.callback_query
    await query.answer()

    coin = context.user_data['market_coin']
    is_buy = context.user_data['market_is_buy']
    side_str = context.user_data['market_side_str']
    coin_size = context.user_data['market_coin_size']

    try:
        # Show processing
        await query.edit_message_text(f"⏳ Placing {side_str} order for {coin}...")

        # Create use case request
        request = PlaceOrderRequest(
            coin=coin,
            is_buy=is_buy,
            coin_size=coin_size,
            is_market=True,
        )

        # Execute use case
        response = await place_order_use_case.execute(request)

        # Format response details
        usd_str = f"\n**USD Amount**: {format_usd_amount(response.usd_value)}"
        price_str = f"\n**Execution Price**: ${response.price:,.2f}" if response.price else ""

        # Show result
        side_emoji = "🟢" if is_buy else "🔴"
        success_msg = (
            f"{side_emoji} **Market Order Placed**\n\n"
            f"**Coin**: {coin}\n"
            f"**Side**: {side_str}\n"
            f"**Coin Size**: {format_coin_amount(response.size, coin)}{usd_str}{price_str}\n"
            f"**Status**: {response.status}\n\n"
            f"✅ Order submitted to exchange!"
        )

        await query.edit_message_text(
            success_msg,
            parse_mode="Markdown",
            reply_markup=build_main_menu()
        )

    except Exception as e:
        logger.exception(f"Failed to place market order for {coin}")
        await query.edit_message_text(
            f"❌ Failed to place order:\n`{str(e)}`",
            parse_mode="Markdown",
            reply_markup=build_main_menu()
        )

    # Clean up user data
    context.user_data.clear()

    return ConversationHandler.END


async def wizard_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel any wizard and return to main menu."""
    query = update.callback_query
    if query:
        await query.answer()

    # Clean up user data
    context.user_data.clear()

    text = "❌ Operation cancelled.\n\nReturning to main menu..."

    if query:
        await query.edit_message_text(
            text,
            reply_markup=build_main_menu()
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=build_main_menu()
        )

    return ConversationHandler.END


# ============================================================================
# Conversation Handler Setup
# ============================================================================

def get_market_wizard_handler():
    """Build and return the market order wizard ConversationHandler."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(market_wizard_start, pattern="^menu_market$")
        ],
        states={
            MARKET_COIN: [
                CallbackQueryHandler(market_coin_selected, pattern="^select_coin:"),
                CallbackQueryHandler(wizard_cancel, pattern="^menu_main$"),
            ],
            MARKET_SIDE: [
                CallbackQueryHandler(market_side_selected, pattern="^side_(buy|sell):"),
                CallbackQueryHandler(wizard_cancel, pattern="^menu_main$"),
            ],
            MARKET_AMOUNT: [
                CallbackQueryHandler(market_amount_selected, pattern="^amount:"),
                CallbackQueryHandler(market_custom_amount, pattern="^custom_amount$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, market_amount_text_input),
                CallbackQueryHandler(wizard_cancel, pattern="^menu_main$"),
            ],
            MARKET_CONFIRM: [
                CallbackQueryHandler(market_execute, pattern="^confirm_market:"),
                CallbackQueryHandler(wizard_cancel, pattern="^menu_main$"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(wizard_cancel, pattern="^menu_main$"),
        ],
        name="market_wizard",
        persistent=False,
    )


# ============================================================================
# Close Position Handler (Simple flow - select then confirm)
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
            reply_markup=build_confirm_cancel("close_pos", coin)
        )

    except ValueError as e:
        await query.edit_message_text(
            f"❌ {str(e)}",
            reply_markup=build_back_button()
        )
    except Exception as e:
        logger.exception(f"Failed to get position details for {coin}")
        await query.edit_message_text(
            f"❌ Error: `{str(e)}`",
            parse_mode="Markdown",
            reply_markup=build_back_button()
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

        await query.edit_message_text(
            success_msg,
            parse_mode="Markdown",
            reply_markup=build_main_menu()
        )

    except Exception as e:
        logger.exception(f"Failed to close position {coin}")
        await query.edit_message_text(
            f"❌ Failed to close position:\n`{str(e)}`",
            parse_mode="Markdown",
            reply_markup=build_main_menu()
        )


def get_close_position_handlers():
    """Return list of callback handlers for close position flow."""
    return [
        CallbackQueryHandler(close_position_selected, pattern="^select_position:"),
        CallbackQueryHandler(close_position_execute, pattern="^confirm_close_pos:"),
    ]
