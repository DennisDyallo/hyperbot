"""
Rebalancing wizard for portfolio rebalancing.

Flow:
1. /rebalance command → Shows current portfolio allocation
2. User selects strategy (equal weight, custom, cancel)
3. Preview → Shows planned trades with risk warnings
4. Execute → Places trades and reports results

This is a multi-step wizard extracted from commands.py for better separation of concerns.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from src.bot.middleware import authorized_only
from src.config import logger, settings
from src.services.position_service import position_service
from src.services.rebalance_service import rebalance_service


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
            msg = await update.message.reply_text("⏳ Analyzing portfolio...")  # type: ignore

        # Get current positions
        positions = position_service.list_positions()

        if not positions:
            await msg.edit_text("📭 No open positions to rebalance.")  # type: ignore
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

        await msg.edit_text(allocation_text, parse_mode="Markdown", reply_markup=reply_markup)  # type: ignore

    except Exception as e:
        logger.exception("Failed to analyze portfolio for rebalancing")
        error_msg = f"❌ Error: `{str(e)}`"
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(error_msg, parse_mode="Markdown")  # type: ignore


async def rebalance_preview_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rebalance preview callback."""
    query = update.callback_query
    assert query is not None
    assert query.data is not None

    query = update.callback_query
    await query.answer()  # type: ignore

    if query.data == "rebalance_cancel":  # type: ignore
        await query.edit_message_text("❌ Rebalancing cancelled.")  # type: ignore
        return

    if query.data == "rebalance_custom":  # type: ignore
        await query.edit_message_text(  # type: ignore
            "📝 **Custom Rebalancing**\n\n"
            "Custom weight rebalancing is not yet implemented.\n"
            "Use `/rebalance` and select equal weight, or use the web dashboard for advanced options."
        )
        return

    # Extract strategy
    _, strategy = query.data.split(":")  # type: ignore

    try:
        # Show processing
        await query.edit_message_text("⏳ Generating rebalance plan...")  # type: ignore

        # Get positions
        positions = position_service.list_positions()

        # Build target allocations (equal weight)
        num_positions = len(positions)
        target_pct = 100.0 / num_positions if num_positions > 0 else 0

        target_allocations = {p["position"]["coin"]: target_pct for p in positions}

        # Preview rebalance (fix parameter names to match service)
        preview = rebalance_service.preview_rebalance(
            target_weights=target_allocations,  # Service expects "target_weights"
            leverage=3,  # Service expects "leverage"
        )

        # Format preview message (preview is RebalanceResult dataclass)
        preview_msg = "📊 **Rebalance Preview**\n\n"

        if not preview.planned_trades or all(
            t.action.value == "SKIP" for t in preview.planned_trades
        ):
            preview_msg += "✅ Portfolio is already balanced!\n\n"
            await query.edit_message_text(preview_msg)  # type: ignore
            return

        preview_msg += f"**Target**: Equal weight ({target_pct:.1f}% each)\n"
        preview_msg += "**Leverage**: 3x\n\n"
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

        preview_msg += (
            f"_Environment: {'🧪 Testnet' if settings.HYPERLIQUID_TESTNET else '🚀 Mainnet'}_"
        )

        # Create confirmation keyboard
        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ Execute Rebalance",
                    callback_data=f"rebalance_execute:{strategy}",
                ),
                InlineKeyboardButton("❌ Cancel", callback_data="rebalance_cancel"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(preview_msg, parse_mode="Markdown", reply_markup=reply_markup)  # type: ignore

    except Exception as e:
        logger.exception("Failed to preview rebalance")
        await query.edit_message_text(  # type: ignore
            f"❌ Failed to generate preview:\n`{str(e)}`", parse_mode="Markdown"
        )


async def rebalance_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rebalance execution callback."""
    query = update.callback_query
    assert query is not None
    assert query.data is not None

    query = update.callback_query
    await query.answer()  # type: ignore

    # Extract strategy
    _, strategy = query.data.split(":")  # type: ignore

    try:
        # Show processing
        await query.edit_message_text("⏳ Executing rebalance...\n\nThis may take a few moments.")  # type: ignore

        # Get positions and build target allocations
        positions = position_service.list_positions()
        num_positions = len(positions)
        target_pct = 100.0 / num_positions if num_positions > 0 else 0

        target_allocations = {p["position"]["coin"]: target_pct for p in positions}

        # Execute rebalance
        result = rebalance_service.execute_rebalance(
            target_weights=target_allocations,
            leverage=3,
            dry_run=False,  # Execute for real
        )

        # Format result message
        if result.success:
            total_trades = result.executed_trades
            success_msg = "✅ **Rebalance Complete**\n\n"
            success_msg += f"**Total Trades**: {total_trades}\n"
            success_msg += f"**Successful**: {result.successful_trades}\n"
            success_msg += f"**Failed**: {result.failed_trades}\n"
            success_msg += f"**Skipped**: {result.skipped_trades}\n\n"

            if result.failed_trades > 0:
                success_msg += "⚠️ Some trades failed. Check your positions.\n\n"
                if result.errors:
                    success_msg += "**Errors**:\n"
                    for error in result.errors[:3]:  # Show first 3 errors
                        success_msg += f"• {error}\n"
                    success_msg += "\n"

            success_msg += "_Use /positions to see updated portfolio_"
            await query.edit_message_text(success_msg, parse_mode="Markdown")  # type: ignore
        else:
            error_msg = f"❌ **Rebalance Failed**\n\n{result.message}"
            if result.errors:
                error_msg += "\n\n**Errors**:\n"
                for error in result.errors[:3]:
                    error_msg += f"• {error}\n"
            await query.edit_message_text(error_msg, parse_mode="Markdown")  # type: ignore

    except Exception as e:
        logger.exception("Failed to execute rebalance")
        await query.edit_message_text(f"❌ Rebalance failed:\n`{str(e)}`", parse_mode="Markdown")  # type: ignore


def get_rebalance_handlers() -> list[CallbackQueryHandler | CommandHandler]:
    """Return all rebalance-related handlers."""
    return [
        CommandHandler("rebalance", rebalance_command),
        CallbackQueryHandler(rebalance_preview_callback, pattern="^rebalance_preview:"),
        CallbackQueryHandler(rebalance_execute_callback, pattern="^rebalance_execute:"),
        CallbackQueryHandler(rebalance_preview_callback, pattern="^rebalance_(custom|cancel)$"),
    ]
