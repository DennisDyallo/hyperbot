"""
Middleware and decorators for Telegram bot.
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from src.config import logger, settings


def authorized_only(func):
    """
    Decorator to restrict command access to authorized users only.

    Usage:
        @authorized_only
        async def my_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Only authorized users can execute this
            pass

    Reference: docs/telegram/best-practices.md - Security Best Practices
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        user_id = user.id if user else None

        if not user_id:
            logger.warning("Received update without user information")
            return

        if user_id not in settings.TELEGRAM_AUTHORIZED_USERS:
            logger.warning(
                f"Unauthorized access attempt by user {user_id} "
                f"(@{user.username if user.username else 'no_username'})"
            )
            if update.message:
                await update.message.reply_text(
                    "🚫 Unauthorized. This bot is private.\n\n"
                    f"Your user ID: `{user_id}`\n"
                    "Contact the bot owner to request access.",
                    parse_mode="Markdown"
                )
            return

        # Log authorized access
        logger.info(
            f"Authorized command from user {user_id} "
            f"(@{user.username if user.username else 'no_username'}): "
            f"{update.message.text if update.message else 'callback'}"
        )

        return await func(update, context, *args, **kwargs)

    return wrapper


def admin_only(func):
    """
    Decorator to restrict command access to admin users only.
    Currently, all authorized users are admins.

    This can be extended in the future to have a separate admin list.
    """
    # For now, admin_only is the same as authorized_only
    return authorized_only(func)
