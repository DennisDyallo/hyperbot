"""
Main Telegram bot application.
"""
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from src.config import logger, settings
from src.services.hyperliquid_service import hyperliquid_service
from src.bot.handlers import basic, trading, advanced, wizards


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
            await update.effective_message.reply_text(
                error_message,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands."""
    await update.message.reply_text(
        "❓ Unknown command. Use /help to see available commands."
    )


def create_application() -> Application:
    """
    Create and configure the Telegram bot application.

    Returns:
        Configured Application instance

    Raises:
        ValueError: If bot token is not configured
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN not configured. "
            "Please set it in your .env file."
        )

    if not settings.TELEGRAM_AUTHORIZED_USERS:
        logger.warning(
            "No authorized users configured. "
            "Set TELEGRAM_AUTHORIZED_USERS in .env to allow access."
        )

    logger.info("Creating Telegram bot application...")

    # Create application
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register ConversationHandlers first (they have priority over simple callbacks)
    application.add_handler(wizards.get_market_wizard_handler())

    # Register command handlers
    # Basic commands
    application.add_handler(CommandHandler("start", basic.start))
    application.add_handler(CommandHandler("help", basic.help_command))
    application.add_handler(CommandHandler("account", basic.account_command))
    application.add_handler(CommandHandler("positions", basic.positions_command))
    application.add_handler(CommandHandler("status", basic.status_command))

    # Trading commands (legacy - kept for backward compatibility)
    application.add_handler(CommandHandler("close", trading.close_command))
    application.add_handler(CommandHandler("market", trading.market_command))

    # Advanced commands (legacy - kept for backward compatibility)
    application.add_handler(CommandHandler("rebalance", advanced.rebalance_command))
    application.add_handler(CommandHandler("scale", advanced.scale_command))

    # Register menu navigation callback handlers
    for handler in basic.get_menu_callback_handlers():
        application.add_handler(handler)

    # Register close position handlers
    for handler in wizards.get_close_position_handlers():
        application.add_handler(handler)

    # Register trading callback query handlers (legacy)
    for handler in trading.get_callback_handlers():
        application.add_handler(handler)
    for handler in advanced.get_callback_handlers():
        application.add_handler(handler)

    # Unknown command handler (must be last)
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Register error handler
    application.add_error_handler(error_handler)

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

    logger.info("Bot services initialized")


async def post_shutdown(application: Application):
    """
    Post-shutdown hook.
    Called after the bot stops.
    """
    logger.info("Shutting down bot...")


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
