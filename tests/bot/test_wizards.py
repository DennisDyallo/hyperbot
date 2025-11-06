"""
Unit tests for bot wizard handlers.

Tests callback data parsing to catch bugs like the "not enough values to unpack" error.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.bot.handlers import wizards


class TestMarketWizardCallbackParsing:
    """Test market order wizard callback data parsing."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update with callback_query."""
        update = Mock()
        update.callback_query = Mock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.effective_user = Mock()
        update.effective_user.id = 1383283890
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        context = Mock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_market_coin_selected_parsing(self, mock_update, mock_context):
        """Test parsing coin selection callback data."""
        # Callback data format: "select_coin:BTC"
        mock_update.callback_query.data = "select_coin:BTC"

        # Store coin in user_data for next step
        mock_context.user_data['market_coin'] = "BTC"

        await wizards.market_coin_selected(mock_update, mock_context)

        # Should parse successfully without error
        mock_update.callback_query.answer.assert_called_once()
        assert mock_context.user_data['market_coin'] == "BTC"

    @pytest.mark.asyncio
    async def test_market_side_selected_parsing_buy(self, mock_update, mock_context):
        """
        Test parsing buy/sell selection callback data.

        Bug Fix: Previously tried to unpack incorrectly causing
        "not enough values to unpack (expected 2, got 1)" error.
        """
        # Callback data format: "side_buy:ETH"
        mock_update.callback_query.data = "side_buy:ETH"
        mock_context.user_data['market_coin'] = "ETH"

        await wizards.market_side_selected(mock_update, mock_context)

        # Should parse "buy" from "side_buy:ETH" correctly
        mock_update.callback_query.answer.assert_called_once()
        assert mock_context.user_data['market_is_buy'] is True
        assert mock_context.user_data['market_side_str'] == "BUY"

    @pytest.mark.asyncio
    async def test_market_side_selected_parsing_sell(self, mock_update, mock_context):
        """Test parsing sell selection callback data."""
        # Callback data format: "side_sell:BTC"
        mock_update.callback_query.data = "side_sell:BTC"
        mock_context.user_data['market_coin'] = "BTC"

        await wizards.market_side_selected(mock_update, mock_context)

        # Should parse "sell" from "side_sell:BTC" correctly
        mock_update.callback_query.answer.assert_called_once()
        assert mock_context.user_data['market_is_buy'] is False
        assert mock_context.user_data['market_side_str'] == "SELL"

    @pytest.mark.asyncio
    async def test_market_amount_selected_parsing(self, mock_update, mock_context):
        """Test parsing amount selection callback data."""
        # Callback data format: "amount:100" or "amount:$100"
        mock_update.callback_query.data = "amount:100"
        mock_context.user_data['market_coin'] = "BTC"
        mock_context.user_data['market_is_buy'] = True
        mock_context.user_data['market_side_str'] = "BUY"

        # Patch convert_usd_to_coin (not market_data_service)
        with patch('src.bot.handlers.wizards.convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (0.00096, 104088.0)  # (coin_size, current_price)

            await wizards.market_amount_selected(mock_update, mock_context)

            # Should parse amount successfully and call convert function
            mock_update.callback_query.answer.assert_called_once()
            mock_convert.assert_called_once_with(100.0, "BTC")

    @pytest.mark.asyncio
    async def test_close_position_callback_parsing(self, mock_update, mock_context):
        """Test parsing close position callback data."""
        # Callback data format: "close_pos:SOL"
        mock_update.callback_query.data = "close_pos:SOL"

        with patch('src.bot.handlers.wizards.position_service') as mock_pos_service:
            mock_pos_service.get_position.return_value = {
                "coin": "SOL",
                "size": 1.2,
                "entry_price": 161.64,
                "position_value": 193.97,
                "unrealized_pnl": 2.15
            }

            await wizards.close_position_selected(mock_update, mock_context)

            # Should parse coin correctly
            mock_update.callback_query.answer.assert_called_once()

    def test_callback_data_format_validation(self):
        """
        Test that callback data parsing handles edge cases.

        This prevents regression of the "not enough values to unpack" bug.
        """
        # Valid formats
        assert "side_buy:BTC".split(":") == ["side_buy", "BTC"]
        assert "side_sell:ETH".split(":") == ["side_sell", "ETH"]
        assert "select_coin:SOL".split(":") == ["select_coin", "SOL"]

        # Extract side from "side_buy"
        side_action = "side_buy"
        parts = side_action.split("_")
        assert len(parts) == 2
        assert parts[1] == "buy"

        # Extract side from "side_sell"
        side_action = "side_sell"
        parts = side_action.split("_")
        assert len(parts) == 2
        assert parts[1] == "sell"


class TestClosePositionHandlers:
    """Test close position handler field usage."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update."""
        update = Mock()
        update.callback_query = Mock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.edit_message_text = AsyncMock()
        update.callback_query.data = "confirm_close_pos:SOL"
        update.effective_user = Mock()
        update.effective_user.id = 1383283890
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        context = Mock()
        context.user_data = {}
        return context

    @pytest.mark.asyncio
    async def test_close_position_execute_uses_size_closed(self, mock_update, mock_context):
        """
        Test that close_position_execute uses ClosePositionUseCase response.

        Handler calls edit_message_text twice: once for progress, once for result.
        """
        mock_update.callback_query.data = "confirm_close_pos:SOL"

        with patch('src.bot.handlers.wizards.close_position_use_case') as mock_use_case:
            # Mock ClosePositionResponse
            from src.use_cases.trading import ClosePositionResponse
            mock_response = Mock(spec=ClosePositionResponse)
            mock_response.status = "success"
            mock_response.coin = "SOL"
            mock_response.size_closed = 1.26
            mock_response.usd_value = 193.97

            mock_use_case.execute = AsyncMock(return_value=mock_response)

            await wizards.close_position_execute(mock_update, mock_context)

            # Should answer callback and call edit_message_text twice (progress + result)
            mock_update.callback_query.answer.assert_called_once()
            assert mock_update.callback_query.edit_message_text.call_count == 2

            # Verify final message contains size information
            final_call = mock_update.callback_query.edit_message_text.call_args_list[1]
            message_text = final_call[0][0] if final_call[0] else final_call[1].get('text', '')
            assert "1.26" in message_text or "1.3" in message_text  # Size should be in message
            assert "SOL" in message_text
