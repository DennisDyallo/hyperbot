"""
Loading state management for async operations in Telegram bot.

Provides consistent loading indicators and message management to improve
perceived performance and user feedback.
"""

from typing import Final, cast

from telegram import Message, Update

# Standard loading messages with emoji
LOADING_EMOJI: Final[str] = "⏳"

LOADING_MESSAGES: Final[dict[str, str]] = {
    "preview": f"{LOADING_EMOJI} Calculating preview...",
    "price": f"{LOADING_EMOJI} Fetching current {{coin}} price...",
    "order": f"{LOADING_EMOJI} Placing order...",
    "leverage": f"{LOADING_EMOJI} Setting leverage to {{leverage}}x...",
    "position": f"{LOADING_EMOJI} Fetching {{coin}} position...",
    "positions": f"{LOADING_EMOJI} Loading positions...",
    "account": f"{LOADING_EMOJI} Loading account data...",
    "close": f"{LOADING_EMOJI} Closing {{coin}} position...",
    "cancel": f"{LOADING_EMOJI} Canceling order...",
    "market_data": f"{LOADING_EMOJI} Fetching market data...",
}


class LoadingMessage:
    """
    Manages loading state messages in Telegram bot.

    Ensures consistent loading indicators and proper message cleanup.
    Supports both new messages and editing existing messages.

    Example:
        >>> loading = LoadingMessage()
        >>> msg = await loading.show(update, "order")
        >>> # ... perform async operation ...
        >>> await loading.hide(msg, "✅ Order placed!")
    """

    @staticmethod
    async def show(
        update: Update,
        action: str,
        **kwargs: str,
    ) -> Message:
        """
        Display a loading message.

        Args:
            update: The Telegram update object.
            action: The action key from LOADING_MESSAGES.
            **kwargs: Format parameters for the message (e.g., coin="BTC").

        Returns:
            The sent or edited message.

        Raises:
            ValueError: If action is not in LOADING_MESSAGES.

        Example:
            >>> msg = await LoadingMessage.show(update, "price", coin="BTC")
            >>> # Shows: "⏳ Fetching current BTC price..."
        """
        if action not in LOADING_MESSAGES:
            raise ValueError(
                f"Unknown loading action: {action}. Available: {', '.join(LOADING_MESSAGES.keys())}"
            )

        message_template = LOADING_MESSAGES[action]
        message_text = message_template.format(**kwargs)

        # Determine if we should send new message or edit existing
        if update.callback_query:
            # Edit the message from callback query
            result = await update.callback_query.edit_message_text(message_text)
            # edit_message_text can return bool on success
            if isinstance(result, bool):
                # Fallback to the callback query message if bool returned
                if update.callback_query.message:
                    return cast(Message, update.callback_query.message)
                raise ValueError("Callback query has no message")
            return result

        if update.message:
            # Send new message
            return await update.message.reply_text(message_text)

        raise ValueError("Update must have either callback_query or message")

    @staticmethod
    async def hide(message: Message, replacement_text: str) -> Message:
        """
        Hide loading message by replacing with final content.

        Args:
            message: The loading message to replace.
            replacement_text: The final message content.

        Returns:
            The edited message.

        Example:
            >>> await LoadingMessage.hide(msg, "✅ Order placed successfully!")
        """
        result = await message.edit_text(replacement_text)
        # edit_text can return bool on success
        if isinstance(result, bool):
            return message
        return result

    @staticmethod
    def get_message(action: str, **kwargs: str) -> str:
        """
        Get formatted loading message without displaying it.

        Useful for custom message handling or testing.

        Args:
            action: The action key from LOADING_MESSAGES.
            **kwargs: Format parameters for the message.

        Returns:
            Formatted loading message string.

        Raises:
            ValueError: If action is not in LOADING_MESSAGES.

        Example:
            >>> text = LoadingMessage.get_message("price", coin="ETH")
            >>> # Returns: "⏳ Fetching current ETH price..."
        """
        if action not in LOADING_MESSAGES:
            raise ValueError(
                f"Unknown loading action: {action}. Available: {', '.join(LOADING_MESSAGES.keys())}"
            )

        message_template = LOADING_MESSAGES[action]
        return message_template.format(**kwargs)
