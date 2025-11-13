"""
Notification management commands for order fill notifications.

Commands:
- /notify_status - Show notification service status
- /notify_test - Send test notification
- /notify_history - Show recent notification history
"""

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.middleware import authorized_only
from src.config import logger
from src.services.order_monitor_service import order_monitor_service


@authorized_only
async def notify_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show order fill notification service status.

    Usage: /notify_status
    """
    if not update.message:
        return

    try:
        # Get service status
        status = order_monitor_service.get_status()

        # Format status message
        status_lines = [
            "📊 **Order Fill Notification Status**",
            "",
            f"**Service**: {'🟢 Running' if status['running'] else '🔴 Stopped'}",
            "",
            "**WebSocket:**",
            f"  • Healthy: {'✅ Yes' if status['websocket_healthy'] else '⚠️ No'}",
            f"  • Last Heartbeat: {status['last_heartbeat'] or 'Never'}",
            f"  • Reconnects: {status['websocket_reconnects']}",
            f"  • Reconnect Attempts: {status['reconnect_attempts']}",
            "",
            "**State:**",
            f"  • Last Processed: {status['last_processed_timestamp']}",
            f"  • Age: {status['state_age_seconds']:.1f}s",
            "",
            "**Recovery:**",
        ]

        # Add recovery info if available
        state = order_monitor_service.state_manager.state
        if state.last_recovery_run:
            status_lines.append(f"  • Last Run: {state.last_recovery_run}")
            status_lines.append(f"  • Fills Found: {state.recovery_fills_found}")
        else:
            status_lines.append("  • No recovery run yet")

        status_lines.extend([
            "",
            f"**Cache**: {len(state.recent_fill_hashes)} recent fill hashes",
        ])

        status_text = "\n".join(status_lines)

        await update.message.reply_text(status_text, parse_mode="Markdown")

    except Exception as e:
        logger.exception("Error in notify_status command")
        await update.message.reply_text(f"❌ Error getting status: {str(e)}")


@authorized_only
async def notify_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Send a test notification.

    Usage: /notify_test
    """
    if not update.message:
        return

    try:
        # Create test notification
        test_message = (
            "🧪 **Test Notification**\n\n"
            "This is a test of the order fill notification system.\n\n"
            "If you receive this message, notifications are working correctly.\n\n"
            f"**Chat ID**: {update.message.chat_id}\n"
            f"**Service Running**: {'✅ Yes' if order_monitor_service._running else '⚠️ No'}"
        )

        # Send test notification to user
        await update.message.reply_text(test_message, parse_mode="Markdown")

        logger.info(f"Test notification sent to {update.message.chat_id}")

    except Exception as e:
        logger.exception("Error in notify_test command")
        await update.message.reply_text(f"❌ Error sending test: {str(e)}")


@authorized_only
async def notify_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show recent notification history.

    Usage: /notify_history [count]

    Args:
        count: Number of recent fills to show (default: 10, max: 50)
    """
    if not update.message:
        return

    try:
        # Parse count argument
        count = 10
        if context.args and len(context.args) > 0:
            try:
                count = int(context.args[0])
                count = max(1, min(count, 50))  # Clamp between 1 and 50
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid count. Usage: /notify_history [count]\n"
                    "Example: /notify_history 20"
                )
                return

        # Get recent fill hashes
        state = order_monitor_service.state_manager.state
        recent_hashes = list(state.recent_fill_hashes)

        if not recent_hashes:
            await update.message.reply_text(
                "ℹ️ No recent fills in cache.\n\n"
                "Fills will appear here after orders are executed."
            )
            return

        # Format history message
        history_lines = [
            f"📜 **Recent Fill History (Last {min(count, len(recent_hashes))})**",
            "",
            f"Total fills in cache: {len(recent_hashes)}",
            "Cache limit: 1000 fills",
            "",
            "**Fill Hashes:**",
        ]

        # Show most recent fills
        for i, fill_hash in enumerate(recent_hashes[:count], 1):
            history_lines.append(f"{i}. `{fill_hash}`")

        if len(recent_hashes) > count:
            history_lines.append("")
            history_lines.append(f"_...and {len(recent_hashes) - count} more_")

        history_lines.extend([
            "",
            "**Recovery Info:**",
            f"Last recovery: {state.last_recovery_run or 'Never'}",
            f"Fills recovered: {state.recovery_fills_found}",
        ])

        history_text = "\n".join(history_lines)

        await update.message.reply_text(history_text, parse_mode="Markdown")

    except Exception as e:
        logger.exception("Error in notify_history command")
        await update.message.reply_text(f"❌ Error getting history: {str(e)}")
