"""
Telegram mock factories.

Provides factories and builders for creating realistic Telegram Update and Context mocks
used in bot handler tests. Reduces boilerplate and enforces consistent mock structure.
"""

from typing import Any
from unittest.mock import AsyncMock, Mock


class UpdateBuilder:
    """
    Fluent builder for creating Telegram Update mocks.

    Handles both message-based updates (commands, text) and callback queries (inline buttons).

    Example:
        >>> update = UpdateBuilder()                \\
        ...     .with_message()                     \\
        ...     .with_user(id=1383283890)           \\
        ...     .with_text("/start")                \\
        ...     .build()
        >>> update.message.text
        '/start'

        >>> update = UpdateBuilder()                \\
        ...     .with_callback_query("menu_main")   \\
        ...     .with_user(id=1383283890)           \\
        ...     .build()
        >>> update.callback_query.data
        'menu_main'
    """

    def __init__(self):
        self._update = Mock()
        self._has_message = False
        self._has_callback = False
        self._user_id = 1383283890  # Default authorized user
        self._username = "testuser"
        self._text = None
        self._callback_data = None

    def with_message(self) -> "UpdateBuilder":
        """Add a message to the update."""
        self._has_message = True
        self._has_callback = False
        return self

    def with_callback_query(self, data: str) -> "UpdateBuilder":
        """Add a callback query to the update."""
        self._has_callback = True
        self._has_message = False
        self._callback_data = data
        return self

    def with_user(self, id: int, username: str | None = None) -> "UpdateBuilder":
        """Set the user ID and optional username."""
        self._user_id = id
        if username:
            self._username = username
        return self

    def with_text(self, text: str) -> "UpdateBuilder":
        """Set message text (requires with_message)."""
        self._text = text
        return self

    def build(self) -> Mock:
        """Build and return the Update mock."""
        # Set up user
        self._update.effective_user = Mock()
        self._update.effective_user.id = self._user_id
        self._update.effective_user.username = self._username

        if self._has_message:
            # Set up message
            self._update.message = Mock()
            self._update.message.reply_text = AsyncMock()
            self._update.message.text = self._text
            self._update.callback_query = None

        elif self._has_callback:
            # Set up callback query
            self._update.callback_query = Mock()
            self._update.callback_query.data = self._callback_data
            self._update.callback_query.answer = AsyncMock()
            self._update.callback_query.edit_message_text = AsyncMock()
            self._update.message = None

        else:
            # No message or callback
            self._update.message = None
            self._update.callback_query = None

        return self._update


class ContextBuilder:
    """
    Fluent builder for creating Telegram Context mocks.

    Example:
        >>> context = ContextBuilder()              \\
        ...     .with_user_data({"coin": "BTC"})    \\
        ...     .build()
        >>> context.user_data["coin"]
        'BTC'
    """

    def __init__(self):
        self._user_data = {}
        self._args = []

    def with_user_data(self, data: dict[str, Any]) -> "ContextBuilder":
        """Set user_data dictionary."""
        self._user_data = data
        return self

    def with_args(self, args: list) -> "ContextBuilder":
        """Set command args list."""
        self._args = args
        return self

    def build(self) -> Mock:
        """Build and return the Context mock."""
        context = Mock()
        context.user_data = self._user_data.copy()
        context.args = self._args.copy()
        context.bot = Mock()
        context.bot.send_message = AsyncMock()
        return context


class TelegramMockFactory:
    """
    Static factory methods for creating common Telegram mock configurations.

    Provides convenience methods for the most common test scenarios.
    """

    @staticmethod
    def create_command_update(
        command: str = "/start", user_id: int = 1383283890, username: str = "testuser"
    ) -> Mock:
        """
        Create Update mock for a command (e.g., /start, /help).

        Args:
            command: Command string including slash
            user_id: Telegram user ID
            username: Telegram username

        Returns:
            Mock Update with message containing command
        """
        return (
            UpdateBuilder().with_message().with_user(user_id, username).with_text(command).build()
        )

    @staticmethod
    def create_text_update(
        text: str, user_id: int = 1383283890, username: str = "testuser"
    ) -> Mock:
        """
        Create Update mock for a text message.

        Args:
            text: Message text
            user_id: Telegram user ID
            username: Telegram username

        Returns:
            Mock Update with message containing text
        """
        return UpdateBuilder().with_message().with_user(user_id, username).with_text(text).build()

    @staticmethod
    def create_callback_update(
        callback_data: str, user_id: int = 1383283890, username: str = "testuser"
    ) -> Mock:
        """
        Create Update mock for a callback query (inline button press).

        Args:
            callback_data: Callback data string
            user_id: Telegram user ID
            username: Telegram username

        Returns:
            Mock Update with callback_query
        """
        return (
            UpdateBuilder().with_callback_query(callback_data).with_user(user_id, username).build()
        )

    @staticmethod
    def create_authorized_update(command: str = "/start") -> Mock:
        """
        Create Update mock for authorized user (default user ID 1383283890).

        Args:
            command: Command string

        Returns:
            Mock Update from authorized user
        """
        return TelegramMockFactory.create_command_update(
            command=command, user_id=1383283890, username="authorized_user"
        )

    @staticmethod
    def create_unauthorized_update(command: str = "/start") -> Mock:
        """
        Create Update mock for unauthorized user (user ID 999999999).

        Args:
            command: Command string

        Returns:
            Mock Update from unauthorized user
        """
        return TelegramMockFactory.create_command_update(
            command=command, user_id=999999999, username="unauthorized_user"
        )

    @staticmethod
    def create_context(user_data: dict[str, Any] | None = None) -> Mock:
        """
        Create Context mock.

        Args:
            user_data: Optional user_data dictionary

        Returns:
            Mock Context
        """
        if user_data is None:
            user_data = {}

        return ContextBuilder().with_user_data(user_data).build()


# Convenience functions for backwards compatibility with existing fixtures
def mock_telegram_update(
    user_id: int = 1383283890, username: str = "testuser", text: str | None = None
) -> Mock:
    """
    Legacy function for creating Update mocks.

    Prefer using UpdateBuilder or TelegramMockFactory for new tests.
    """
    builder = UpdateBuilder().with_message().with_user(user_id, username)
    if text:
        builder = builder.with_text(text)
    return builder.build()


def mock_telegram_callback_query(
    data: str = "menu_main", user_id: int = 1383283890, username: str = "testuser"
) -> Mock:
    """
    Legacy function for creating callback query Update mocks.

    Prefer using UpdateBuilder or TelegramMockFactory for new tests.
    """
    return TelegramMockFactory.create_callback_update(data, user_id, username)


def mock_telegram_context(user_data: dict[str, Any] | None = None) -> Mock:
    """
    Legacy function for creating Context mocks.

    Prefer using ContextBuilder or TelegramMockFactory for new tests.
    """
    return TelegramMockFactory.create_context(user_data)
