"""
Wizard state extraction decorator.

Provides a decorator that extracts and validates common wizard state
(query, user_data) from update and context objects, reducing boilerplate.
"""

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes

from src.config import logger

# Type variables for generic decorator typing
P = ParamSpec("P")
RT = TypeVar("RT")


def extract_callback_state(
    func: Callable[
        [Update, ContextTypes.DEFAULT_TYPE, CallbackQuery, dict[str, Any]], Awaitable[RT]
    ],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[RT]]:
    """
    Decorator that extracts and validates callback query state.

    Extracts:
    - query: CallbackQuery object (asserts not None)
    - user_data: User data dictionary (asserts not None)

    Automatically answers the callback query.

    Usage:
        @extract_callback_state
        async def handler(update, context, query, user_data):
            # query and user_data are already extracted and validated
            coin = query.data.split(":")[1]
            user_data["coin"] = coin
            ...

    Args:
        func: Handler function expecting (update, context, query, user_data)

    Returns:
        Wrapped handler that accepts (update, context) and extracts state
    """

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> RT:
        """Wrapper that extracts and validates state before calling handler."""
        # Extract query
        query = update.callback_query
        if query is None:
            logger.error(f"No callback query in {func.__name__}")
            raise ValueError("Expected callback query but got None")

        # Extract user_data
        user_data = context.user_data
        if user_data is None:
            logger.error(f"No user data in {func.__name__}")
            raise ValueError("Expected user_data but got None")

        # Answer the callback query
        await query.answer()

        # Call the original handler with extracted state
        result = await func(update, context, query, user_data)
        return result

    return wrapper


def extract_message_state(
    func: Callable[[Update, ContextTypes.DEFAULT_TYPE, dict[str, Any]], Awaitable[RT]],
) -> Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[RT]]:
    """
    Decorator that extracts and validates message state.

    Extracts:
    - user_data: User data dictionary (asserts not None)

    Usage:
        @extract_message_state
        async def handler(update, context, user_data):
            # user_data is already extracted and validated
            message_text = update.message.text
            user_data["amount"] = parse_amount(message_text)
            ...

    Args:
        func: Handler function expecting (update, context, user_data)

    Returns:
        Wrapped handler that accepts (update, context) and extracts state
    """

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> RT:
        """Wrapper that extracts and validates state before calling handler."""
        # Extract user_data
        user_data = context.user_data
        if user_data is None:
            logger.error(f"No user data in {func.__name__}")
            raise ValueError("Expected user_data but got None")

        # Call the original handler with extracted state
        result = await func(update, context, user_data)
        return result

    return wrapper
