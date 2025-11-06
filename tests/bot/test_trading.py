"""
Unit tests for trading command handlers.

Tests /close and /market commands with their callbacks.

MIGRATED: Now using tests/helpers for Telegram mocking.
- TelegramMockFactory replaces manual Mock() boilerplate
- UpdateBuilder and ContextBuilder for cleaner test setup
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.bot.handlers import trading

# Import helpers for cleaner Telegram mocking
from tests.helpers import TelegramMockFactory, UpdateBuilder, ContextBuilder


@pytest.fixture
def authorized_user_id():
    """Authorized user ID."""
    return 1383283890


class TestCloseCommand:
    """Test /close command handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update with editable message support."""
        update = UpdateBuilder().with_message().with_user(1383283890).build()
        # Add edit_text support for progress messages
        mock_msg = Mock()
        mock_msg.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=mock_msg)
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        return ContextBuilder().build()

    @pytest.mark.asyncio
    async def test_close_command_no_args(self, mock_update, mock_context):
        """Test /close without arguments shows usage."""
        await trading.close_command(mock_update, mock_context)

        # Should show usage message
        mock_update.message.reply_text.assert_called_once()
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in call_text
        assert "/close <coin>" in call_text

    @pytest.mark.asyncio
    async def test_close_command_success(self, mock_update, mock_context):
        """Test /close with valid position."""
        mock_context.args = ["BTC"]
        mock_position = {
            "position": {
                "coin": "BTC",
                "size": 0.5,
                "entry_price": 100000.0,
                "position_value": 50000.0,
                "unrealized_pnl": 1000.0,
                "return_on_equity": 0.02
            }
        }

        with patch('src.bot.handlers.trading.position_service') as mock_service:
            mock_service.get_position.return_value = mock_position

            await trading.close_command(mock_update, mock_context)

        # Should show confirmation
        mock_msg = mock_update.message.reply_text.return_value
        mock_msg.edit_text.assert_called_once()
        call_text = mock_msg.edit_text.call_args[0][0]
        assert "Close Position Confirmation" in call_text or "📊" in call_text
        assert "BTC" in call_text
        assert "LONG" in call_text
        # Should have reply_markup with confirmation buttons
        assert "reply_markup" in mock_msg.edit_text.call_args[1]

    @pytest.mark.asyncio
    async def test_close_command_position_not_found(self, mock_update, mock_context):
        """Test /close with non-existent position."""
        mock_context.args = ["INVALID"]

        with patch('src.bot.handlers.trading.position_service') as mock_service:
            mock_service.get_position.side_effect = ValueError("Position not found")

            await trading.close_command(mock_update, mock_context)

        # Should show error
        mock_msg = mock_update.message.reply_text.return_value
        mock_msg.edit_text.assert_called_once()
        call_text = mock_msg.edit_text.call_args[0][0]
        assert "❌" in call_text
        assert "Position not found" in call_text

    @pytest.mark.asyncio
    async def test_close_command_generic_error(self, mock_update, mock_context):
        """Test /close with generic error."""
        mock_context.args = ["BTC"]

        with patch('src.bot.handlers.trading.position_service') as mock_service:
            mock_service.get_position.side_effect = Exception("API error")

            await trading.close_command(mock_update, mock_context)

        # Should handle error
        # Either in reply_text or in edit_text
        assert mock_update.message.reply_text.call_count >= 1


class TestCloseCallback:
    """Test close position callback handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update with callback query."""
        # Use builder for callback query - data will be set in individual tests
        return UpdateBuilder().with_callback_query("").with_user(1383283890).build()

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        return ContextBuilder().build()

    @pytest.mark.asyncio
    async def test_close_callback_cancel(self, mock_update, mock_context):
        """Test close callback with cancel."""
        mock_update.callback_query.data = "close_cancel"

        await trading.close_callback(mock_update, mock_context)

        # Should show cancelled message
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_text = mock_update.callback_query.edit_message_text.call_args[0][0]
        assert "cancelled" in call_text.lower()

    @pytest.mark.asyncio
    async def test_close_callback_confirm_success(self, mock_update, mock_context):
        """Test close callback confirmation success."""
        mock_update.callback_query.data = "close_confirm:BTC"
        mock_result = {
            "status": "success",
            "size": 0.5
        }

        with patch('src.bot.handlers.trading.position_service') as mock_service:
            with patch('src.bot.handlers.trading.convert_coin_to_usd') as mock_convert:
                mock_service.close_position.return_value = mock_result
                mock_convert.return_value = (50000.0, 100000.0)

                await trading.close_callback(mock_update, mock_context)

        # Should show success message
        assert mock_update.callback_query.edit_message_text.call_count == 2  # Processing + success
        final_call_text = mock_update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "✅" in final_call_text or "Position Closed" in final_call_text
        assert "BTC" in final_call_text

    @pytest.mark.asyncio
    async def test_close_callback_error(self, mock_update, mock_context):
        """Test close callback with error."""
        mock_update.callback_query.data = "close_confirm:ETH"

        with patch('src.bot.handlers.trading.position_service') as mock_service:
            mock_service.close_position.side_effect = Exception("Order failed")

            await trading.close_callback(mock_update, mock_context)

        # Should show error
        assert mock_update.callback_query.edit_message_text.call_count == 2  # Processing + error
        final_call_text = mock_update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "❌" in final_call_text or "Failed" in final_call_text


class TestMarketCommand:
    """Test /market command handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update with editable message support."""
        update = UpdateBuilder().with_message().with_user(1383283890).build()
        # Add edit_text support for progress messages
        mock_msg = Mock()
        mock_msg.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=mock_msg)
        return update

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        return ContextBuilder().build()

    @pytest.mark.asyncio
    async def test_market_command_no_args(self, mock_update, mock_context):
        """Test /market without arguments shows usage."""
        await trading.market_command(mock_update, mock_context)

        # Should show usage
        mock_update.message.reply_text.assert_called_once()
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in call_text
        assert "/market" in call_text

    @pytest.mark.asyncio
    async def test_market_command_insufficient_args(self, mock_update, mock_context):
        """Test /market with too few arguments."""
        mock_context.args = ["BTC", "buy"]  # Missing amount

        await trading.market_command(mock_update, mock_context)

        # Should show usage
        mock_update.message.reply_text.assert_called_once()
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "Usage" in call_text

    @pytest.mark.asyncio
    async def test_market_command_invalid_side(self, mock_update, mock_context):
        """Test /market with invalid side."""
        mock_context.args = ["BTC", "invalid", "100"]

        await trading.market_command(mock_update, mock_context)

        # Should show error
        mock_update.message.reply_text.assert_called_once()
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "Invalid side" in call_text

    @pytest.mark.asyncio
    async def test_market_command_invalid_amount(self, mock_update, mock_context):
        """Test /market with invalid USD amount."""
        mock_context.args = ["BTC", "buy", "invalid"]

        with patch('src.bot.handlers.trading.parse_usd_amount') as mock_parse:
            mock_parse.side_effect = ValueError("Invalid amount format")

            await trading.market_command(mock_update, mock_context)

        # Should show error
        mock_update.message.reply_text.assert_called_once()
        call_text = mock_update.message.reply_text.call_args[0][0]
        assert "❌" in call_text

    @pytest.mark.asyncio
    async def test_market_command_buy_success(self, mock_update, mock_context):
        """Test /market buy with valid parameters."""
        mock_context.args = ["BTC", "buy", "100"]

        with patch('src.bot.handlers.trading.convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (0.00096, 104088.0)

            await trading.market_command(mock_update, mock_context)

        # Should show confirmation
        mock_msg = mock_update.message.reply_text.return_value
        mock_msg.edit_text.assert_called_once()
        call_text = mock_msg.edit_text.call_args[0][0]
        assert "Market Order Confirmation" in call_text or "🟢" in call_text
        assert "BTC" in call_text
        assert "BUY" in call_text
        # Should have reply_markup
        assert "reply_markup" in mock_msg.edit_text.call_args[1]

    @pytest.mark.asyncio
    async def test_market_command_sell_success(self, mock_update, mock_context):
        """Test /market sell with valid parameters."""
        mock_context.args = ["ETH", "sell", "$50"]

        with patch('src.bot.handlers.trading.convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (0.013, 3850.0)

            await trading.market_command(mock_update, mock_context)

        # Should show confirmation
        mock_msg = mock_update.message.reply_text.return_value
        mock_msg.edit_text.assert_called_once()
        call_text = mock_msg.edit_text.call_args[0][0]
        assert "Market Order Confirmation" in call_text or "🔴" in call_text
        assert "ETH" in call_text
        assert "SELL" in call_text

    @pytest.mark.asyncio
    async def test_market_command_price_fetch_error(self, mock_update, mock_context):
        """Test /market with price fetch error."""
        mock_context.args = ["BTC", "buy", "100"]

        with patch('src.bot.handlers.trading.convert_usd_to_coin') as mock_convert:
            mock_convert.side_effect = ValueError("Coin not found")

            await trading.market_command(mock_update, mock_context)

        # Should show error
        mock_msg = mock_update.message.reply_text.return_value
        mock_msg.edit_text.assert_called_once()
        call_text = mock_msg.edit_text.call_args[0][0]
        assert "❌" in call_text

    @pytest.mark.asyncio
    async def test_market_command_generic_error(self, mock_update, mock_context):
        """Test /market with generic error."""
        mock_context.args = ["BTC", "buy", "100"]

        with patch('src.bot.handlers.trading.convert_usd_to_coin') as mock_convert:
            mock_convert.side_effect = Exception("API error")

            await trading.market_command(mock_update, mock_context)

        # Should handle error
        mock_update.message.reply_text.assert_called()


class TestMarketCallback:
    """Test market order callback handler."""

    @pytest.fixture
    def mock_update(self):
        """Create mock Update with callback query."""
        # Use builder for callback query - data will be set in individual tests
        return UpdateBuilder().with_callback_query("").with_user(1383283890).build()

    @pytest.fixture
    def mock_context(self):
        """Create mock Context."""
        return ContextBuilder().build()

    @pytest.mark.asyncio
    async def test_market_callback_cancel(self, mock_update, mock_context):
        """Test market callback with cancel."""
        mock_update.callback_query.data = "market_cancel"

        await trading.market_callback(mock_update, mock_context)

        # Should show cancelled
        mock_update.callback_query.answer.assert_called_once()
        mock_update.callback_query.edit_message_text.assert_called_once()
        call_text = mock_update.callback_query.edit_message_text.call_args[0][0]
        assert "cancelled" in call_text.lower()

    @pytest.mark.asyncio
    async def test_market_callback_buy_success(self, mock_update, mock_context):
        """Test market callback buy confirmation."""
        mock_update.callback_query.data = "market_confirm:BTC:buy:0.001"
        mock_result = {
            "status": "success"
        }

        with patch('src.bot.handlers.trading.order_service') as mock_service:
            with patch('src.bot.handlers.trading.convert_coin_to_usd') as mock_convert:
                mock_service.place_market_order.return_value = mock_result
                mock_convert.return_value = (100.0, 100000.0)

                await trading.market_callback(mock_update, mock_context)

        # Should show success
        assert mock_update.callback_query.edit_message_text.call_count == 2  # Processing + success
        final_call_text = mock_update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "✅" in final_call_text or "Market Order Placed" in final_call_text
        assert "BTC" in final_call_text
        assert "BUY" in final_call_text

    @pytest.mark.asyncio
    async def test_market_callback_sell_success(self, mock_update, mock_context):
        """Test market callback sell confirmation."""
        mock_update.callback_query.data = "market_confirm:ETH:sell:0.05"
        mock_result = {
            "status": "success"
        }

        with patch('src.bot.handlers.trading.order_service') as mock_service:
            with patch('src.bot.handlers.trading.convert_coin_to_usd') as mock_convert:
                mock_service.place_market_order.return_value = mock_result
                mock_convert.return_value = (200.0, 4000.0)

                await trading.market_callback(mock_update, mock_context)

        # Should show success
        assert mock_update.callback_query.edit_message_text.call_count == 2
        final_call_text = mock_update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "🔴" in final_call_text or "Market Order Placed" in final_call_text
        assert "ETH" in final_call_text
        assert "SELL" in final_call_text

    @pytest.mark.asyncio
    async def test_market_callback_error(self, mock_update, mock_context):
        """Test market callback with error."""
        mock_update.callback_query.data = "market_confirm:SOL:buy:5.0"

        with patch('src.bot.handlers.trading.order_service') as mock_service:
            mock_service.place_market_order.side_effect = Exception("Order failed")

            await trading.market_callback(mock_update, mock_context)

        # Should show error
        assert mock_update.callback_query.edit_message_text.call_count == 2  # Processing + error
        final_call_text = mock_update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "❌" in final_call_text or "Failed" in final_call_text
