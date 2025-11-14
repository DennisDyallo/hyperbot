"""
Unit tests for advanced command handlers (rebalancing).

Tests /rebalance command and callbacks in bot/handlers/commands.py.

REFACTORED: Now using tests/helpers for cleaner Telegram mocking.
- TelegramMockFactory replaces all manual Mock() creation for Update/Context
- Result: ~50 fewer lines, more maintainable tests
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.bot.handlers import wizard_rebalance as rebalance_module

# Import helpers for cleaner test code
from tests.helpers import TelegramMockFactory


@pytest.fixture
def authorized_user_id():
    """Authorized user ID."""
    return 1383283890


class TestRebalanceCommand:
    """Test /rebalance command handler."""

    @pytest.mark.asyncio
    async def test_rebalance_command_with_positions(self):
        """Test /rebalance with open positions."""
        update = TelegramMockFactory.create_command_update("/rebalance")
        mock_msg = Mock()
        mock_msg.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=mock_msg)
        context = TelegramMockFactory.create_context()

        mock_positions = [
            {"position": {"coin": "BTC", "position_value": 10000.0}},
            {"position": {"coin": "ETH", "position_value": 5000.0}},
        ]

        with patch("src.bot.handlers.wizard_rebalance.position_service") as mock_service:
            mock_service.list_positions.return_value = mock_positions

            await rebalance_module.rebalance_command(update, context)

        # Should show portfolio and options
        mock_msg.edit_text.assert_called_once()
        call_text = mock_msg.edit_text.call_args[0][0]
        assert "Current Portfolio" in call_text or "📊" in call_text
        assert "BTC" in call_text
        assert "ETH" in call_text
        # Should have reply_markup with rebalance options
        assert "reply_markup" in mock_msg.edit_text.call_args[1]

    @pytest.mark.asyncio
    async def test_rebalance_command_no_positions(self):
        """Test /rebalance with no positions."""
        update = TelegramMockFactory.create_command_update("/rebalance")
        mock_msg = Mock()
        mock_msg.edit_text = AsyncMock()
        update.message.reply_text = AsyncMock(return_value=mock_msg)
        context = TelegramMockFactory.create_context()

        with patch("src.bot.handlers.wizard_rebalance.position_service") as mock_service:
            mock_service.list_positions.return_value = []

            await rebalance_module.rebalance_command(update, context)

        # Should show no positions message
        mock_msg.edit_text.assert_called_once()
        call_text = mock_msg.edit_text.call_args[0][0]
        assert "No open positions" in call_text or "📭" in call_text

    @pytest.mark.asyncio
    async def test_rebalance_command_via_callback(self):
        """Test /rebalance via callback query (from menu)."""
        update = TelegramMockFactory.create_callback_update("menu_rebalance")
        context = TelegramMockFactory.create_context()

        mock_positions = [{"position": {"coin": "SOL", "position_value": 1000.0}}]

        with patch("src.bot.handlers.wizard_rebalance.position_service") as mock_service:
            mock_service.list_positions.return_value = mock_positions

            await rebalance_module.rebalance_command(update, context)

        # Should handle callback query
        update.callback_query.answer.assert_called_once()
        assert update.callback_query.edit_message_text.call_count >= 1

    @pytest.mark.asyncio
    async def test_rebalance_command_error(self):
        """Test /rebalance with error."""
        update = TelegramMockFactory.create_command_update("/rebalance")
        context = TelegramMockFactory.create_context()

        with patch("src.bot.handlers.wizard_rebalance.position_service") as mock_service:
            mock_service.list_positions.side_effect = Exception("API error")

            await rebalance_module.rebalance_command(update, context)

        # Should handle error
        update.message.reply_text.assert_called()


class TestRebalancePreviewCallback:
    """Test rebalance preview callback handler."""

    @pytest.mark.asyncio
    async def test_rebalance_preview_cancel(self):
        """Test rebalance preview cancel."""
        update = TelegramMockFactory.create_callback_update("rebalance_cancel")
        context = TelegramMockFactory.create_context()

        await rebalance_module.rebalance_preview_callback(update, context)

        # Should show cancelled message
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_text = update.callback_query.edit_message_text.call_args[0][0]
        assert "cancelled" in call_text.lower()

    @pytest.mark.asyncio
    async def test_rebalance_preview_custom(self):
        """Test rebalance preview custom weights."""
        update = TelegramMockFactory.create_callback_update("rebalance_custom")
        context = TelegramMockFactory.create_context()

        await rebalance_module.rebalance_preview_callback(update, context)

        # Should show not implemented message
        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        call_text = update.callback_query.edit_message_text.call_args[0][0]
        assert "Custom" in call_text or "not yet implemented" in call_text

    @pytest.mark.asyncio
    async def test_rebalance_preview_equal_weight_with_trades(self):
        """Test rebalance preview with equal weight strategy."""
        update = TelegramMockFactory.create_callback_update("rebalance_preview:equal")
        context = TelegramMockFactory.create_context()

        mock_positions = [{"position": {"coin": "BTC"}}, {"position": {"coin": "ETH"}}]

        # Mock preview result with planned trades
        from src.services.rebalance_service import (
            RebalanceResult,
            RebalanceTrade,
            TradeAction,
        )

        mock_trades = [
            RebalanceTrade(
                coin="BTC",
                action=TradeAction.INCREASE,
                current_allocation_pct=33.3,
                target_allocation_pct=50.0,
                diff_pct=16.7,
                current_usd_value=5000.0,
                target_usd_value=7500.0,
                trade_usd_value=2500.0,
                trade_size=0.025,
                target_leverage=3,
            ),
            RebalanceTrade(
                coin="ETH",
                action=TradeAction.DECREASE,
                current_allocation_pct=66.7,
                target_allocation_pct=50.0,
                diff_pct=-16.7,
                current_usd_value=10000.0,
                target_usd_value=7500.0,
                trade_usd_value=-2500.0,
                trade_size=-0.625,
                target_leverage=3,
            ),
        ]
        mock_preview = RebalanceResult(
            success=True,
            message="Preview generated",
            planned_trades=mock_trades,
            executed_trades=0,
            successful_trades=0,
            failed_trades=0,
            skipped_trades=0,
            initial_allocation={"BTC": 33.3, "ETH": 66.7},
            final_allocation={"BTC": 50.0, "ETH": 50.0},
            errors=[],
            risk_warnings=[],
        )

        with (
            patch("src.bot.handlers.wizard_rebalance.position_service") as mock_pos_service,
            patch("src.bot.handlers.wizard_rebalance.rebalance_service") as mock_rebal_service,
        ):
            mock_pos_service.list_positions.return_value = mock_positions
            mock_rebal_service.preview_rebalance.return_value = mock_preview

            await rebalance_module.rebalance_preview_callback(update, context)

        # Should show preview with trades
        assert update.callback_query.edit_message_text.call_count == 2  # Processing + preview
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "Rebalance Preview" in final_call_text or "📊" in final_call_text
        assert "Required Trades" in final_call_text
        # Should have confirmation buttons
        assert "reply_markup" in update.callback_query.edit_message_text.call_args_list[1][1]

    @pytest.mark.asyncio
    async def test_rebalance_preview_already_balanced(self):
        """Test rebalance preview when portfolio is already balanced."""
        update = TelegramMockFactory.create_callback_update("rebalance_preview:equal")
        context = TelegramMockFactory.create_context()

        mock_positions = [{"position": {"coin": "BTC"}}, {"position": {"coin": "ETH"}}]

        # Mock preview with all SKIP trades
        from src.services.rebalance_service import (
            RebalanceResult,
            RebalanceTrade,
            TradeAction,
        )

        mock_trades = [
            RebalanceTrade(
                coin="BTC",
                action=TradeAction.SKIP,
                current_allocation_pct=50.0,
                target_allocation_pct=50.0,
                diff_pct=0.0,
                current_usd_value=7500.0,
                target_usd_value=7500.0,
                trade_usd_value=0.0,
                trade_size=0.0,
                target_leverage=3,
            )
        ]
        mock_preview = RebalanceResult(
            success=True,
            message="Already balanced",
            planned_trades=mock_trades,
            executed_trades=0,
            successful_trades=0,
            failed_trades=0,
            skipped_trades=1,
            initial_allocation={"BTC": 50.0},
            final_allocation={"BTC": 50.0},
            errors=[],
            risk_warnings=[],
        )

        with (
            patch("src.bot.handlers.wizard_rebalance.position_service") as mock_pos_service,
            patch("src.bot.handlers.wizard_rebalance.rebalance_service") as mock_rebal_service,
        ):
            mock_pos_service.list_positions.return_value = mock_positions
            mock_rebal_service.preview_rebalance.return_value = mock_preview

            await rebalance_module.rebalance_preview_callback(update, context)

        # Should show already balanced message
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "already balanced" in final_call_text.lower() or "✅" in final_call_text

    @pytest.mark.asyncio
    async def test_rebalance_preview_error(self):
        """Test rebalance preview with error."""
        update = TelegramMockFactory.create_callback_update("rebalance_preview:equal")
        context = TelegramMockFactory.create_context()

        with patch("src.bot.handlers.wizard_rebalance.position_service") as mock_service:
            mock_service.list_positions.side_effect = Exception("API error")

            await rebalance_module.rebalance_preview_callback(update, context)

        # Should show error
        assert update.callback_query.edit_message_text.call_count == 2  # Processing + error
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "❌" in final_call_text or "Failed" in final_call_text


class TestRebalanceExecuteCallback:
    """Test rebalance execution callback handler."""

    @pytest.mark.asyncio
    async def test_rebalance_execute_success(self):
        """Test successful rebalance execution."""
        update = TelegramMockFactory.create_callback_update("rebalance_execute:equal")
        context = TelegramMockFactory.create_context()

        mock_positions = [{"position": {"coin": "BTC"}}, {"position": {"coin": "ETH"}}]

        # Mock execution result
        from src.services.rebalance_service import RebalanceResult

        mock_result = RebalanceResult(
            success=True,
            message="Rebalance complete",
            planned_trades=[],
            executed_trades=2,
            successful_trades=2,
            failed_trades=0,
            skipped_trades=0,
            initial_allocation={"BTC": 40.0, "ETH": 60.0},
            final_allocation={"BTC": 50.0, "ETH": 50.0},
            errors=[],
            risk_warnings=[],
        )

        with (
            patch("src.bot.handlers.wizard_rebalance.position_service") as mock_pos_service,
            patch("src.bot.handlers.wizard_rebalance.rebalance_service") as mock_rebal_service,
        ):
            mock_pos_service.list_positions.return_value = mock_positions
            mock_rebal_service.execute_rebalance.return_value = mock_result

            await rebalance_module.rebalance_execute_callback(update, context)

        # Should show success
        assert update.callback_query.edit_message_text.call_count == 2  # Processing + result
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "✅" in final_call_text or "Rebalance Complete" in final_call_text
        assert "**Successful**: 2" in final_call_text

    @pytest.mark.asyncio
    async def test_rebalance_execute_partial_failure(self):
        """Test rebalance execution with some failures."""
        update = TelegramMockFactory.create_callback_update("rebalance_execute:equal")
        context = TelegramMockFactory.create_context()

        mock_positions = [
            {"position": {"coin": "BTC"}},
            {"position": {"coin": "ETH"}},
            {"position": {"coin": "SOL"}},
        ]

        # Mock result with failures
        from src.services.rebalance_service import RebalanceResult

        mock_result = RebalanceResult(
            success=True,
            message="Rebalance complete with failures",
            planned_trades=[],
            executed_trades=3,
            successful_trades=2,
            failed_trades=1,
            skipped_trades=0,
            initial_allocation={"BTC": 30.0, "ETH": 50.0, "SOL": 20.0},
            final_allocation={"BTC": 33.3, "ETH": 33.3, "SOL": 33.3},
            errors=["Failed to close SOL position"],
            risk_warnings=[],
        )

        with (
            patch("src.bot.handlers.wizard_rebalance.position_service") as mock_pos_service,
            patch("src.bot.handlers.wizard_rebalance.rebalance_service") as mock_rebal_service,
        ):
            mock_pos_service.list_positions.return_value = mock_positions
            mock_rebal_service.execute_rebalance.return_value = mock_result

            await rebalance_module.rebalance_execute_callback(update, context)

        # Should show warning about failures
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "**Failed**: 1" in final_call_text
        assert "⚠️" in final_call_text or "Some trades failed" in final_call_text

    @pytest.mark.asyncio
    async def test_rebalance_execute_complete_failure(self):
        """Test rebalance execution complete failure."""
        update = TelegramMockFactory.create_callback_update("rebalance_execute:equal")
        context = TelegramMockFactory.create_context()

        mock_positions = [{"position": {"coin": "BTC"}}]

        # Mock failed result
        from src.services.rebalance_service import RebalanceResult

        mock_result = RebalanceResult(
            success=False,
            message="Rebalance failed",
            planned_trades=[],
            executed_trades=0,
            successful_trades=0,
            failed_trades=0,
            skipped_trades=0,
            initial_allocation={"BTC": 100.0},
            final_allocation={"BTC": 100.0},
            errors=["Insufficient balance"],
            risk_warnings=[],
        )

        with (
            patch("src.bot.handlers.wizard_rebalance.position_service") as mock_pos_service,
            patch("src.bot.handlers.wizard_rebalance.rebalance_service") as mock_rebal_service,
        ):
            mock_pos_service.list_positions.return_value = mock_positions
            mock_rebal_service.execute_rebalance.return_value = mock_result

            await rebalance_module.rebalance_execute_callback(update, context)

        # Should show failure
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "❌" in final_call_text or "Rebalance Failed" in final_call_text

    @pytest.mark.asyncio
    async def test_rebalance_execute_error(self):
        """Test rebalance execution with exception."""
        update = TelegramMockFactory.create_callback_update("rebalance_execute:equal")
        context = TelegramMockFactory.create_context()

        with patch("src.bot.handlers.wizard_rebalance.position_service") as mock_service:
            mock_service.list_positions.side_effect = Exception("API error")

            await rebalance_module.rebalance_execute_callback(update, context)

        # Should show error
        assert update.callback_query.edit_message_text.call_count == 2
        final_call_text = update.callback_query.edit_message_text.call_args_list[1][0][0]
        assert "❌" in final_call_text or "failed" in final_call_text.lower()
