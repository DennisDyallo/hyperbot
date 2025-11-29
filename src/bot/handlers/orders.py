"""
Order management handlers for Telegram bot.

Provides commands and interactions for viewing and canceling outstanding orders.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.bot.middleware import authorized_only
from src.config import logger
from src.use_cases.trading import (
    CancelBulkOrdersRequest,
    CancelBulkOrdersUseCase,
    CancelOrderRequest,
    CancelOrderUseCase,
    ListOrdersRequest,
    ListOrdersUseCase,
)

# Initialize use cases
list_orders_use_case = ListOrdersUseCase()
cancel_order_use_case = CancelOrderUseCase()
cancel_bulk_orders_use_case = CancelBulkOrdersUseCase()

# Conversation states (for future use if needed)
SELECTING_FILTER, CONFIRMING_CANCEL, CONFIRMING_BULK_CANCEL = range(3)


# ============================================================================
# Keyboard Builders
# ============================================================================


def build_orders_menu() -> InlineKeyboardMarkup:
    """Build main orders management menu."""
    keyboard = [
        [
            InlineKeyboardButton("📋 View All Orders", callback_data="orders_view_all"),
        ],
        [
            InlineKeyboardButton("🔍 Filter by Coin", callback_data="orders_filter_coin"),
            InlineKeyboardButton("🔍 Filter by Side", callback_data="orders_filter_side"),
        ],
        [
            InlineKeyboardButton("🗑️ Cancel All Orders", callback_data="orders_cancel_all"),
        ],
        [
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_order_actions_menu(coin: str, order_id: int) -> InlineKeyboardMarkup:
    """Build action menu for a specific order."""
    keyboard = [
        [
            InlineKeyboardButton(
                "❌ Cancel This Order", callback_data=f"cancel_order:{coin}:{order_id}"
            ),
        ],
        [
            InlineKeyboardButton("« Back to Orders", callback_data="orders_view_all"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_confirmation_menu(action: str) -> InlineKeyboardMarkup:
    """Build confirmation menu for destructive actions."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}"),
            InlineKeyboardButton("❌ Cancel", callback_data="orders_view_all"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_side_filter_menu() -> InlineKeyboardMarkup:
    """Build menu for filtering by side (buy/sell)."""
    keyboard = [
        [
            InlineKeyboardButton("🟢 Buy Orders", callback_data="orders_filter_side:buy"),
            InlineKeyboardButton("🔴 Sell Orders", callback_data="orders_filter_side:sell"),
        ],
        [
            InlineKeyboardButton("📋 All Orders", callback_data="orders_view_all"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================================================
# Command Handlers
# ============================================================================


@authorized_only
async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /orders command.
    Shows orders management menu.
    """
    assert update.message is not None

    menu_text = (
        "📋 **Outstanding Orders Management**\n\n"
        "View and manage your open orders.\n"
        "Select an option below:"
    )

    await update.message.reply_text(
        menu_text, parse_mode="Markdown", reply_markup=build_orders_menu()
    )


# ============================================================================
# Callback Query Handlers
# ============================================================================


async def handle_view_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display all outstanding orders."""
    assert update.callback_query is not None
    query = update.callback_query
    await query.answer()

    try:
        # Fetch all orders (no filters)
        request = ListOrdersRequest(coin=None, side=None, order_type=None)
        response = await list_orders_use_case.execute(request)

        if response.status == "failed":
            await query.edit_message_text(
                f"❌ Failed to fetch orders:\n{response.message}",
                parse_mode="Markdown",
                reply_markup=build_orders_menu(),
            )
            return

        if response.total_count == 0:
            await query.edit_message_text(
                "✅ You have no outstanding orders.",
                parse_mode="Markdown",
                reply_markup=build_orders_menu(),
            )
            return

        # Format orders list (paginate if > 10 orders)
        orders_text = f"📋 **Outstanding Orders** ({response.total_count})\n\n"

        for idx, order in enumerate(response.orders[:10], 1):
            side_emoji = "🟢" if order.side == "buy" else "🔴"
            price_str = f"@ ${order.limit_price:.2f}" if order.limit_price else "Market"

            orders_text += (
                f"{idx}. {side_emoji} **{order.coin}** - {order.size} {order.coin}\n"
                f"   {order.order_type.title()} {price_str}\n"
                f"   ID: `{order.order_id}`\n\n"
            )

        if response.total_count > 10:
            orders_text += f"\n_Showing first 10 of {response.total_count} orders_\n"

        # Build inline keyboard with order actions
        keyboard = []
        for order in response.orders[:10]:
            side_emoji = "🟢" if order.side == "buy" else "🔴"
            label = f"{side_emoji} Cancel {order.coin} #{order.order_id}"
            callback = f"cancel_order:{order.coin}:{order.order_id}"
            keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

        # Add bulk actions
        if response.total_count > 1:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🗑️ Cancel All Orders", callback_data="orders_cancel_all_confirm"
                    )
                ]
            )

        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])

        await query.edit_message_text(
            orders_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        await query.edit_message_text(
            f"❌ Error: {str(e)}", parse_mode="Markdown", reply_markup=build_orders_menu()
        )


async def handle_filter_by_side(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show side filter menu."""
    assert update.callback_query is not None
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🔍 **Filter by Side**\n\nSelect order side:",
        parse_mode="Markdown",
        reply_markup=build_side_filter_menu(),
    )


async def handle_filter_side_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle side filter selection (buy/sell)."""
    assert update.callback_query is not None
    query = update.callback_query
    await query.answer()

    # Extract side from callback data
    side = query.data.split(":")[1] if ":" in query.data else None  # type: ignore

    if not side:
        await query.edit_message_text("❌ Invalid selection", reply_markup=build_orders_menu())
        return

    try:
        # Fetch orders filtered by side
        request = ListOrdersRequest(coin=None, side=side, order_type=None)
        response = await list_orders_use_case.execute(request)

        if response.status == "failed":
            await query.edit_message_text(
                f"❌ Failed: {response.message}", reply_markup=build_orders_menu()
            )
            return

        side_emoji = "🟢" if side == "buy" else "🔴"
        side_label = "Buy" if side == "buy" else "Sell"

        if response.total_count == 0:
            await query.edit_message_text(
                f"{side_emoji} No {side_label} orders found.",
                parse_mode="Markdown",
                reply_markup=build_orders_menu(),
            )
            return

        # Format filtered orders
        orders_text = f"{side_emoji} **{side_label} Orders** ({response.total_count})\n\n"

        for idx, order in enumerate(response.orders[:10], 1):
            price_str = f"@ ${order.limit_price:.2f}" if order.limit_price else "Market"
            orders_text += (
                f"{idx}. **{order.coin}** - {order.size} {order.coin}\n"
                f"   {order.order_type.title()} {price_str}\n"
                f"   ID: `{order.order_id}`\n\n"
            )

        # Build keyboard
        keyboard = []
        for order in response.orders[:10]:
            label = f"Cancel {order.coin} #{order.order_id}"
            callback = f"cancel_order:{order.coin}:{order.order_id}"
            keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

        keyboard.append([InlineKeyboardButton("« Back", callback_data="orders_filter_side")])
        keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])

        await query.edit_message_text(
            orders_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Error filtering orders: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}", reply_markup=build_orders_menu())


async def handle_cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle individual order cancellation."""
    assert update.callback_query is not None
    query = update.callback_query
    await query.answer()

    try:
        # Parse callback data: "cancel_order:BTC:12345"
        parts = query.data.split(":")  # type: ignore
        if len(parts) != 3:
            await query.edit_message_text("❌ Invalid order data", reply_markup=build_orders_menu())
            return

        coin = parts[1]
        order_id = int(parts[2])

        # Show confirmation
        confirm_text = (
            f"⚠️ **Confirm Order Cancellation**\n\n"
            f"Coin: **{coin}**\n"
            f"Order ID: `{order_id}`\n\n"
            f"Are you sure you want to cancel this order?"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Yes, Cancel", callback_data=f"confirm_cancel:{coin}:{order_id}"
                ),
            ],
            [
                InlineKeyboardButton("❌ No, Go Back", callback_data="orders_view_all"),
            ],
        ]

        await query.edit_message_text(
            confirm_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Error preparing cancellation: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}", reply_markup=build_orders_menu())


async def handle_confirm_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute individual order cancellation after confirmation."""
    assert update.callback_query is not None
    query = update.callback_query
    await query.answer()

    try:
        # Parse callback data: "confirm_cancel:BTC:12345"
        parts = query.data.split(":")  # type: ignore
        if len(parts) != 3:
            await query.edit_message_text("❌ Invalid data", reply_markup=build_orders_menu())
            return

        coin = parts[1]
        order_id = int(parts[2])

        # Execute cancellation
        await query.edit_message_text(f"⏳ Canceling order {coin} #{order_id}...")

        request = CancelOrderRequest(coin=coin, order_id=order_id)
        response = await cancel_order_use_case.execute(request)

        if response.status == "success":
            result_text = (
                f"✅ **Order Canceled**\n\n"
                f"Coin: **{coin}**\n"
                f"Order ID: `{order_id}`\n\n"
                f"{response.message}"
            )
        else:
            result_text = (
                f"❌ **Cancellation Failed**\n\n"
                f"Coin: **{coin}**\n"
                f"Order ID: `{order_id}`\n\n"
                f"Error: {response.message}"
            )

        keyboard = [
            [InlineKeyboardButton("📋 View Orders", callback_data="orders_view_all")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
        ]

        await query.edit_message_text(
            result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Error canceling order: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}", reply_markup=build_orders_menu())


async def handle_cancel_all_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show confirmation for canceling all orders."""
    assert update.callback_query is not None
    query = update.callback_query
    await query.answer()

    confirm_text = (
        "⚠️ **Confirm Cancel All Orders**\n\n"
        "This will cancel ALL outstanding orders.\n\n"
        "Are you sure you want to continue?"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, Cancel All", callback_data="confirm_cancel_all"),
        ],
        [
            InlineKeyboardButton("❌ No, Go Back", callback_data="orders_view_all"),
        ],
    ]

    await query.edit_message_text(
        confirm_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_confirm_cancel_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Execute cancel all orders after confirmation."""
    assert update.callback_query is not None
    query = update.callback_query
    await query.answer()

    try:
        await query.edit_message_text("⏳ Canceling all orders...")

        request = CancelBulkOrdersRequest(cancel_all=True)
        response = await cancel_bulk_orders_use_case.execute(request)

        if response.status == "success":
            result_text = (
                f"✅ **All Orders Canceled**\n\n"
                f"Total canceled: {response.successful}\n\n"
                f"{response.message}"
            )
        elif response.status == "partial":
            result_text = (
                f"⚠️ **Partial Success**\n\n"
                f"Successful: {response.successful}\n"
                f"Failed: {response.failed}\n\n"
                f"{response.message}"
            )
        else:
            result_text = f"❌ **Cancellation Failed**\n\nError: {response.message}"

        keyboard = [
            [InlineKeyboardButton("📋 View Orders", callback_data="orders_view_all")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
        ]

        await query.edit_message_text(
            result_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Error canceling all orders: {e}")
        await query.edit_message_text(f"❌ Error: {str(e)}", reply_markup=build_orders_menu())


# ============================================================================
# Handler Registration
# ============================================================================


def get_orders_handlers() -> list:
    """
    Get all order management handlers.

    Returns:
        List of handlers to register with the application
    """
    return [
        CommandHandler("orders", orders_command),
        CallbackQueryHandler(handle_view_all_orders, pattern="^orders_view_all$"),
        CallbackQueryHandler(handle_filter_by_side, pattern="^orders_filter_side$"),
        CallbackQueryHandler(handle_filter_side_selection, pattern="^orders_filter_side:"),
        CallbackQueryHandler(handle_cancel_order, pattern="^cancel_order:"),
        CallbackQueryHandler(handle_confirm_cancel, pattern="^confirm_cancel:"),
        CallbackQueryHandler(handle_cancel_all_confirm, pattern="^orders_cancel_all_confirm$"),
        CallbackQueryHandler(handle_confirm_cancel_all, pattern="^confirm_cancel_all$"),
    ]
