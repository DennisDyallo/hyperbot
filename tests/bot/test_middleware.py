"""
Unit tests for bot middleware and decorators.

Tests authorization decorators that restrict command access.

REFACTORED: Now using tests/helpers for Telegram mock creation.
"""
import pytest
from unittest.mock import patch
from telegram import Update
from telegram.ext import ContextTypes
from src.bot.middleware import authorized_only, admin_only

# Import helpers for cleaner Telegram mocking
from tests.helpers import TelegramMockFactory


class TestAuthorizedOnlyDecorator:
    """Test authorized_only decorator."""

    @pytest.fixture
    def authorized_user_id(self):
        """Return an authorized user ID."""
        return 1383283890

    @pytest.fixture
    def unauthorized_user_id(self):
        """Return an unauthorized user ID."""
        return 999999999

    @pytest.mark.asyncio
    async def test_authorized_user_can_access(self, authorized_user_id):
        """Test that authorized users can access decorated functions."""
        update = TelegramMockFactory.create_command_update(
            "/test_command",
            user_id=authorized_user_id,
            username="test_user"
        )
        context = TelegramMockFactory.create_context()

        @authorized_only
        async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            return "success"

        with patch('src.bot.middleware.settings.TELEGRAM_AUTHORIZED_USERS', [authorized_user_id]):
            result = await test_command(update, context)

        assert result == "success"
        update.message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_unauthorized_user_blocked(self, unauthorized_user_id, authorized_user_id):
        """Test that unauthorized users are blocked."""
        update = TelegramMockFactory.create_command_update(
            "/test_command",
            user_id=unauthorized_user_id,
            username="hacker"
        )
        context = TelegramMockFactory.create_context()

        @authorized_only
        async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            return "success"

        with patch('src.bot.middleware.settings.TELEGRAM_AUTHORIZED_USERS', [authorized_user_id]):
            result = await test_command(update, context)

        # Should return None (blocked)
        assert result is None

        # Should send unauthorized message
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        message = call_args[0][0]
        assert "🚫 Unauthorized" in message
        assert str(unauthorized_user_id) in message

    @pytest.mark.asyncio
    async def test_unauthorized_user_without_username(self, unauthorized_user_id, authorized_user_id):
        """Test unauthorized user without username."""
        update = TelegramMockFactory.create_command_update(
            "/test_command",
            user_id=unauthorized_user_id,
            username=None
        )
        context = TelegramMockFactory.create_context()

        @authorized_only
        async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            return "success"

        with patch('src.bot.middleware.settings.TELEGRAM_AUTHORIZED_USERS', [authorized_user_id]):
            result = await test_command(update, context)

        assert result is None
        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_user_id_blocked(self):
        """Test that requests without user ID are blocked."""
        # Create update without effective_user
        update = TelegramMockFactory.create_command_update("/test_command")
        update.effective_user = None
        context = TelegramMockFactory.create_context()

        @authorized_only
        async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            return "success"

        result = await test_command(update, context)

        # Should return None (blocked)
        assert result is None

        # Should not send message (no user to reply to)
        if hasattr(update, 'message') and update.message:
            update.message.reply_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_callback_query_authorized(self, authorized_user_id):
        """Test authorization works with callback queries (no message)."""
        # Create callback query update (no message)
        update = TelegramMockFactory.create_callback_update(
            "menu_main",
            user_id=authorized_user_id,
            username="test_user"
        )
        context = TelegramMockFactory.create_context()

        @authorized_only
        async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            return "success"

        with patch('src.bot.middleware.settings.TELEGRAM_AUTHORIZED_USERS', [authorized_user_id]):
            result = await test_command(update, context)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves original function metadata."""
        @authorized_only
        async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            """Test command docstring."""
            pass

        # functools.wraps should preserve function name and docstring
        assert test_command.__name__ == "test_command"
        assert "Test command docstring" in test_command.__doc__

    @pytest.mark.asyncio
    async def test_decorator_passes_args_and_kwargs(self, authorized_user_id):
        """Test that decorator passes through additional args and kwargs."""
        update = TelegramMockFactory.create_command_update(
            "/test_command",
            user_id=authorized_user_id,
            username="test_user"
        )
        context = TelegramMockFactory.create_context()

        @authorized_only
        async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE, arg1, kwarg1=None):
            return f"arg1={arg1}, kwarg1={kwarg1}"

        with patch('src.bot.middleware.settings.TELEGRAM_AUTHORIZED_USERS', [authorized_user_id]):
            result = await test_command(update, context, "value1", kwarg1="value2")

        assert result == "arg1=value1, kwarg1=value2"


class TestAdminOnlyDecorator:
    """Test admin_only decorator."""

    @pytest.fixture
    def authorized_user_id(self):
        """Return an authorized user ID."""
        return 1383283890

    @pytest.mark.asyncio
    async def test_admin_only_delegates_to_authorized_only(self, authorized_user_id):
        """Test that admin_only currently delegates to authorized_only."""
        update = TelegramMockFactory.create_command_update(
            "/admin_command",
            user_id=authorized_user_id,
            username="admin_user"
        )
        context = TelegramMockFactory.create_context()

        @admin_only
        async def test_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
            return "admin_success"

        with patch('src.bot.middleware.settings.TELEGRAM_AUTHORIZED_USERS', [authorized_user_id]):
            result = await test_admin_command(update, context)

        assert result == "admin_success"
        update.message.reply_text.assert_not_called()
