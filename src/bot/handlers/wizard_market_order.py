"""
Market Order Wizard - Multi-step ConversationHandler for market orders.

Guides users through:
1. Coin selection
2. Buy/Sell direction
3. USD amount (preset or custom)
4. Confirmation and execution
"""

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.bot.menus import (
    build_buy_sell_menu,
    build_coin_selection_menu,
    build_confirm_cancel,
    build_quick_amounts_menu,
)
from src.bot.middleware import authorized_only
from src.bot.utils import (
    convert_usd_to_coin,
    format_coin_amount,
    format_usd_amount,
    parse_usd_amount,
    send_cancel_and_end,
    send_error_and_end,
    send_success_and_end,
)
from src.config import logger, settings
from src.use_cases.trading import (
    PlaceOrderRequest,
    PlaceOrderUseCase,
)

# Initialize use case
place_order_use_case = PlaceOrderUseCase()

# Conversation states
MARKET_COIN, MARKET_SIDE, MARKET_AMOUNT, MARKET_CONFIRM = range(4)


# ============================================================================
# Market Order Wizard Handlers
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
        text, parse_mode="Markdown", reply_markup=build_coin_selection_menu()
    )

    return MARKET_COIN


async def market_coin_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle coin selection - ask for buy/sell."""
    query = update.callback_query
    await query.answer()

    # Extract coin from callback data
    coin = query.data.split(":")[1]
    context.user_data["market_coin"] = coin

    text = f"💰 **Market Order: {coin}**\n\nStep 2/3: Buy or Sell?\n\nSelect order side:"

    await query.edit_message_text(
        text, parse_mode="Markdown", reply_markup=build_buy_sell_menu(coin)
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

    context.user_data["market_is_buy"] = is_buy
    context.user_data["market_side_str"] = side_str.upper()

    side_emoji = "🟢" if is_buy else "🔴"

    text = (
        f"{side_emoji} **{side_str.upper()} {coin}**\n\n"
        f"Step 3/3: Enter amount in USD\n\n"
        f"Choose a preset amount or enter custom:"
    )

    await query.edit_message_text(
        text, parse_mode="Markdown", reply_markup=build_quick_amounts_menu()
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
        # Use utility function - automatically shows main menu!
        return await send_error_and_end(
            update, f"❌ Invalid amount: {str(e)}\n\nReturning to main menu."
        )

    coin = context.user_data["market_coin"]
    is_buy = context.user_data["market_is_buy"]
    side_str = context.user_data["market_side_str"]

    # Show loading
    await query.edit_message_text(f"⏳ Fetching {coin} price...")

    # Convert USD to coin size
    try:
        coin_size, current_price = convert_usd_to_coin(usd_amount, coin)
    except (ValueError, RuntimeError) as e:
        # Use utility function - automatically shows main menu!
        return await send_error_and_end(update, f"❌ {str(e)}\n\nReturning to main menu.")

    # Store for confirmation
    context.user_data["market_usd"] = usd_amount
    context.user_data["market_coin_size"] = coin_size
    context.user_data["market_price"] = current_price

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
        text, parse_mode="Markdown", reply_markup=build_confirm_cancel("market", "")
    )

    return MARKET_CONFIRM


async def market_custom_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom amount input request."""
    query = update.callback_query
    await query.answer()

    coin = context.user_data["market_coin"]
    side_str = context.user_data["market_side_str"]

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

    coin = context.user_data["market_coin"]
    is_buy = context.user_data["market_is_buy"]
    side_str = context.user_data["market_side_str"]

    # Show loading
    msg = await update.message.reply_text(f"⏳ Fetching {coin} price...")

    # Convert USD to coin size
    try:
        coin_size, current_price = convert_usd_to_coin(usd_amount, coin)
    except (ValueError, RuntimeError) as e:
        # Use utility function - automatically shows main menu!
        return await send_error_and_end(update, f"❌ {str(e)}\n\nReturning to main menu.")

    # Store for confirmation
    context.user_data["market_usd"] = usd_amount
    context.user_data["market_coin_size"] = coin_size
    context.user_data["market_price"] = current_price

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
        text, parse_mode="Markdown", reply_markup=build_confirm_cancel("market", "")
    )

    return MARKET_CONFIRM


async def market_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute the market order."""
    query = update.callback_query
    await query.answer()

    coin = context.user_data["market_coin"]
    is_buy = context.user_data["market_is_buy"]
    side_str = context.user_data["market_side_str"]
    coin_size = context.user_data["market_coin_size"]

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

        # Clean up user data
        context.user_data.clear()

        # Use utility function - automatically shows main menu!
        return await send_success_and_end(update, success_msg)

    except Exception as e:
        logger.exception(f"Failed to place market order for {coin}")
        # Clean up user data
        context.user_data.clear()

        # Use utility function - automatically shows main menu!
        return await send_error_and_end(update, f"❌ Failed to place order:\n`{str(e)}`")


async def wizard_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel any wizard and return to main menu."""
    query = update.callback_query
    if query:
        await query.answer()

    # Clean up user data
    context.user_data.clear()

    # Use utility function - automatically shows main menu!
    return await send_cancel_and_end(update, "❌ Operation cancelled.\n\nReturning to main menu...")


# ============================================================================
# Conversation Handler Setup
# ============================================================================


def get_market_wizard_handler():
    """Build and return the market order wizard ConversationHandler."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(market_wizard_start, pattern="^menu_market$")],
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
