"""
Tests for state extractor decorators.

Validates the @extract_callback_state and @extract_message_state decorators
that eliminate boilerplate in wizard handlers.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes

from src.bot.components.state_extractor import (
    extract_callback_state,
    extract_message_state,
)


class TestExtractCallbackState:
    """Test @extract_callback_state decorator."""

    @pytest.mark.asyncio
    async def test_extracts_query_and_user_data(self) -> None:
        """Test that decorator extracts query and user_data."""

        @extract_callback_state
        async def handler(update, context, query, user_data):  # type: ignore
            return {"query": query, "user_data": user_data}

        # Setup mocks
        query = AsyncMock(spec=CallbackQuery)
        query.data = "test_data"
        query.answer = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        user_data = {"test": "value"}
        context.user_data = user_data

        # Call decorated handler
        result = await handler(update, context)

        # Verify query was answered
        query.answer.assert_called_once()

        # Verify extracted values were passed
        assert result["query"] == query
        assert result["user_data"] == user_data

    @pytest.mark.asyncio
    async def test_answers_callback_query(self) -> None:
        """Test that decorator automatically answers callback query."""

        @extract_callback_state
        async def handler(update, context, query, user_data):  # type: ignore
            return "success"

        # Setup mocks
        query = AsyncMock(spec=CallbackQuery)
        query.answer = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {"test": "value"}

        # Call decorated handler
        await handler(update, context)

        # Verify query.answer() was called
        query.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_on_missing_query(self) -> None:
        """Test that decorator raises ValueError when query is None."""

        @extract_callback_state
        async def handler(update, context, query, user_data):  # type: ignore
            return "success"

        # Setup mocks with None query
        update = MagicMock(spec=Update)
        update.callback_query = None

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {"test": "value"}

        # Should raise ValueError
        with pytest.raises(ValueError, match="Expected callback query"):
            await handler(update, context)

    @pytest.mark.asyncio
    async def test_raises_on_missing_user_data(self) -> None:
        """Test that decorator raises ValueError when user_data is None."""

        @extract_callback_state
        async def handler(update, context, query, user_data):  # type: ignore
            return "success"

        # Setup mocks with None user_data
        query = AsyncMock(spec=CallbackQuery)
        query.answer = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = None

        # Should raise ValueError
        with pytest.raises(ValueError, match="Expected user_data"):
            await handler(update, context)

    @pytest.mark.asyncio
    async def test_preserves_handler_return_value(self) -> None:
        """Test that decorator preserves handler's return value."""

        @extract_callback_state
        async def handler(update, context, query, user_data):  # type: ignore
            return 42

        # Setup mocks
        query = AsyncMock(spec=CallbackQuery)
        query.answer = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {"test": "value"}

        # Call decorated handler
        result = await handler(update, context)

        assert result == 42

    @pytest.mark.asyncio
    async def test_allows_handler_to_modify_user_data(self) -> None:
        """Test that handler can modify user_data dict."""

        @extract_callback_state
        async def handler(update, context, query, user_data):  # type: ignore
            user_data["new_key"] = "new_value"
            return user_data

        # Setup mocks
        query = AsyncMock(spec=CallbackQuery)
        query.answer = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        user_data = {"existing": "value"}
        context.user_data = user_data

        # Call decorated handler
        result = await handler(update, context)

        # Verify user_data was modified
        assert result["existing"] == "value"
        assert result["new_key"] == "new_value"

    @pytest.mark.asyncio
    async def test_can_access_query_data(self) -> None:
        """Test that handler can access query.data."""

        @extract_callback_state
        async def handler(update, context, query, user_data):  # type: ignore
            return query.data

        # Setup mocks
        query = AsyncMock(spec=CallbackQuery)
        query.data = "select_coin:BTC"
        query.answer = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        # Call decorated handler
        result = await handler(update, context)

        assert result == "select_coin:BTC"


class TestExtractMessageState:
    """Test @extract_message_state decorator."""

    @pytest.mark.asyncio
    async def test_extracts_user_data(self) -> None:
        """Test that decorator extracts user_data."""

        @extract_message_state
        async def handler(update, context, user_data):  # type: ignore
            return user_data

        # Setup mocks
        update = MagicMock(spec=Update)
        update.message = MagicMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        user_data = {"test": "value"}
        context.user_data = user_data

        # Call decorated handler
        result = await handler(update, context)

        assert result == user_data

    @pytest.mark.asyncio
    async def test_raises_on_missing_user_data(self) -> None:
        """Test that decorator raises ValueError when user_data is None."""

        @extract_message_state
        async def handler(update, context, user_data):  # type: ignore
            return "success"

        # Setup mocks with None user_data
        update = MagicMock(spec=Update)
        update.message = MagicMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = None

        # Should raise ValueError
        with pytest.raises(ValueError, match="Expected user_data"):
            await handler(update, context)

    @pytest.mark.asyncio
    async def test_preserves_handler_return_value(self) -> None:
        """Test that decorator preserves handler's return value."""

        @extract_message_state
        async def handler(update, context, user_data):  # type: ignore
            return 42

        # Setup mocks
        update = MagicMock(spec=Update)
        update.message = MagicMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {"test": "value"}

        # Call decorated handler
        result = await handler(update, context)

        assert result == 42

    @pytest.mark.asyncio
    async def test_allows_handler_to_modify_user_data(self) -> None:
        """Test that handler can modify user_data dict."""

        @extract_message_state
        async def handler(update, context, user_data):  # type: ignore
            user_data["new_key"] = "new_value"
            return user_data

        # Setup mocks
        update = MagicMock(spec=Update)
        update.message = MagicMock()

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        user_data = {"existing": "value"}
        context.user_data = user_data

        # Call decorated handler
        result = await handler(update, context)

        # Verify user_data was modified
        assert result["existing"] == "value"
        assert result["new_key"] == "new_value"

    @pytest.mark.asyncio
    async def test_can_access_message_text(self) -> None:
        """Test that handler can access message.text."""

        @extract_message_state
        async def handler(update, context, user_data):  # type: ignore
            return update.message.text

        # Setup mocks
        update = MagicMock(spec=Update)
        update.message = MagicMock()
        update.message.text = "100"

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        # Call decorated handler
        result = await handler(update, context)

        assert result == "100"


class TestStateExtractorIntegration:
    """Integration tests for state extractors."""

    @pytest.mark.asyncio
    async def test_callback_state_realistic_wizard_flow(self) -> None:
        """Test decorator in realistic wizard scenario."""

        @extract_callback_state
        async def coin_selected(update, context, query, user_data):  # type: ignore
            # Parse callback data
            coin = query.data.split(":")[1]
            user_data["coin"] = coin
            return f"selected_{coin}"

        # Setup realistic mocks
        query = AsyncMock(spec=CallbackQuery)
        query.data = "select_coin:BTC"
        query.answer = AsyncMock()
        query.edit_message_text = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        # Call handler
        result = await coin_selected(update, context)

        # Verify flow
        query.answer.assert_called_once()
        assert result == "selected_BTC"
        assert context.user_data["coin"] == "BTC"

    @pytest.mark.asyncio
    async def test_message_state_realistic_wizard_flow(self) -> None:
        """Test message decorator in realistic wizard scenario."""

        @extract_message_state
        async def amount_entered(update, context, user_data):  # type: ignore
            # Parse message text
            amount_text = update.message.text
            amount = float(amount_text.replace("$", ""))
            user_data["amount"] = amount
            return f"amount_{amount}"

        # Setup realistic mocks
        update = MagicMock(spec=Update)
        update.message = MagicMock()
        update.message.text = "$100.50"

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {"coin": "BTC"}

        # Call handler
        result = await amount_entered(update, context)

        # Verify flow
        assert result == "amount_100.5"
        assert context.user_data["amount"] == 100.5
        assert context.user_data["coin"] == "BTC"  # Preserved from before

    @pytest.mark.asyncio
    async def test_multiple_decorated_handlers_share_state(self) -> None:
        """Test that multiple handlers can share user_data state."""

        @extract_callback_state
        async def handler1(update, context, query, user_data):  # type: ignore
            user_data["step1"] = "done"
            return "step1"

        @extract_callback_state
        async def handler2(update, context, query, user_data):  # type: ignore
            user_data["step2"] = "done"
            return user_data

        # Setup mocks
        query = AsyncMock(spec=CallbackQuery)
        query.answer = AsyncMock()

        update = MagicMock(spec=Update)
        update.callback_query = query

        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.user_data = {}

        # Call handlers in sequence
        await handler1(update, context)
        result = await handler2(update, context)

        # Verify state was shared
        assert result["step1"] == "done"
        assert result["step2"] == "done"
