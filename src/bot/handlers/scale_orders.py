"""
Scale Order wizard handler for Telegram bot.

Provides an interactive, user-friendly wizard for creating scale orders
using inline keyboards and conversational flow.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from src.bot.middleware import authorized_only
from src.services.scale_order_service import scale_order_service
from src.services.market_data_service import market_data_service
from src.models.scale_order import ScaleOrderConfig
from src.config import logger
from typing import Dict, Any

# Conversation states
(
    SELECT_COIN,
    SELECT_DIRECTION,
    SELECT_RANGE_METHOD,
    ENTER_TARGET_PRICE,
    SELECT_RANGE_WIDTH,
    ENTER_MIN_PRICE,
    ENTER_MAX_PRICE,
    SELECT_NUM_ORDERS,
    ENTER_CUSTOM_NUM_ORDERS,
    ENTER_TOTAL_SIZE,
    SELECT_DISTRIBUTION,
    PREVIEW_CONFIRM,
) = range(12)


class ScaleOrderWizard:
    """Wizard for creating scale orders step-by-step."""

    @staticmethod
    @authorized_only
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the scale order wizard."""
        # Clear any previous wizard data
        context.user_data.clear()

        await update.message.reply_text(
            "📊 *Scale Order Wizard*\n\n"
            "Let's create a scale order to gradually build or exit a position.\n\n"
            "First, which coin would you like to trade?\n"
            "_(Example: BTC, ETH, SOL)_",
            parse_mode="Markdown"
        )

        return SELECT_COIN

    @staticmethod
    async def select_coin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle coin selection."""
        coin = update.message.text.strip().upper()

        # Validate coin exists
        try:
            current_price = market_data_service.get_price(coin)
            context.user_data["coin"] = coin
            context.user_data["current_price"] = current_price

            # Ask for direction
            keyboard = [
                [InlineKeyboardButton("📈 Scale IN (Buy as price drops)", callback_data="direction_in")],
                [InlineKeyboardButton("📉 Scale OUT (Sell as price rises)", callback_data="direction_out")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"✅ {coin} selected (Current price: ${current_price:,.2f})\n\n"
                f"*What would you like to do?*\n\n"
                f"📈 *Scale IN*: Buy progressively as price drops (accumulate)\n"
                f"📉 *Scale OUT*: Sell progressively as price rises (take profits)",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

            return SELECT_DIRECTION

        except Exception as e:
            await update.message.reply_text(
                f"❌ Error: Could not find price for {coin}.\n"
                f"Please enter a valid coin symbol."
            )
            return SELECT_COIN

    @staticmethod
    async def select_direction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle direction selection (Scale IN vs OUT)."""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("❌ Scale order cancelled.")
            return ConversationHandler.END

        is_buy = query.data == "direction_in"
        context.user_data["is_buy"] = is_buy
        direction_text = "Scale IN (Buy)" if is_buy else "Scale OUT (Sell)"

        # Ask for range method
        keyboard = [
            [InlineKeyboardButton("🎯 Auto Range (I'll set a target price)", callback_data="range_auto")],
            [InlineKeyboardButton("✍️ Manual Range (I'll set min/max)", callback_data="range_manual")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"✅ Direction: *{direction_text}*\n\n"
            f"*How would you like to set the price range?*\n\n"
            f"🎯 *Auto*: Just tell me your target price, I'll calculate the range\n"
            f"✍️ *Manual*: You specify exact min and max prices",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        return SELECT_RANGE_METHOD

    @staticmethod
    async def select_range_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle range method selection (Auto vs Manual)."""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("❌ Scale order cancelled.")
            return ConversationHandler.END

        is_auto = query.data == "range_auto"
        context.user_data["range_auto"] = is_auto

        coin = context.user_data["coin"]
        current_price = context.user_data["current_price"]
        is_buy = context.user_data["is_buy"]

        if is_auto:
            # Auto mode - ask for target price
            direction_hint = "drop to" if is_buy else "rise to"
            await query.edit_message_text(
                f"🎯 *Auto Range Mode*\n\n"
                f"Current {coin} price: ${current_price:,.2f}\n\n"
                f"What price do you expect {coin} to {direction_hint}?\n"
                f"_(Enter target price)_",
                parse_mode="Markdown"
            )
            return ENTER_TARGET_PRICE
        else:
            # Manual mode - ask for min price
            await query.edit_message_text(
                f"✍️ *Manual Range Mode*\n\n"
                f"Current {coin} price: ${current_price:,.2f}\n\n"
                f"Enter the *minimum* price for your range:",
                parse_mode="Markdown"
            )
            return ENTER_MIN_PRICE

    @staticmethod
    async def enter_target_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle target price input for auto mode."""
        try:
            target_price = float(update.message.text.strip())
            context.user_data["target_price"] = target_price

            current_price = context.user_data["current_price"]
            is_buy = context.user_data["is_buy"]
            coin = context.user_data["coin"]

            # Validate direction makes sense
            if is_buy and target_price > current_price:
                await update.message.reply_text(
                    f"⚠️ For Scale IN (buy), target should be *below* current price.\n"
                    f"Current: ${current_price:,.2f}, Target: ${target_price:,.2f}\n\n"
                    f"Please enter a lower target price:",
                    parse_mode="Markdown"
                )
                return ENTER_TARGET_PRICE

            if not is_buy and target_price < current_price:
                await update.message.reply_text(
                    f"⚠️ For Scale OUT (sell), target should be *above* current price.\n"
                    f"Current: ${current_price:,.2f}, Target: ${target_price:,.2f}\n\n"
                    f"Please enter a higher target price:",
                    parse_mode="Markdown"
                )
                return ENTER_TARGET_PRICE

            # Ask for range width
            keyboard = [
                [InlineKeyboardButton("Tight Range (±5%)", callback_data="width_5")],
                [InlineKeyboardButton("Medium Range (±10%)", callback_data="width_10")],
                [InlineKeyboardButton("Wide Range (±15%)", callback_data="width_15")],
                [InlineKeyboardButton("From Current to Target", callback_data="width_current")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            direction = "down" if is_buy else "up"
            pct_move = abs((target_price - current_price) / current_price * 100)

            await update.message.reply_text(
                f"✅ Target: ${target_price:,.2f} ({pct_move:.1f}% {direction})\n\n"
                f"*How wide should the range be?*\n\n"
                f"This determines how spread out your orders will be.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

            return SELECT_RANGE_WIDTH

        except ValueError:
            await update.message.reply_text(
                "❌ Invalid price. Please enter a number (e.g., 95000):"
            )
            return ENTER_TARGET_PRICE

    @staticmethod
    async def select_range_width(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle range width selection for auto mode."""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("❌ Scale order cancelled.")
            return ConversationHandler.END

        current_price = context.user_data["current_price"]
        target_price = context.user_data["target_price"]
        is_buy = context.user_data["is_buy"]

        # Calculate range based on selection
        if query.data == "width_current":
            # Simple: from current to target
            start_price = current_price
            end_price = target_price
        else:
            # Use percentage width around target
            width_pct = int(query.data.split("_")[1]) / 100  # 5, 10, or 15 → 0.05, 0.10, 0.15

            if is_buy:
                # Scale IN: range goes from higher to lower
                # Target is the low end, add width above it
                end_price = target_price
                start_price = target_price * (1 + width_pct)
            else:
                # Scale OUT: range goes from lower to higher
                # Target is the high end, subtract width below it
                start_price = target_price * (1 - width_pct)
                end_price = target_price

        context.user_data["start_price"] = start_price
        context.user_data["end_price"] = end_price

        # Continue to number of orders
        return await ScaleOrderWizard._ask_num_orders(query, context)

    @staticmethod
    async def enter_min_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle minimum price input for manual mode."""
        try:
            min_price = float(update.message.text.strip())
            context.user_data["min_price"] = min_price

            coin = context.user_data["coin"]
            current_price = context.user_data["current_price"]

            await update.message.reply_text(
                f"✅ Minimum price: ${min_price:,.2f}\n\n"
                f"Current {coin} price: ${current_price:,.2f}\n\n"
                f"Now enter the *maximum* price for your range:",
                parse_mode="Markdown"
            )

            return ENTER_MAX_PRICE

        except ValueError:
            await update.message.reply_text(
                "❌ Invalid price. Please enter a number (e.g., 48000):"
            )
            return ENTER_MIN_PRICE

    @staticmethod
    async def enter_max_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle maximum price input for manual mode."""
        try:
            max_price = float(update.message.text.strip())
            min_price = context.user_data["min_price"]

            if max_price <= min_price:
                await update.message.reply_text(
                    f"❌ Maximum price (${max_price:,.2f}) must be *higher* than minimum (${min_price:,.2f}).\n\n"
                    f"Please enter a higher maximum price:",
                    parse_mode="Markdown"
                )
                return ENTER_MAX_PRICE

            is_buy = context.user_data["is_buy"]

            # For scale orders, start_price > end_price for buys, opposite for sells
            if is_buy:
                context.user_data["start_price"] = max_price
                context.user_data["end_price"] = min_price
            else:
                context.user_data["start_price"] = min_price
                context.user_data["end_price"] = max_price

            # Continue to number of orders
            return await ScaleOrderWizard._ask_num_orders_message(update, context)

        except ValueError:
            await update.message.reply_text(
                "❌ Invalid price. Please enter a number (e.g., 52000):"
            )
            return ENTER_MAX_PRICE

    @staticmethod
    async def _ask_num_orders(query, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Helper to ask for number of orders (after callback query)."""
        keyboard = [
            [InlineKeyboardButton("3 orders", callback_data="num_3")],
            [InlineKeyboardButton("5 orders (Recommended)", callback_data="num_5")],
            [InlineKeyboardButton("10 orders", callback_data="num_10")],
            [InlineKeyboardButton("Custom", callback_data="num_custom")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        start = context.user_data["start_price"]
        end = context.user_data["end_price"]
        range_pct = abs((end - start) / start * 100)

        await query.edit_message_text(
            f"✅ Price range: ${min(start, end):,.2f} - ${max(start, end):,.2f} ({range_pct:.1f}% range)\n\n"
            f"*How many orders should I place?*\n\n"
            f"More orders = smoother distribution, but more fees",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        return SELECT_NUM_ORDERS

    @staticmethod
    async def _ask_num_orders_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Helper to ask for number of orders (after text message)."""
        keyboard = [
            [InlineKeyboardButton("3 orders", callback_data="num_3")],
            [InlineKeyboardButton("5 orders (Recommended)", callback_data="num_5")],
            [InlineKeyboardButton("10 orders", callback_data="num_10")],
            [InlineKeyboardButton("Custom", callback_data="num_custom")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        start = context.user_data["start_price"]
        end = context.user_data["end_price"]
        range_pct = abs((end - start) / start * 100)

        await update.message.reply_text(
            f"✅ Price range: ${min(start, end):,.2f} - ${max(start, end):,.2f} ({range_pct:.1f}% range)\n\n"
            f"*How many orders should I place?*\n\n"
            f"More orders = smoother distribution, but more fees",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

        return SELECT_NUM_ORDERS

    @staticmethod
    async def select_num_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle number of orders selection."""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("❌ Scale order cancelled.")
            return ConversationHandler.END

        if query.data == "num_custom":
            await query.edit_message_text(
                "Enter custom number of orders (2-20):",
                parse_mode="Markdown"
            )
            return ENTER_CUSTOM_NUM_ORDERS

        # Extract number from callback data
        num_orders = int(query.data.split("_")[1])
        context.user_data["num_orders"] = num_orders

        # Ask for total size
        coin = context.user_data["coin"]
        await query.edit_message_text(
            f"✅ Number of orders: {num_orders}\n\n"
            f"What's the *total size* you want to trade?\n"
            f"_(Enter size in {coin}, e.g., 0.1)_",
            parse_mode="Markdown"
        )

        return ENTER_TOTAL_SIZE

    @staticmethod
    async def enter_custom_num_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle custom number of orders input."""
        try:
            num_orders = int(update.message.text.strip())

            if num_orders < 2 or num_orders > 20:
                await update.message.reply_text(
                    "❌ Number of orders must be between 2 and 20.\n"
                    "Please enter a valid number:"
                )
                return ENTER_CUSTOM_NUM_ORDERS

            context.user_data["num_orders"] = num_orders

            # Ask for total size
            coin = context.user_data["coin"]
            await update.message.reply_text(
                f"✅ Number of orders: {num_orders}\n\n"
                f"What's the *total size* you want to trade?\n"
                f"_(Enter size in {coin}, e.g., 0.1)_",
                parse_mode="Markdown"
            )

            return ENTER_TOTAL_SIZE

        except ValueError:
            await update.message.reply_text(
                "❌ Invalid number. Please enter a whole number between 2 and 20:"
            )
            return ENTER_CUSTOM_NUM_ORDERS

    @staticmethod
    async def enter_total_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle total size input."""
        try:
            total_size = float(update.message.text.strip())

            if total_size <= 0:
                await update.message.reply_text(
                    "❌ Size must be greater than 0.\n"
                    "Please enter a valid size:"
                )
                return ENTER_TOTAL_SIZE

            context.user_data["total_size"] = total_size

            # Ask for distribution type
            keyboard = [
                [InlineKeyboardButton("📊 Linear (Equal sizes)", callback_data="dist_linear")],
                [InlineKeyboardButton("📈 Geometric (Weighted)", callback_data="dist_geometric")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            coin = context.user_data["coin"]
            num_orders = context.user_data["num_orders"]
            avg_size = total_size / num_orders

            await update.message.reply_text(
                f"✅ Total size: {total_size} {coin}\n\n"
                f"*How should I distribute the size across orders?*\n\n"
                f"📊 *Linear*: Each order has equal size (~{avg_size:.4f} {coin})\n"
                f"📈 *Geometric*: First orders larger, later orders smaller",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

            return SELECT_DISTRIBUTION

        except ValueError:
            await update.message.reply_text(
                "❌ Invalid size. Please enter a number (e.g., 0.5):"
            )
            return ENTER_TOTAL_SIZE

    @staticmethod
    async def select_distribution(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle distribution type selection."""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("❌ Scale order cancelled.")
            return ConversationHandler.END

        distribution = "geometric" if query.data == "dist_geometric" else "linear"
        context.user_data["distribution"] = distribution

        # Generate preview
        try:
            config = ScaleOrderConfig(
                coin=context.user_data["coin"],
                is_buy=context.user_data["is_buy"],
                total_size=context.user_data["total_size"],
                num_orders=context.user_data["num_orders"],
                start_price=context.user_data["start_price"],
                end_price=context.user_data["end_price"],
                distribution_type=distribution
            )

            preview = scale_order_service.preview_scale_order(config)

            # Build preview message
            coin = context.user_data["coin"]
            direction = "BUY" if config.is_buy else "SELL"
            current_price = context.user_data["current_price"]

            preview_text = f"📊 *Scale Order Preview*\n\n"
            preview_text += f"*Coin*: {coin}\n"
            preview_text += f"*Direction*: {direction}\n"
            preview_text += f"*Current Price*: ${current_price:,.2f}\n"
            preview_text += f"*Total Size*: {config.total_size} {coin}\n"
            preview_text += f"*Orders*: {config.num_orders}\n"
            preview_text += f"*Distribution*: {distribution.title()}\n"
            preview_text += f"*Avg Fill Price*: ${preview.estimated_avg_price:,.2f}\n"
            preview_text += f"*Price Range*: {preview.price_range_pct:.1f}%\n\n"

            preview_text += "*Order Breakdown:*\n"
            preview_text += "```\n"
            preview_text += f"{'#':<3} {'Price':<12} {'Size':<10}\n"
            preview_text += "-" * 27 + "\n"

            for i, order in enumerate(preview.orders, 1):
                preview_text += f"{i:<3} ${order['price']:<11,.2f} {order['size']:<10.6f}\n"

            preview_text += "```\n"

            # Confirmation buttons
            keyboard = [
                [InlineKeyboardButton("✅ Execute", callback_data="confirm_execute")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                preview_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

            # Store config for execution
            context.user_data["config"] = config

            return PREVIEW_CONFIRM

        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            await query.edit_message_text(
                f"❌ Error generating preview: {str(e)}\n\n"
                f"Scale order cancelled."
            )
            return ConversationHandler.END

    @staticmethod
    async def preview_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle preview confirmation."""
        query = update.callback_query
        await query.answer()

        if query.data == "cancel":
            await query.edit_message_text("❌ Scale order cancelled.")
            return ConversationHandler.END

        # Execute scale order
        try:
            config: ScaleOrderConfig = context.user_data["config"]

            await query.edit_message_text("⏳ Placing scale order...")

            result = scale_order_service.place_scale_order(config)

            # Format result message
            coin = config.coin
            direction = "BUY" if config.is_buy else "SELL"

            if result.status == "completed":
                msg = f"✅ *Scale Order Placed Successfully!*\n\n"
                msg += f"*Order ID*: `{result.scale_order_id}`\n"
                msg += f"*Coin*: {coin}\n"
                msg += f"*Direction*: {direction}\n"
                msg += f"*Orders Placed*: {result.orders_placed}/{result.num_orders}\n"
                msg += f"*Total Size*: {result.total_placed_size:.6f} {coin}\n"
                if result.average_price:
                    msg += f"*Average Price*: ${result.average_price:,.2f}\n"
                msg += f"\n_Use /scale_status to monitor this order_"
            elif result.status == "partial":
                msg = f"⚠️ *Scale Order Partially Placed*\n\n"
                msg += f"*Order ID*: `{result.scale_order_id}`\n"
                msg += f"*Successful*: {result.orders_placed}/{result.num_orders}\n"
                msg += f"*Failed*: {result.orders_failed}\n"
                msg += f"*Size Placed*: {result.total_placed_size:.6f} {coin}\n\n"
                msg += f"Some orders failed to place. Check logs for details."
            else:
                msg = f"❌ *Scale Order Failed*\n\n"
                msg += f"All {result.num_orders} orders failed to place.\n"
                msg += f"Please check your account and try again."

            await query.edit_message_text(msg, parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Scale order execution failed: {e}")
            await query.edit_message_text(
                f"❌ *Error placing scale order*\n\n"
                f"Error: {str(e)}",
                parse_mode="Markdown"
            )

        return ConversationHandler.END

    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel the conversation."""
        await update.message.reply_text("❌ Scale order wizard cancelled.")
        return ConversationHandler.END


# Create conversation handler
scale_order_conversation = ConversationHandler(
    entry_points=[CommandHandler("scale", ScaleOrderWizard.start)],
    states={
        SELECT_COIN: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScaleOrderWizard.select_coin)
        ],
        SELECT_DIRECTION: [
            CallbackQueryHandler(ScaleOrderWizard.select_direction)
        ],
        SELECT_RANGE_METHOD: [
            CallbackQueryHandler(ScaleOrderWizard.select_range_method)
        ],
        ENTER_TARGET_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScaleOrderWizard.enter_target_price)
        ],
        SELECT_RANGE_WIDTH: [
            CallbackQueryHandler(ScaleOrderWizard.select_range_width)
        ],
        ENTER_MIN_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScaleOrderWizard.enter_min_price)
        ],
        ENTER_MAX_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScaleOrderWizard.enter_max_price)
        ],
        SELECT_NUM_ORDERS: [
            CallbackQueryHandler(ScaleOrderWizard.select_num_orders)
        ],
        ENTER_CUSTOM_NUM_ORDERS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScaleOrderWizard.enter_custom_num_orders)
        ],
        ENTER_TOTAL_SIZE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ScaleOrderWizard.enter_total_size)
        ],
        SELECT_DISTRIBUTION: [
            CallbackQueryHandler(ScaleOrderWizard.select_distribution)
        ],
        PREVIEW_CONFIRM: [
            CallbackQueryHandler(ScaleOrderWizard.preview_confirm)
        ],
    },
    fallbacks=[CommandHandler("cancel", ScaleOrderWizard.cancel)],
    name="scale_order_wizard",
    persistent=False
)
