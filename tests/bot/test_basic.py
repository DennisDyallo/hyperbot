"""
Unit tests for basic bot command handlers.

Tests all command handlers and menu callbacks in bot/handlers/basic.py.

REFACTORED: Now using tests/helpers for cleaner Telegram mocking and data creation.
- TelegramMockFactory replaces all manual Mock() creation
- PositionBuilder replaces manual nested dictionaries
- Result: ~100 fewer lines, more maintainable tests
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.bot.handlers import basic

# Import helpers for cleaner test code
from tests.helpers import TelegramMockFactory, PositionBuilder


@pytest.fixture
def authorized_user_id():
    """Authorized user ID."""
    return 1383283890


@pytest.fixture
def unauthorized_user_id():
    """Unauthorized user ID."""
    return 999999999


class TestStartCommand:
    """Test /start command handler."""

    @pytest.mark.asyncio
    async def test_start_authorized_user(self, authorized_user_id):
        """Test /start for authorized user shows welcome with menu."""
        update = TelegramMockFactory.create_command_update(
            "/start", user_id=authorized_user_id
        )
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.basic.settings.TELEGRAM_AUTHORIZED_USERS', [authorized_user_id]):
            await basic.start(update, context)

        # Should show welcome message with menu
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Welcome" in message_text
        assert "authorized" in message_text
        # Should have reply_markup (menu)
        assert "reply_markup" in call_args[1]

    @pytest.mark.asyncio
    async def test_start_unauthorized_user(self, unauthorized_user_id, authorized_user_id):
        """Test /start for unauthorized user shows rejection."""
        update = TelegramMockFactory.create_command_update(
            "/start", user_id=unauthorized_user_id
        )
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.basic.settings.TELEGRAM_AUTHORIZED_USERS', [authorized_user_id]):
            await basic.start(update, context)

        # Should show rejection message
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "not authorized" in message_text
        assert str(unauthorized_user_id) in message_text


class TestHelpCommand:
    """Test /help command handler."""

    @pytest.mark.asyncio
    async def test_help_command_shows_commands(self):
        """Test /help shows list of available commands."""
        update = TelegramMockFactory.create_command_update("/help")
        context = TelegramMockFactory.create_context()

        await basic.help_command(update, context)

        # Should show help text with commands
        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Available Commands" in message_text or "📚" in message_text
        assert "/account" in message_text
        assert "/positions" in message_text
        assert "/help" in message_text


class TestAccountCommand:
    """Test /account command handler."""

    @pytest.mark.asyncio
    async def test_account_command_success(self):
        """Test /account displays account summary successfully."""
        # Create update with message that returns a mock for editing
        update = TelegramMockFactory.create_command_update("/account")
        mock_msg = Mock()
        mock_msg.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=mock_msg)
        context = TelegramMockFactory.create_context()

        mock_summary = {
            'total_account_value': 10000.0,
            'perps_account_value': 8000.0,
            'spot_account_value': 2000.0,
            'available_balance': 5000.0,
            'margin_used': 3000.0,
            'num_perp_positions': 3,
            'num_spot_balances': 2,
            'total_unrealized_pnl': 150.50,
            'cross_margin_ratio_pct': 25.5,
            'cross_maintenance_margin': 500.0,
            'cross_account_leverage': 2.5,
            'is_testnet': True
        }

        with patch('src.bot.handlers.basic.account_service') as mock_service:
            mock_service.get_account_summary.return_value = mock_summary

            await basic.account_command(update, context)

        # Should show loading then account summary
        assert update.message.reply_text.call_count == 1
        mock_msg.edit_text.assert_called_once()

        # Verify summary contains key data
        call_text = mock_msg.edit_text.call_args[0][0]
        assert "Account Summary" in call_text or "💰" in call_text
        assert "10000" in call_text or "10,000" in call_text  # Total value
        assert "150" in call_text  # PnL

    @pytest.mark.asyncio
    async def test_account_command_error(self):
        """Test /account handles errors gracefully."""
        update = TelegramMockFactory.create_command_update("/account")
        mock_msg = Mock()
        mock_msg.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=mock_msg)
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.basic.account_service') as mock_service:
            mock_service.get_account_summary.side_effect = Exception("API error")

            await basic.account_command(update, context)

        # Should show error message
        assert update.message.reply_text.call_count >= 1


class TestPositionsCommand:
    """Test /positions command handler."""

    @pytest.mark.asyncio
    async def test_positions_command_with_positions(self):
        """Test /positions displays position list."""
        update = TelegramMockFactory.create_command_update("/positions")
        mock_msg = Mock()
        mock_msg.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=mock_msg)
        context = TelegramMockFactory.create_context()

        # Use PositionBuilder for cleaner data creation
        btc_pos = PositionBuilder()         \
            .with_coin("BTC")               \
            .with_size(0.5)                 \
            .with_entry_price(100000.0)     \
            .with_position_value(50000.0)   \
            .with_pnl(1000.0)               \
            .with_leverage(3)               \
            .build()

        eth_pos = PositionBuilder()         \
            .with_coin("ETH")               \
            .with_size(-10.0)               \
            .with_entry_price(4000.0)       \
            .with_position_value(40000.0)   \
            .with_pnl(-500.0)               \
            .with_leverage(2)               \
            .build()

        with patch('src.bot.handlers.basic.position_service') as mock_service:
            mock_service.list_positions.return_value = [btc_pos, eth_pos]

            await basic.positions_command(update, context)

        # Should show positions
        mock_msg.edit_text.assert_called_once()
        call_text = mock_msg.edit_text.call_args[0][0]
        assert "BTC" in call_text
        assert "ETH" in call_text
        assert "LONG" in call_text
        assert "SHORT" in call_text

    @pytest.mark.asyncio
    async def test_positions_command_empty(self):
        """Test /positions with no positions."""
        update = TelegramMockFactory.create_command_update("/positions")
        mock_msg = Mock()
        mock_msg.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=mock_msg)
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.basic.position_service') as mock_service:
            mock_service.list_positions.return_value = []

            await basic.positions_command(update, context)

        # Should show empty message
        mock_msg.edit_text.assert_called_once()
        call_text = mock_msg.edit_text.call_args[0][0]
        assert "No open positions" in call_text or "📭" in call_text

    @pytest.mark.asyncio
    async def test_positions_command_error(self):
        """Test /positions handles errors."""
        update = TelegramMockFactory.create_command_update("/positions")
        mock_msg = Mock()
        mock_msg.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=mock_msg)
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.basic.position_service') as mock_service:
            mock_service.list_positions.side_effect = Exception("API error")

            await basic.positions_command(update, context)

        # Should handle error (may show loading message first)
        assert update.message.reply_text.call_count >= 1


class TestStatusCommand:
    """Test /status command handler."""

    @pytest.mark.asyncio
    async def test_status_command(self):
        """Test /status shows bot status."""
        update = TelegramMockFactory.create_command_update("/status")
        context = TelegramMockFactory.create_context()

        await basic.status_command(update, context)

        # Should show status
        update.message.reply_text.assert_called_once()
        call_text = update.message.reply_text.call_args[0][0]
        assert "Bot Status" in call_text or "🤖" in call_text
        assert "Online" in call_text or "✅" in call_text


class TestMenuMainCallback:
    """Test menu_main_callback handler."""

    @pytest.mark.asyncio
    async def test_menu_main_callback(self):
        """Test main menu callback."""
        update = TelegramMockFactory.create_callback_update("menu_main")
        context = TelegramMockFactory.create_context()

        await basic.menu_main_callback(update, context)

        # Should answer and show main menu
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_args = update.callback_query.edit_message_text.call_args
        message_text = call_args[0][0]
        assert "Main Menu" in message_text or "🏠" in message_text
        # Should have reply_markup
        assert "reply_markup" in call_args[1]


class TestMenuAccountCallback:
    """Test menu_account_callback handler."""

    @pytest.mark.asyncio
    async def test_menu_account_success(self):
        """Test account menu callback success."""
        update = TelegramMockFactory.create_callback_update("menu_account")
        context = TelegramMockFactory.create_context()

        mock_summary = {
            'total_account_value': 10000.0,
            'perps_account_value': 8000.0,
            'spot_account_value': 2000.0,
            'available_balance': 5000.0,
            'margin_used': 3000.0,
            'num_perp_positions': 3,
            'num_spot_balances': 2,
            'total_unrealized_pnl': 150.50,
            'cross_margin_ratio_pct': 25.5,
            'cross_account_leverage': 2.5
        }

        with patch('src.bot.handlers.basic.account_service') as mock_service:
            mock_service.get_account_summary.return_value = mock_summary

            await basic.menu_account_callback(update, context)

        # Should show loading then account
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "Account Summary" in final_call_text or "💰" in final_call_text

    @pytest.mark.asyncio
    async def test_menu_account_error(self):
        """Test account menu callback error handling."""
        update = TelegramMockFactory.create_callback_update("menu_account")
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.basic.account_service') as mock_service:
            mock_service.get_account_summary.side_effect = Exception("API error")

            await basic.menu_account_callback(update, context)

        # Should show error
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "❌" in final_call_text or "Failed" in final_call_text


class TestMenuPositionsCallback:
    """Test menu_positions_callback handler."""

    @pytest.mark.asyncio
    async def test_menu_positions_with_positions(self):
        """Test positions menu with positions."""
        update = TelegramMockFactory.create_callback_update("menu_positions")
        context = TelegramMockFactory.create_context()

        # Use PositionBuilder for clean data creation
        sol_pos = PositionBuilder()         \
            .with_coin("SOL")               \
            .with_size(10.0)                \
            .with_entry_price(150.0)        \
            .with_position_value(1500.0)    \
            .with_pnl(50.0)                 \
            .with_leverage(5)               \
            .build()

        with patch('src.bot.handlers.basic.position_service') as mock_service:
            mock_service.list_positions.return_value = [sol_pos]

            await basic.menu_positions_callback(update, context)

        # Should show positions
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "SOL" in final_call_text
        assert "LONG" in final_call_text

    @pytest.mark.asyncio
    async def test_menu_positions_empty(self):
        """Test positions menu with no positions."""
        update = TelegramMockFactory.create_callback_update("menu_positions")
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.basic.position_service') as mock_service:
            mock_service.list_positions.return_value = []

            await basic.menu_positions_callback(update, context)

        # Should show empty message
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "No open positions" in final_call_text or "📭" in final_call_text

    @pytest.mark.asyncio
    async def test_menu_positions_error(self):
        """Test positions menu error handling."""
        update = TelegramMockFactory.create_callback_update("menu_positions")
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.basic.position_service') as mock_service:
            mock_service.list_positions.side_effect = Exception("API error")

            await basic.menu_positions_callback(update, context)

        # Should show error
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "❌" in final_call_text or "Failed" in final_call_text


class TestMenuHelpCallback:
    """Test menu_help_callback handler."""

    @pytest.mark.asyncio
    async def test_menu_help_callback(self):
        """Test help menu callback."""
        update = TelegramMockFactory.create_callback_update("menu_help")
        context = TelegramMockFactory.create_context()

        await basic.menu_help_callback(update, context)

        # Should show help
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_text = update.callback_query.edit_message_text.call_args[0][0]
        assert "Help" in call_text or "📚" in call_text


class TestMenuStatusCallback:
    """Test menu_status_callback handler."""

    @pytest.mark.asyncio
    async def test_menu_status_callback(self):
        """Test status menu callback."""
        update = TelegramMockFactory.create_callback_update("menu_status")
        context = TelegramMockFactory.create_context()

        await basic.menu_status_callback(update, context)

        # Should show status
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_text = update.callback_query.edit_message_text.call_args[0][0]
        assert "Status" in call_text or "🤖" in call_text
        assert "Online" in call_text or "✅" in call_text


class TestMenuCloseCallback:
    """Test menu_close_callback handler."""

    @pytest.mark.asyncio
    async def test_menu_close_with_positions(self):
        """Test close menu with positions."""
        update = TelegramMockFactory.create_callback_update("menu_close")
        context = TelegramMockFactory.create_context()

        # Use PositionBuilder for clean data
        btc_pos = PositionBuilder().with_coin("BTC").with_size(0.1).with_pnl(100.0).build()

        with patch('src.bot.handlers.basic.position_service') as mock_service:
            mock_service.list_positions.return_value = [btc_pos]

            await basic.menu_close_callback(update, context)

        # Should show close menu
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "Close Position" in final_call_text or "🎯" in final_call_text

    @pytest.mark.asyncio
    async def test_menu_close_empty(self):
        """Test close menu with no positions."""
        update = TelegramMockFactory.create_callback_update("menu_close")
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.basic.position_service') as mock_service:
            mock_service.list_positions.return_value = []

            await basic.menu_close_callback(update, context)

        # Should show no positions message
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "No open positions" in final_call_text or "📭" in final_call_text

    @pytest.mark.asyncio
    async def test_menu_close_error(self):
        """Test close menu error handling."""
        update = TelegramMockFactory.create_callback_update("menu_close")
        context = TelegramMockFactory.create_context()

        with patch('src.bot.handlers.basic.position_service') as mock_service:
            mock_service.list_positions.side_effect = Exception("API error")

            await basic.menu_close_callback(update, context)

        # Should show error
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "❌" in final_call_text or "Failed" in final_call_text


class TestMenuRebalanceCallback:
    """Test menu_rebalance_callback handler."""

    @pytest.mark.asyncio
    async def test_menu_rebalance_callback_delegates(self):
        """Test rebalance menu delegates to rebalance command."""
        update = TelegramMockFactory.create_callback_update("menu_rebalance")
        context = TelegramMockFactory.create_context()

        # rebalance_command is imported inside the function from advanced module
        with patch('src.bot.handlers.advanced.rebalance_command', new_callable=AsyncMock) as mock_rebalance:
            await basic.menu_rebalance_callback(update, context)

            # Should answer callback and delegate
            update.callback_query.answer.assert_called_once()
            mock_rebalance.assert_called_once_with(update, context)


class TestMenuScaleCallback:
    """Test menu_scale_callback handler."""

    @pytest.mark.asyncio
    async def test_menu_scale_callback_shows_info(self):
        """Test scale menu shows info about scale orders."""
        update = TelegramMockFactory.create_callback_update("menu_scale")
        context = TelegramMockFactory.create_context()

        await basic.menu_scale_callback(update, context)

        # Should show scale order info
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_text = update.callback_query.edit_message_text.call_args[0][0]
        assert "Scale Order" in call_text or "📊" in call_text
        assert "/scale" in call_text
