"""Tests for the /close command handler."""

from unittest.mock import AsyncMock, patch

import pytest

from src.bot.handlers import wizard_close_position as close_handlers
from src.use_cases.trading.close_position import ClosePositionResponse
from tests.helpers import PositionBuilder, TelegramMockFactory


@pytest.mark.asyncio
async def test_close_command_no_args_no_positions():
    """When no positions exist, the command should inform the user."""
    update = TelegramMockFactory.create_command_update("/close")
    context = TelegramMockFactory.create_context()
    context.args = []

    with patch(
        "src.bot.handlers.wizard_close_position.position_service.list_positions",
        return_value=[],
    ):
        await close_handlers.close_command(update, context)

    update.message.reply_text.assert_called_once()
    message = update.message.reply_text.call_args[0][0]
    assert "No open positions" in message


@pytest.mark.asyncio
async def test_close_command_no_args_with_positions():
    """When positions exist, the command should show selection menu."""
    update = TelegramMockFactory.create_command_update("/close")
    context = TelegramMockFactory.create_context()
    context.args = []

    btc_position = PositionBuilder().with_coin("BTC").with_size(0.5).with_pnl(100.0).build()

    with patch(
        "src.bot.handlers.wizard_close_position.position_service.list_positions",
        return_value=[btc_position],
    ):
        await close_handlers.close_command(update, context)

    update.message.reply_text.assert_called_once()
    kwargs = update.message.reply_text.call_args.kwargs
    assert "reply_markup" in kwargs
    assert kwargs["reply_markup"] is not None


@pytest.mark.asyncio
async def test_close_command_executes_full_close():
    """Test closing a position directly via /close <coin>."""
    update = TelegramMockFactory.create_command_update("/close BTC")
    context = TelegramMockFactory.create_context()
    context.args = ["BTC"]

    response = ClosePositionResponse(
        status="success",
        coin="BTC",
        size_closed=0.25,
        usd_value=5000.0,
        remaining_size=0.0,
        close_type="full",
        message="Position closed successfully",
    )

    with patch(
        "src.bot.handlers.wizard_close_position.close_position_use_case.execute",
        AsyncMock(return_value=response),
    ):
        await close_handlers.close_command(update, context)

    update.message.reply_text.assert_called_once()
    message = update.message.reply_text.call_args[0][0]
    assert "BTC" in message
    assert "Remaining" in message


@pytest.mark.asyncio
async def test_close_command_invalid_amount():
    """Invalid amount strings should produce guidance instead of execution."""
    update = TelegramMockFactory.create_command_update("/close BTC abc")
    context = TelegramMockFactory.create_context()
    context.args = ["BTC", "abc"]

    await close_handlers.close_command(update, context)

    update.message.reply_text.assert_called_once()
    message = update.message.reply_text.call_args[0][0]
    assert "Invalid amount" in message
