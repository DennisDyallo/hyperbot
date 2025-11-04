"""
Advanced command handlers for Telegram bot (rebalancing, scale orders).

Reference: docs/telegram/best-practices.md - Multi-step Flows
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from src.bot.middleware import authorized_only
from src.bot.utils import parse_usd_amount, format_coin_amount, format_usd_amount
from src.services.rebalance_service import rebalance_service
from src.services.scale_order_service import scale_order_service
from src.services.position_service import position_service
from src.config import logger, settings


@authorized_only
async def rebalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /rebalance command or menu button.
    Rebalances portfolio with preset options.

    Reference: docs/hyperliquid/api-reference.md - Portfolio Rebalancing
    """
    try:
        # Handle both command and callback query
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            msg = await query.edit_message_text("⏳ Analyzing portfolio...")
        else:
            msg = await update.message.reply_text("⏳ Analyzing portfolio...")

        # Get current positions
        positions = position_service.list_positions()

        if not positions:
            await msg.edit_text("📭 No open positions to rebalance.")
            return

        # Show current allocation
        total_value = sum(abs(p["position"]["position_value"]) for p in positions)

        allocation_text = "📊 **Current Portfolio**\n\n"
        for pos in positions:
            p = pos["position"]
            coin = p["coin"]
            value = abs(p["position_value"])
            pct = (value / total_value * 100) if total_value > 0 else 0
            allocation_text += f"• {coin}: ${value:.2f} ({pct:.1f}%)\n"

        allocation_text += f"\n**Total Value**: ${total_value:.2f}\n\n"
        allocation_text += "**Rebalance Options**:\n"
        allocation_text += "Choose a rebalancing strategy below."

        # Create inline keyboard with preset options
        keyboard = [
            [InlineKeyboardButton("⚖️ Equal Weight", callback_data="rebalance_preview:equal")],
            [InlineKeyboardButton("📊 Custom Weights", callback_data="rebalance_custom")],
            [InlineKeyboardButton("❌ Cancel", callback_data="rebalance_cancel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await msg.edit_text(
            allocation_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.exception("Failed to analyze portfolio for rebalancing")
        error_msg = f"❌ Error: `{str(e)}`"
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(error_msg, parse_mode="Markdown")


async def rebalance_preview_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rebalance preview callback."""
    query = update.callback_query
    await query.answer()

    if query.data == "rebalance_cancel":
        await query.edit_message_text("❌ Rebalancing cancelled.")
        return

    if query.data == "rebalance_custom":
        await query.edit_message_text(
            "📝 **Custom Rebalancing**\n\n"
            "Custom weight rebalancing is not yet implemented.\n"
            "Use `/rebalance` and select equal weight, or use the web dashboard for advanced options."
        )
        return

    # Extract strategy
    _, strategy = query.data.split(":")

    try:
        # Show processing
        await query.edit_message_text("⏳ Generating rebalance plan...")

        # Get positions
        positions = position_service.list_positions()

        # Build target allocations (equal weight)
        num_positions = len(positions)
        target_pct = 100.0 / num_positions if num_positions > 0 else 0

        target_allocations = {
            p["position"]["coin"]: target_pct
            for p in positions
        }

        # Preview rebalance (fix parameter names to match service)
        preview = rebalance_service.preview_rebalance(
            target_weights=target_allocations,  # Service expects "target_weights"
            leverage=3  # Service expects "leverage"
        )

        # Format preview message (preview is RebalanceResult dataclass)
        preview_msg = "📊 **Rebalance Preview**\n\n"

        if not preview.planned_trades or all(t.action.value == "SKIP" for t in preview.planned_trades):
            preview_msg += "✅ Portfolio is already balanced!\n\n"
            await query.edit_message_text(preview_msg)
            return

        preview_msg += f"**Target**: Equal weight ({target_pct:.1f}% each)\n"
        preview_msg += f"**Leverage**: 3x\n\n"
        preview_msg += "**Required Trades**:\n"

        # Get actionable trades (skip SKIP actions)
        actionable_trades = [t for t in preview.planned_trades if t.action.value != "SKIP"]

        for trade in actionable_trades[:5]:  # Show first 5 trades
            action = trade.action.value
            coin = trade.coin

            if action == "CLOSE":
                preview_msg += f"🔴 Close {coin} (${abs(trade.current_usd_value):.2f})\n"
            elif action == "DECREASE":
                preview_msg += f"🟡 Reduce {coin} by ${abs(trade.trade_usd_value):.2f}\n"
            elif action == "INCREASE":
                preview_msg += f"🟢 Increase {coin} by ${abs(trade.trade_usd_value):.2f}\n"
            elif action == "OPEN":
                preview_msg += f"🆕 Open {coin} (${abs(trade.target_usd_value):.2f})\n"

        if len(actionable_trades) > 5:
            preview_msg += f"_...and {len(actionable_trades) - 5} more trades_\n"

        preview_msg += f"\n**Total Actionable Trades**: {len(actionable_trades)}\n"
        preview_msg += f"**Total Trades**: {len(preview.planned_trades)}\n\n"

        if preview.risk_warnings:
            preview_msg += "⚠️ **Warnings**:\n"
            for warning in preview.risk_warnings[:3]:
                preview_msg += f"• {warning}\n"
            preview_msg += "\n"

        preview_msg += f"_Environment: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}_"

        # Create confirmation keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Execute Rebalance", callback_data=f"rebalance_execute:{strategy}"),
                InlineKeyboardButton("❌ Cancel", callback_data="rebalance_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            preview_msg,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.exception("Failed to preview rebalance")
        await query.edit_message_text(
            f"❌ Failed to generate preview:\n`{str(e)}`",
            parse_mode="Markdown"
        )


async def rebalance_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rebalance execution callback."""
    query = update.callback_query
    await query.answer()

    # Extract strategy
    _, strategy = query.data.split(":")

    try:
        # Show processing
        await query.edit_message_text("⏳ Executing rebalance...\n\nThis may take a few moments.")

        # Get positions and build target allocations
        positions = position_service.list_positions()
        num_positions = len(positions)
        target_pct = 100.0 / num_positions if num_positions > 0 else 0

        target_allocations = {
            p["position"]["coin"]: target_pct
            for p in positions
        }

        # Execute rebalance
        result = rebalance_service.execute_rebalance(
            target_allocations=target_allocations,
            target_leverage=3
        )

        # Format result message
        summary = result["summary"]
        success_msg = "✅ **Rebalance Complete**\n\n"
        success_msg += f"**Total Trades**: {summary['total_trades']}\n"
        success_msg += f"**Successful**: {summary['successful_trades']}\n"
        success_msg += f"**Failed**: {summary['failed_trades']}\n\n"

        if summary["failed_trades"] > 0:
            success_msg += "⚠️ Some trades failed. Check your positions.\n\n"

        success_msg += f"**Final Portfolio Value**: ${summary['final_portfolio_value']:.2f}\n"
        success_msg += f"**Value Change**: {summary['value_change_pct']:.2f}%\n\n"
        success_msg += "_Use /positions to see updated portfolio_"

        await query.edit_message_text(success_msg, parse_mode="Markdown")

    except Exception as e:
        logger.exception("Failed to execute rebalance")
        await query.edit_message_text(
            f"❌ Rebalance failed:\n`{str(e)}`",
            parse_mode="Markdown"
        )


@authorized_only
async def scale_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler for /scale command or menu button.
    Places a scale order (multiple limit orders at different price levels).

    Usage: /scale <coin> <buy/sell> <total_size> <num_orders> <start_price> <end_price>

    Reference: docs/hyperliquid/api-reference.md - Scale Orders
    """
    # Handle callback query from menu button
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "📊 **Scale Order**\n\n"
            "**Usage**: `/scale <coin> <buy/sell> <usd_amount> <orders> <start_price> <end_price>`\n\n"
            "**Example**:\n"
            "`/scale BTC buy 100 5 108000 106000`\n"
            "_Places 5 buy orders totaling $100 from $108k down to $106k_\n\n"
            "**Parameters**:\n"
            "• `coin`: Asset symbol (BTC, ETH, etc.)\n"
            "• `buy/sell`: Order side\n"
            "• `usd_amount`: Total USD across all orders\n"
            "• `orders`: Number of orders (2-20)\n"
            "• `start_price`: First order price\n"
            "• `end_price`: Last order price\n\n"
            "Use the command format above to place a scale order.",
            parse_mode="Markdown"
        )
        return

    # Check arguments for command usage
    if not context.args or len(context.args) < 6:
        await update.message.reply_text(
            "📊 **Scale Order**\n\n"
            "**Usage**: `/scale <coin> <buy/sell> <usd_amount> <orders> <start_price> <end_price>`\n\n"
            "**Example**:\n"
            "`/scale BTC buy 100 5 108000 106000`\n"
            "_Places 5 buy orders totaling $100 from $108k down to $106k_\n\n"
            "**Parameters**:\n"
            "• `coin`: Asset symbol (BTC, ETH, etc.)\n"
            "• `buy/sell`: Order side\n"
            "• `usd_amount`: Total USD across all orders\n"
            "• `orders`: Number of orders (2-20)\n"
            "• `start_price`: First order price\n"
            "• `end_price`: Last order price\n\n"
            "Orders will be distributed evenly across the price range.",
            parse_mode="Markdown"
        )
        return

    try:
        coin = context.args[0].upper()
        side_str = context.args[1].lower()
        usd_amount_str = context.args[2]
        num_orders = int(context.args[3])
        start_price = float(context.args[4])
        end_price = float(context.args[5])

        # Validate side
        if side_str not in ["buy", "sell"]:
            await update.message.reply_text("❌ Invalid side. Use `buy` or `sell`.", parse_mode="Markdown")
            return

        is_buy = side_str == "buy"
        side_emoji = "🟢" if is_buy else "🔴"

        # Parse USD amount
        try:
            total_usd = parse_usd_amount(usd_amount_str)
        except ValueError as e:
            await update.message.reply_text(f"❌ {str(e)}")
            return

        if num_orders < 2 or num_orders > 20:
            await update.message.reply_text("❌ Number of orders must be between 2 and 20.")
            return

        if start_price <= 0 or end_price <= 0:
            await update.message.reply_text("❌ Prices must be greater than 0.")
            return

        # Show processing
        msg = await update.message.reply_text(
            f"⏳ Fetching {coin} price and generating scale order..."
        )

        # Convert USD to coin size (use average of start/end price for estimate)
        avg_price = (start_price + end_price) / 2
        total_size = total_usd / avg_price

        # Preview scale order
        from src.models.scale_order import ScaleOrderConfig

        config = ScaleOrderConfig(
            coin=coin,
            is_buy=is_buy,
            total_size=total_size,
            num_orders=num_orders,
            start_price=start_price,
            end_price=end_price,
            distribution_type="linear"
        )

        preview = scale_order_service.preview_scale_order(config)

        # Format preview
        preview_msg = f"{side_emoji} **Scale Order Preview**\n\n"
        preview_msg += f"**Coin**: {coin}\n"
        preview_msg += f"**Side**: {side_str.upper()}\n"
        preview_msg += f"**Total USD**: {format_usd_amount(total_usd)}\n"
        preview_msg += f"**Total Coins**: {format_coin_amount(total_size, coin)}\n"
        preview_msg += f"**Orders**: {num_orders}\n"
        preview_msg += f"**Price Range**: ${start_price:,.2f} → ${end_price:,.2f}\n"
        preview_msg += f"**Avg Price**: ${avg_price:,.2f}\n\n"

        preview_msg += "**Order Breakdown**:\n"
        for i, order in enumerate(preview["orders"][:5], 1):
            preview_msg += f"{i}. ${order['price']:.2f} × {order['size']:.4f} = ${order['value']:.2f}\n"

        if len(preview["orders"]) > 5:
            preview_msg += f"_...and {len(preview['orders']) - 5} more orders_\n"

        preview_msg += f"\n_Environment: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}_"

        # Create confirmation keyboard
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Place Orders",
                    callback_data=f"scale_execute:{coin}:{side_str}:{total_size}:{num_orders}:{start_price}:{end_price}"
                ),
                InlineKeyboardButton("❌ Cancel", callback_data="scale_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await msg.edit_text(
            preview_msg,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    except ValueError as e:
        await update.message.reply_text(f"❌ Invalid parameter: {str(e)}")
    except Exception as e:
        logger.exception("Failed to preview scale order")
        await update.message.reply_text(
            f"❌ Error: `{str(e)}`",
            parse_mode="Markdown"
        )


async def scale_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle scale order execution callback."""
    query = update.callback_query
    await query.answer()

    if query.data == "scale_cancel":
        await query.edit_message_text("❌ Scale order cancelled.")
        return

    # Extract parameters
    parts = query.data.split(":")
    _, coin, side_str, total_size, num_orders, start_price, end_price = parts

    is_buy = side_str == "buy"
    total_size = float(total_size)
    num_orders = int(num_orders)
    start_price = float(start_price)
    end_price = float(end_price)

    try:
        # Show processing
        await query.edit_message_text(
            f"⏳ Placing {num_orders} {side_str.upper()} orders for {coin}...\n\n"
            f"This may take a few moments."
        )

        # Place scale order
        from src.models.scale_order import ScaleOrderConfig

        config = ScaleOrderConfig(
            coin=coin,
            is_buy=is_buy,
            total_size=total_size,
            num_orders=num_orders,
            start_price=start_price,
            end_price=end_price,
            distribution_type="linear"
        )

        result = scale_order_service.place_scale_order(config)

        # Format result
        side_emoji = "🟢" if is_buy else "🔴"
        success_msg = f"{side_emoji} **Scale Order Placed**\n\n"
        success_msg += f"**Coin**: {coin}\n"
        success_msg += f"**Side**: {side_str.upper()}\n"
        success_msg += f"**Total Orders**: {result['total_orders']}\n"
        success_msg += f"**Successful**: {result['successful_orders']}\n"
        success_msg += f"**Failed**: {result['failed_orders']}\n\n"

        if result["failed_orders"] > 0:
            success_msg += "⚠️ Some orders failed to place.\n\n"

        success_msg += f"**Scale Order ID**: `{result['scale_order_id']}`\n\n"
        success_msg += "_Orders are now live on the exchange_"

        await query.edit_message_text(success_msg, parse_mode="Markdown")

    except Exception as e:
        logger.exception(f"Failed to place scale order for {coin}")
        await query.edit_message_text(
            f"❌ Failed to place scale order:\n`{str(e)}`",
            parse_mode="Markdown"
        )


# Export callback handlers
def get_callback_handlers():
    """Return list of callback query handlers for advanced commands."""
    return [
        CallbackQueryHandler(rebalance_preview_callback, pattern="^rebalance_preview:"),
        CallbackQueryHandler(rebalance_execute_callback, pattern="^rebalance_execute:"),
        CallbackQueryHandler(rebalance_preview_callback, pattern="^rebalance_(custom|cancel)$"),
        CallbackQueryHandler(scale_execute_callback, pattern="^scale_"),
    ]
