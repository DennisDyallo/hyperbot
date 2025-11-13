"""
Main Telegram bot application.
"""

from warnings import filterwarnings

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

# Suppress PTBUserWarning about CallbackQueryHandler with per_message=False
# This is expected behavior for ConversationHandlers with mixed handler types
# (MessageHandler + CallbackQueryHandler). See:
# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Frequently-Asked-Questions#what-do-the-per_-settings-in-conversationhandler-do
# IMPORTANT: Must be set BEFORE importing handlers (warnings triggered at import time)
filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

from src.bot.handlers import (  # noqa: E402
    commands,
    menus,
    notify,
    wizard_close_position,
    wizard_market_order,
    wizard_scale_order,
)
from src.config import logger, settings  # noqa: E402
from src.services.hyperliquid_service import hyperliquid_service  # noqa: E402
from src.services.order_monitor_service import order_monitor_service  # noqa: E402


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle errors in the bot.

    Reference: docs/telegram/best-practices.md - Error Handling
    """
    logger.error(f"Exception while handling an update: {context.error}")

    # Send error message to user if update is available
    if update and update.effective_message:
        error_message = (
            "❌ An error occurred while processing your request.\n\n"
            f"Error: `{str(context.error)[:100]}`"
        )
        try:
            await update.effective_message.reply_text(error_message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands."""
    if update.message:
        await update.message.reply_text("❓ Unknown command. Use /help to see available commands.")


def create_application() -> Application:
    """
    Create and configure the Telegram bot application.

    Returns:
        Configured Application instance

    Raises:
        ValueError: If bot token is not configured
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured. Please set it in your .env file.")

    if not settings.TELEGRAM_AUTHORIZED_USERS:
        logger.warning(
            "No authorized users configured. Set TELEGRAM_AUTHORIZED_USERS in .env to allow access."
        )

    logger.info("Creating Telegram bot application...")

    # Create application
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register ConversationHandlers first (they have priority over simple callbacks)
    logger.info("Registering ConversationHandlers...")
    application.add_handler(wizard_market_order.get_market_wizard_handler())
    logger.info("✅ Market wizard registered")
    application.add_handler(wizard_scale_order.scale_order_conversation)
    logger.info("✅ Scale order wizard registered")

    # Register command handlers
    application.add_handler(CommandHandler("start", commands.start))
    application.add_handler(CommandHandler("help", commands.help_command))
    application.add_handler(CommandHandler("account", commands.account_command))
    application.add_handler(CommandHandler("positions", commands.positions_command))
    application.add_handler(CommandHandler("status", commands.status_command))
    application.add_handler(CommandHandler("rebalance", commands.rebalance_command))

    # Register notification commands
    application.add_handler(CommandHandler("notify_status", notify.notify_status))
    application.add_handler(CommandHandler("notify_test", notify.notify_test))
    application.add_handler(CommandHandler("notify_history", notify.notify_history))

    # Register menu navigation callback handlers
    for handler in menus.get_menu_handlers():
        application.add_handler(handler)

    # Register rebalancing callback handlers
    from telegram.ext import CallbackQueryHandler

    application.add_handler(
        CallbackQueryHandler(commands.rebalance_preview_callback, pattern="^rebalance_preview:")
    )
    application.add_handler(
        CallbackQueryHandler(commands.rebalance_execute_callback, pattern="^rebalance_execute:")
    )
    application.add_handler(
        CallbackQueryHandler(
            commands.rebalance_preview_callback, pattern="^rebalance_(custom|cancel)$"
        )
    )

    # Register close position handlers
    for handler in wizard_close_position.get_close_position_handlers():
        application.add_handler(handler)

    # Unknown command handler (must be last)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Register error handler
    application.add_error_handler(error_handler)  # type: ignore[arg-type]

    logger.info("Bot application created successfully")
    return application


async def post_init(application: Application):
    """
    Post-initialization hook.
    Called after the bot is initialized but before it starts polling.
    """
    logger.info("Initializing bot services...")

    # Initialize Hyperliquid service if not already initialized
    if not hyperliquid_service._initialized:
        try:
            hyperliquid_service.initialize()
            logger.info("Hyperliquid service initialized for bot")
        except Exception as e:
            logger.error(f"Failed to initialize Hyperliquid service: {e}")
            logger.warning("Bot will start but Hyperliquid features may not work")

    # Start OrderMonitorService for fill notifications
    try:
        # Store bot instance in order_monitor_service for sending messages
        order_monitor_service.bot = application.bot

        await order_monitor_service.start()
        logger.info("✅ Order fill monitoring started")
    except Exception as e:
        logger.error(f"Failed to start order monitor service: {e}")
        logger.warning("Bot will start but fill notifications may not work")

    # Schedule account health auto-refresh job
    try:

        async def refresh_account_messages(context):
            """Auto-refresh active account health messages every 30s."""
            from src.bot.formatters.account import format_account_health_message
            from src.use_cases.portfolio.risk_analysis import (
                RiskAnalysisRequest,
                RiskAnalysisUseCase,
            )

            # Iterate over all users with active account messages
            for user_data in context.application.user_data.values():
                if "account_message_id" not in user_data:
                    continue

                try:
                    # Fetch fresh risk data
                    use_case = RiskAnalysisUseCase()
                    risk_data = await use_case.execute(
                        RiskAnalysisRequest(coins=None, include_cross_margin_ratio=True)
                    )

                    # Format message
                    message = format_account_health_message(risk_data)

                    # Update message
                    await context.bot.edit_message_text(
                        chat_id=user_data["account_chat_id"],
                        message_id=user_data["account_message_id"],
                        text=message,
                        parse_mode="HTML",
                    )

                except Exception as e:
                    # Message may have been deleted or edited manually
                    logger.debug(f"Auto-refresh skipped (message unavailable): {e}")
                    # Remove stale message_id
                    user_data.pop("account_message_id", None)
                    user_data.pop("account_chat_id", None)

        # Run every 30 seconds
        application.job_queue.run_repeating(
            callback=refresh_account_messages,
            interval=30,
            first=30,  # Wait 30s before first run
            name="account_health_refresh",
        )

        logger.info("✅ Account health auto-refresh enabled (30s interval)")
    except Exception as e:
        logger.error(f"Failed to schedule account refresh job: {e}")
        logger.warning("Bot will start but account auto-refresh may not work")

    logger.info("Bot services initialized")


async def post_shutdown(application: Application):
    """
    Post-shutdown hook.
    Called after the bot stops.
    """
    logger.info("Shutting down bot...")

    # Stop OrderMonitorService
    try:
        await order_monitor_service.stop()
        logger.info("✅ Order fill monitoring stopped")
    except Exception as e:
        logger.error(f"Error stopping order monitor service: {e}")

    logger.info("Bot shutdown complete")


def main():
    """
    Main entry point for the Telegram bot.

    Usage:
        python -m src.bot.main
    or:
        uv run python -m src.bot.main
    """
    logger.info(f"Starting {settings.PROJECT_NAME} Telegram Bot...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Testnet: {settings.HYPERLIQUID_TESTNET}")
    logger.info(f"Authorized users: {len(settings.TELEGRAM_AUTHORIZED_USERS)}")

    try:
        # Create application
        application = create_application()

        # Set up hooks
        application.post_init = post_init
        application.post_shutdown = post_shutdown

        # Start polling
        logger.info("Starting bot polling...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # Ignore old updates on startup
        )

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error in bot: {e}")
        raise


if __name__ == "__main__":
    main()
