"""Tests for loading state management."""

import pytest
from telegram import Message, Update

from src.bot.components.loading import LOADING_MESSAGES, LoadingMessage


class TestLoadingMessage:
    """Test LoadingMessage class."""

    def test_get_message_with_formatting(self) -> None:
        """Test getting formatted loading message."""
        message = LoadingMessage.get_message("price", coin="BTC")
        assert message == "⏳ Fetching current BTC price..."

    def test_get_message_without_formatting(self) -> None:
        """Test getting message without format parameters."""
        message = LoadingMessage.get_message("order")
        assert message == "⏳ Placing order..."

    def test_get_message_unknown_action_raises(self) -> None:
        """Test unknown action raises ValueError."""
        with pytest.raises(ValueError, match="Unknown loading action"):
            LoadingMessage.get_message("invalid_action")

    def test_get_message_missing_format_param_raises(self) -> None:
        """Test missing format parameter raises KeyError."""
        with pytest.raises(KeyError):
            LoadingMessage.get_message("price")  # Missing coin parameter

    def test_all_predefined_messages_exist(self) -> None:
        """Test all predefined loading messages are accessible."""
        expected_actions = [
            "preview",
            "price",
            "order",
            "leverage",
            "position",
            "positions",
            "account",
            "close",
            "cancel",
            "market_data",
        ]

        for action in expected_actions:
            assert action in LOADING_MESSAGES

    def test_all_messages_have_emoji(self) -> None:
        """Test all loading messages include the loading emoji."""
        for message in LOADING_MESSAGES.values():
            assert "⏳" in message

    def test_all_messages_have_ellipsis(self) -> None:
        """Test all loading messages end with ellipsis."""
        for message in LOADING_MESSAGES.values():
            assert message.endswith("...")

    def test_leverage_message_formatting(self) -> None:
        """Test leverage message with formatted parameter."""
        message = LoadingMessage.get_message("leverage", leverage="5")
        assert message == "⏳ Setting leverage to 5x..."

    def test_position_message_formatting(self) -> None:
        """Test position message with coin parameter."""
        message = LoadingMessage.get_message("position", coin="ETH")
        assert message == "⏳ Fetching ETH position..."

    def test_close_message_formatting(self) -> None:
        """Test close position message with coin."""
        message = LoadingMessage.get_message("close", coin="SOL")
        assert message == "⏳ Closing SOL position..."


class TestLoadingMessageAsyncMethods:
    """Test async methods (mock-based tests)."""

    @pytest.mark.asyncio
    async def test_show_returns_message_object(self, mocker) -> None:
        """Test show method returns a Message object."""
        # Mock Update with message
        mock_update = mocker.Mock(spec=Update)
        mock_message = mocker.AsyncMock(spec=Message)
        mock_update.message = mock_message
        mock_update.callback_query = None
        mock_message.reply_text.return_value = mock_message

        result = await LoadingMessage.show(mock_update, "order")

        assert result == mock_message
        mock_message.reply_text.assert_called_once_with("⏳ Placing order...")

    @pytest.mark.asyncio
    async def test_show_with_callback_query_edits_message(self, mocker) -> None:
        """Test show with callback query edits existing message."""
        # Mock Update with callback_query
        mock_update = mocker.Mock(spec=Update)
        mock_callback_query = mocker.AsyncMock()
        mock_message = mocker.AsyncMock(spec=Message)
        mock_update.callback_query = mock_callback_query
        mock_update.message = None
        mock_callback_query.edit_message_text.return_value = mock_message

        result = await LoadingMessage.show(mock_update, "order")

        assert result == mock_message
        mock_callback_query.edit_message_text.assert_called_once_with("⏳ Placing order...")

    @pytest.mark.asyncio
    async def test_show_invalid_action_raises(self, mocker) -> None:
        """Test show with invalid action raises ValueError."""
        mock_update = mocker.Mock(spec=Update)
        mock_update.message = mocker.AsyncMock()

        with pytest.raises(ValueError, match="Unknown loading action"):
            await LoadingMessage.show(mock_update, "invalid_action")

    @pytest.mark.asyncio
    async def test_show_no_message_or_callback_raises(self, mocker) -> None:
        """Test show without message or callback_query raises ValueError."""
        mock_update = mocker.Mock(spec=Update)
        mock_update.message = None
        mock_update.callback_query = None

        with pytest.raises(ValueError, match="must have either callback_query or message"):
            await LoadingMessage.show(mock_update, "order")

    @pytest.mark.asyncio
    async def test_hide_edits_message(self, mocker) -> None:
        """Test hide replaces loading message."""
        mock_message = mocker.AsyncMock(spec=Message)
        mock_message.edit_text.return_value = mock_message

        result = await LoadingMessage.hide(mock_message, "✅ Order placed!")

        assert result == mock_message
        mock_message.edit_text.assert_called_once_with("✅ Order placed!")

    @pytest.mark.asyncio
    async def test_show_with_format_params(self, mocker) -> None:
        """Test show with format parameters."""
        mock_update = mocker.Mock(spec=Update)
        mock_message = mocker.AsyncMock(spec=Message)
        mock_update.message = mock_message
        mock_update.callback_query = None
        mock_message.reply_text.return_value = mock_message

        await LoadingMessage.show(mock_update, "price", coin="BTC")

        mock_message.reply_text.assert_called_once_with("⏳ Fetching current BTC price...")
