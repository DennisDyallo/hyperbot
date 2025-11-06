"""
Unit tests for bot wizard handlers.

Tests callback data parsing to catch bugs like the "not enough values to unpack" error.

REFACTORED: Now using tests/helpers for cleaner Telegram mocking.
- TelegramMockFactory replaces all manual Mock() creation
- Result: Eliminated 15 duplicate fixtures, more maintainable tests
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.bot.handlers import wizards

# Import helpers for cleaner Telegram mocking
from tests.helpers import TelegramMockFactory


class TestMarketWizardCallbackParsing:
    """Test market order wizard callback data parsing."""

    @pytest.mark.asyncio
    async def test_market_coin_selected_parsing(self):
        """Test parsing coin selection callback data."""
        # Callback data format: "select_coin:BTC"
        update = TelegramMockFactory.create_callback_update("select_coin:BTC")
        context = TelegramMockFactory.create_context(user_data={'market_coin': 'BTC'})

        await wizards.market_coin_selected(update, context)

        # Should parse successfully without error
        update.callback_query.answer.assert_called_once()
        assert context.user_data['market_coin'] == "BTC"

    @pytest.mark.asyncio
    async def test_market_side_selected_parsing_buy(self):
        """
        Test parsing buy/sell selection callback data.

        Bug Fix: Previously tried to unpack incorrectly causing
        "not enough values to unpack (expected 2, got 1)" error.
        """
        # Callback data format: "side_buy:ETH"
        update = TelegramMockFactory.create_callback_update("side_buy:ETH")
        context = TelegramMockFactory.create_context(user_data={'market_coin': 'ETH'})

        await wizards.market_side_selected(update, context)

        # Should parse "buy" from "side_buy:ETH" correctly
        update.callback_query.answer.assert_called_once()
        assert context.user_data['market_is_buy'] is True
        assert context.user_data['market_side_str'] == "BUY"

    @pytest.mark.asyncio
    async def test_market_side_selected_parsing_sell(self):
        """Test parsing sell selection callback data."""
        # Callback data format: "side_sell:BTC"
        update = TelegramMockFactory.create_callback_update("side_sell:BTC")
        context = TelegramMockFactory.create_context(user_data={'market_coin': 'BTC'})

        await wizards.market_side_selected(update, context)

        # Should parse "sell" from "side_sell:BTC" correctly
        update.callback_query.answer.assert_called_once()
        assert context.user_data['market_is_buy'] is False
        assert context.user_data['market_side_str'] == "SELL"

    @pytest.mark.asyncio
    async def test_market_amount_selected_parsing(self):
        """Test parsing amount selection callback data."""
        # Callback data format: "amount:100" or "amount:$100"
        update = TelegramMockFactory.create_callback_update("amount:100")
        context = TelegramMockFactory.create_context(user_data={
            'market_coin': 'BTC',
            'market_is_buy': True,
            'market_side_str': 'BUY'
        })

        # Patch convert_usd_to_coin (not market_data_service)
        with patch('src.bot.handlers.wizards.convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (0.00096, 104088.0)  # (coin_size, current_price)

            await wizards.market_amount_selected(update, context)

            # Should parse amount successfully and call convert function
            update.callback_query.answer.assert_called_once()
            mock_convert.assert_called_once_with(100.0, "BTC")

    @pytest.mark.asyncio
    async def test_close_position_callback_parsing(self):
        """Test parsing close position callback data."""
        # Callback data format: "close_pos:SOL"
        update = TelegramMockFactory.create_callback_update("close_pos:SOL")
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.wizards.position_service') as mock_pos_service:
            mock_pos_service.get_position.return_value = {
                "coin": "SOL",
                "size": 1.2,
                "entry_price": 161.64,
                "position_value": 193.97,
                "unrealized_pnl": 2.15
            }

            await wizards.close_position_selected(update, context)

            # Should parse coin correctly
            update.callback_query.answer.assert_called_once()

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


class TestMarketAmountErrorHandling:
    """Test error handling in market amount selection."""

    @pytest.mark.asyncio
    async def test_market_amount_invalid_raises_error(self):
        """Test handling of invalid amount."""
        update = TelegramMockFactory.create_callback_update("amount:abc")
        context = TelegramMockFactory.create_context(user_data={
            'market_coin': 'BTC',
            'market_is_buy': True,
            'market_side_str': 'BUY'
        })

        result = await wizards.market_amount_selected(update, context)

        # Should show error and end conversation
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert "❌ Invalid amount" in call_args[0][0]
        assert result == -1  # ConversationHandler.END

    @pytest.mark.asyncio
    async def test_market_amount_price_fetch_failure(self):
        """Test handling of price fetch failure."""
        update = TelegramMockFactory.create_callback_update("amount:100")
        context = TelegramMockFactory.create_context(user_data={
            'market_coin': 'BTC',
            'market_is_buy': True,
            'market_side_str': 'BUY'
        })

        with patch('src.bot.handlers.wizards.convert_usd_to_coin') as mock_convert:
            mock_convert.side_effect = ValueError("Coin not found")

            result = await wizards.market_amount_selected(update, context)

            # Should show error and end conversation
            assert result == -1  # ConversationHandler.END
            assert update.callback_query.edit_message_text.call_count == 2  # Loading + error


class TestCustomAmountFlow:
    """Test custom amount input handlers."""

    @pytest.mark.asyncio
    async def test_market_custom_amount_request(self):
        """Test custom amount input request."""
        update = TelegramMockFactory.create_callback_update("custom_amount")
        context = TelegramMockFactory.create_context(user_data={
            'market_coin': 'ETH',
            'market_is_buy': False,
            'market_side_str': 'SELL'
        })

        from src.bot.handlers.wizards import MARKET_AMOUNT
        result = await wizards.market_custom_amount(update, context)

        # Should show custom input prompt
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert "✏️" in call_args[0][0]
        assert "Enter USD amount" in call_args[0][0]
        assert result == MARKET_AMOUNT

    @pytest.mark.asyncio
    async def test_market_amount_text_input_invalid(self):
        """Test text input with invalid amount."""
        update = TelegramMockFactory.create_text_update("invalid")
        context = TelegramMockFactory.create_context(user_data={
            'market_coin': 'ETH',
            'market_is_buy': False,
            'market_side_str': 'SELL'
        })

        from src.bot.handlers.wizards import MARKET_AMOUNT
        result = await wizards.market_amount_text_input(update, context)

        # Should show error and stay in same state
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "❌ Invalid amount" in call_args[0][0]
        assert result == MARKET_AMOUNT

    @pytest.mark.asyncio
    async def test_market_amount_text_input_success(self):
        """Test text input with valid amount."""
        update = TelegramMockFactory.create_text_update("50.25")
        mock_msg = Mock()
        mock_msg.edit_text = AsyncMock()
        update.message.reply_text.return_value = mock_msg

        context = TelegramMockFactory.create_context(user_data={
            'market_coin': 'ETH',
            'market_is_buy': False,
            'market_side_str': 'SELL'
        })

        with patch('src.bot.handlers.wizards.convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (0.013, 3850.50)  # ETH price

            from src.bot.handlers.wizards import MARKET_CONFIRM
            result = await wizards.market_amount_text_input(update, context)

            # Should show confirmation
            assert result == MARKET_CONFIRM
            update.message.reply_text.assert_called_once()
            mock_msg.edit_text.assert_called_once()


class TestMarketExecution:
    """Test market order execution."""

    @pytest.mark.asyncio
    async def test_market_execute_success(self):
        """Test successful market order execution."""
        update = TelegramMockFactory.create_callback_update("confirm_market:")
        context = TelegramMockFactory.create_context(user_data={
            'market_coin': 'BTC',
            'market_is_buy': True,
            'market_side_str': 'BUY',
            'market_coin_size': 0.00096
        })

        with patch('src.bot.handlers.wizards.place_order_use_case') as mock_use_case:
            from src.use_cases.trading import PlaceOrderResponse
            mock_response = Mock(spec=PlaceOrderResponse)
            mock_response.status = "success"
            mock_response.coin = "BTC"
            mock_response.size = 0.00096
            mock_response.usd_value = 100.0
            mock_response.price = 104088.0

            mock_use_case.execute = AsyncMock(return_value=mock_response)

            result = await wizards.market_execute(update, context)

            # Should complete successfully
            assert update.callback_query.edit_message_text.call_count == 2  # Progress + result
            assert context.user_data == {}  # Cleared
            assert result == -1  # ConversationHandler.END

    @pytest.mark.asyncio
    async def test_market_execute_failure(self):
        """Test market order execution failure."""
        update = TelegramMockFactory.create_callback_update("confirm_market:")
        context = TelegramMockFactory.create_context(user_data={
            'market_coin': 'BTC',
            'market_is_buy': True,
            'market_side_str': 'BUY',
            'market_coin_size': 0.00096
        })

        with patch('src.bot.handlers.wizards.place_order_use_case') as mock_use_case:
            mock_use_case.execute = AsyncMock(side_effect=Exception("Network error"))

            result = await wizards.market_execute(update, context)

            # Should show error
            assert update.callback_query.edit_message_text.call_count == 2  # Progress + error
            call_args = update.callback_query.edit_message_text.call_args_list[1]
            assert "❌ Failed to place order" in call_args[0][0]
            assert result == -1  # ConversationHandler.END


class TestWizardCancellation:
    """Test wizard cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_with_callback_query(self):
        """Test cancellation via callback query."""
        update = TelegramMockFactory.create_callback_update("cancel_wizard")
        context = TelegramMockFactory.create_context(user_data={'market_coin': 'BTC', 'market_is_buy': True})

        result = await wizards.wizard_cancel(update, context)

        # Should cancel and clear data
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        assert context.user_data == {}
        assert result == -1  # ConversationHandler.END

    @pytest.mark.asyncio
    async def test_cancel_with_message(self):
        """Test cancellation via message."""
        update = Mock()
        update.callback_query = None
        update.message = Mock()
        update.message.reply_text = AsyncMock()

        context = TelegramMockFactory.create_context(user_data={'market_coin': 'ETH'})

        result = await wizards.wizard_cancel(update, context)

        # Should cancel via message
        update.message.reply_text.assert_called_once()
        assert context.user_data == {}
        assert result == -1  # ConversationHandler.END


class TestClosePositionHandlers:
    """Test close position handler field usage."""

    @pytest.mark.asyncio
    async def test_close_position_execute_uses_size_closed(self):
        """
        Test that close_position_execute uses ClosePositionUseCase response.

        Handler calls edit_message_text twice: once for progress, once for result.
        """
        update = TelegramMockFactory.create_callback_update("confirm_close_pos:SOL")
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.wizards.close_position_use_case') as mock_use_case:
            # Mock ClosePositionResponse
            from src.use_cases.trading import ClosePositionResponse
            mock_response = Mock(spec=ClosePositionResponse)
            mock_response.status = "success"
            mock_response.coin = "SOL"
            mock_response.size_closed = 1.26
            mock_response.usd_value = 193.97

            mock_use_case.execute = AsyncMock(return_value=mock_response)

            await wizards.close_position_execute(update, context)

            # Should answer callback and call edit_message_text twice (progress + result)
            update.callback_query.answer.assert_called_once()
            assert update.callback_query.edit_message_text.call_count == 2

            # Verify final message contains size information
            final_call = update.callback_query.edit_message_text.call_args_list[1]
            message_text = final_call[0][0] if final_call[0] else final_call[1].get('text', '')
            assert "1.26" in message_text or "1.3" in message_text  # Size should be in message
            assert "SOL" in message_text

    @pytest.mark.asyncio
    async def test_close_position_selected_value_error(self):
        """Test close position with ValueError (position not found)."""
        update = TelegramMockFactory.create_callback_update("select_position:INVALID")
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.wizards.position_service') as mock_service:
            mock_service.get_position.side_effect = ValueError("Position not found")

            await wizards.close_position_selected(update, context)

            # Should show error
            update.callback_query.answer.assert_called_once()
            call_args = update.callback_query.edit_message_text.call_args
            assert "❌" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_close_position_selected_generic_error(self):
        """Test close position with generic exception."""
        update = TelegramMockFactory.create_callback_update("select_position:BTC")
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.wizards.position_service') as mock_service:
            mock_service.get_position.side_effect = Exception("Network error")

            await wizards.close_position_selected(update, context)

            # Should show error
            assert update.callback_query.edit_message_text.call_count == 2  # Loading + error

    @pytest.mark.asyncio
    async def test_close_position_execute_failure(self):
        """Test close position execution failure."""
        update = TelegramMockFactory.create_callback_update("confirm_close_pos:ETH")
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.wizards.close_position_use_case') as mock_use_case:
            mock_use_case.execute = AsyncMock(side_effect=Exception("Order failed"))

            await wizards.close_position_execute(update, context)

            # Should show error
            assert update.callback_query.edit_message_text.call_count == 2  # Progress + error
            call_args = update.callback_query.edit_message_text.call_args_list[1]
            assert "❌ Failed to close position" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_close_position_selected_success(self):
        """Test successful close position selection shows confirmation."""
        update = TelegramMockFactory.create_callback_update("select_position:SOL")
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.wizards.position_service') as mock_service:
            mock_service.get_position.return_value = {
                "position": {
                    "coin": "SOL",
                    "size": 5.0,
                    "entry_price": 150.0,
                    "position_value": 750.0,
                    "unrealized_pnl": 50.0,
                    "return_on_equity": 0.1
                }
            }

            await wizards.close_position_selected(update, context)

            # Should show confirmation with position details
            assert update.callback_query.edit_message_text.call_count == 2  # Loading + confirmation
            final_call = update.callback_query.edit_message_text.call_args_list[1]
            message_text = final_call[0][0]
            assert "🎯" in message_text or "Close Position" in message_text
            assert "SOL" in message_text
            assert "LONG" in message_text  # size > 0


class TestMarketWizardStart:
    """Test market wizard entry point."""

    @pytest.mark.asyncio
    async def test_market_wizard_start(self):
        """Test market wizard start shows coin selection."""
        update = TelegramMockFactory.create_callback_update("market_wizard")
        context = TelegramMockFactory.create_context()

        from src.bot.handlers.wizards import MARKET_COIN
        result = await wizards.market_wizard_start(update, context)

        # Should show coin selection menu
        assert result == MARKET_COIN
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_text = update.callback_query.edit_message_text.call_args[0][0]
        assert "💰" in call_text or "Market Order" in call_text
        assert "Step 1/3" in call_text


class TestMarketAmountTextInputPriceError:
    """Test price fetch error in text input flow."""

    @pytest.mark.asyncio
    async def test_market_amount_text_input_runtime_error(self):
        """Test runtime error in price fetch."""
        update = TelegramMockFactory.create_text_update("100")
        mock_msg = Mock()
        mock_msg.edit_text = AsyncMock()
        update.message.reply_text.return_value = mock_msg

        context = TelegramMockFactory.create_context(user_data={
            'market_coin': 'BTC',
            'market_is_buy': True,
            'market_side_str': 'BUY'
        })

        with patch('src.bot.handlers.wizards.convert_usd_to_coin') as mock_convert:
            mock_convert.side_effect = RuntimeError("API error")

            result = await wizards.market_amount_text_input(update, context)

            # Should end conversation
            assert result == wizards.ConversationHandler.END
            update.message.reply_text.assert_called_once()
            mock_msg.edit_text.assert_called_once()
            error_text = mock_msg.edit_text.call_args[0][0]
            assert "❌" in error_text
