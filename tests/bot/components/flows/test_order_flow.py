"""Tests for order flow orchestrator."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import InlineKeyboardMarkup

from src.bot.components.flows.order_flow import OrderFlowOrchestrator, OrderFlowState


class TestOrderFlowState:
    """Test OrderFlowState dataclass."""

    def test_initial_state(self) -> None:
        """Test initial state values."""
        state = OrderFlowState()

        assert state.coin is None
        assert state.side is None
        assert state.amount_usd is None
        assert state.leverage is None
        assert state.preview_mode == "quick"

    def test_state_updates(self) -> None:
        """Test updating state values."""
        state = OrderFlowState()

        state.coin = "BTC"
        state.side = "buy"
        state.amount_usd = 1000.0
        state.leverage = 5

        assert state.coin == "BTC"
        assert state.side == "buy"
        assert state.amount_usd == 1000.0
        assert state.leverage == 5


class TestOrderFlowOrchestrator:
    """Test OrderFlowOrchestrator."""

    def test_initialization(self) -> None:
        """Test orchestrator initialization."""
        flow = OrderFlowOrchestrator()

        assert isinstance(flow.state, OrderFlowState)
        assert flow.state.coin is None

    @pytest.mark.asyncio
    async def test_step_2_side_selection(self) -> None:
        """Test side selection step."""
        flow = OrderFlowOrchestrator()

        # Mock update and query
        update = MagicMock()
        query = AsyncMock()
        update.callback_query = query
        context = MagicMock()

        await flow.step_2_side_selection(update, context, "BTC")

        # Check state updated
        assert flow.state.coin == "BTC"

        # Check message sent
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "BTC" in call_args[0][0]
        assert "Buy or Sell" in call_args[0][0]
        assert isinstance(call_args[1]["reply_markup"], InlineKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_step_3_amount_entry(self) -> None:
        """Test amount entry step."""
        flow = OrderFlowOrchestrator()
        flow.state.coin = "BTC"

        update = MagicMock()
        query = AsyncMock()
        update.callback_query = query
        context = MagicMock()

        await flow.step_3_amount_entry(update, context, "buy")

        # Check state updated
        assert flow.state.side == "buy"

        # Check message sent
        query.edit_message_text.assert_called_once()
        call_args = query.edit_message_text.call_args
        assert "BTC" in call_args[0][0]
        assert "BUY" in call_args[0][0]
        assert "Enter amount" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_step_4_leverage_selection(self) -> None:
        """Test leverage selection step."""
        flow = OrderFlowOrchestrator()
        flow.state.coin = "BTC"
        flow.state.side = "buy"

        update = MagicMock()
        query = AsyncMock()
        update.callback_query = query
        context = MagicMock()

        await flow.step_4_leverage_selection(update, context, 1000.0, 5200.0)

        # Check state updated
        assert flow.state.amount_usd == 1000.0

        # Check message sent (2 calls: loading + actual)
        assert query.edit_message_text.call_count == 2
        call_args = query.edit_message_text.call_args
        assert "Select Leverage" in call_args[0][0]
        assert "1x" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_step_5_preview_quick_mode(self) -> None:
        """Test preview in quick mode."""
        flow = OrderFlowOrchestrator()
        flow.state.coin = "BTC"
        flow.state.side = "buy"
        flow.state.amount_usd = 1000.0
        flow.state.preview_mode = "quick"

        update = MagicMock()
        query = AsyncMock()
        update.callback_query = query
        context = MagicMock()

        await flow.step_5_preview(
            update,
            context,
            leverage=5,
            entry_price=98500.0,
            liquidation_price=78800.0,
            margin_available=5200.0,
        )

        # Check state updated
        assert flow.state.leverage == 5

        # Check preview displayed
        assert query.edit_message_text.call_count == 2  # loading + preview
        call_args = query.edit_message_text.call_args
        assert "Order Preview" in call_args[0][0] or "BTC" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_step_5_preview_full_mode(self) -> None:
        """Test preview in full mode."""
        flow = OrderFlowOrchestrator()
        flow.state.coin = "BTC"
        flow.state.side = "buy"
        flow.state.amount_usd = 1000.0
        flow.state.preview_mode = "full"

        update = MagicMock()
        query = AsyncMock()
        update.callback_query = query
        context = MagicMock()

        await flow.step_5_preview(
            update,
            context,
            leverage=5,
            entry_price=98500.0,
            liquidation_price=78800.0,
            margin_available=5200.0,
        )

        # Check full preview displayed
        call_args = query.edit_message_text.call_args
        # Full preview has more content
        message_text = call_args[0][0]
        assert "BTC" in message_text

    @pytest.mark.asyncio
    async def test_step_6_execute(self) -> None:
        """Test order execution step."""
        flow = OrderFlowOrchestrator()
        flow.state.coin = "BTC"
        flow.state.side = "buy"
        flow.state.amount_usd = 1000.0
        flow.state.leverage = 5

        update = MagicMock()
        query = AsyncMock()
        update.callback_query = query
        context = MagicMock()

        execution_result = {"liquidation_distance_pct": 20.0, "avg_fill_price": 98500.0}

        await flow.step_6_execute(update, context, execution_result)

        # Check success message displayed
        assert query.edit_message_text.call_count == 2  # loading + success
        call_args = query.edit_message_text.call_args
        assert "Order Executed" in call_args[0][0]
        assert "BTC" in call_args[0][0]

    def test_toggle_preview_mode(self) -> None:
        """Test toggling preview mode."""
        flow = OrderFlowOrchestrator()

        assert flow.state.preview_mode == "quick"

        flow.toggle_preview_mode()
        assert flow.state.preview_mode == "full"

        flow.toggle_preview_mode()
        assert flow.state.preview_mode == "quick"

    def test_build_preview_data_incomplete_state(self) -> None:
        """Test preview data building with incomplete state."""
        flow = OrderFlowOrchestrator()

        with pytest.raises(ValueError, match="Incomplete order state"):
            flow._build_preview_data(
                entry_price=98500.0, liquidation_price=78800.0, margin_available=5200.0
            )

    def test_build_preview_data_complete_state(self) -> None:
        """Test preview data building with complete state."""
        flow = OrderFlowOrchestrator()
        flow.state.coin = "BTC"
        flow.state.side = "buy"
        flow.state.amount_usd = 1000.0
        flow.state.leverage = 5

        preview_data = flow._build_preview_data(
            entry_price=98500.0, liquidation_price=78800.0, margin_available=5200.0
        )

        assert preview_data.coin == "BTC"
        assert preview_data.side == "buy"
        assert preview_data.amount_usd == 1000.0
        assert preview_data.leverage == 5
        assert preview_data.entry_price == 98500.0
        assert preview_data.liquidation_price == 78800.0

    def test_build_preview_data_with_warnings(self) -> None:
        """Test preview data includes warnings for high risk."""
        flow = OrderFlowOrchestrator()
        flow.state.coin = "BTC"
        flow.state.side = "buy"
        flow.state.amount_usd = 1000.0
        flow.state.leverage = 20  # High leverage

        preview_data = flow._build_preview_data(
            entry_price=98500.0,
            liquidation_price=97000.0,  # Very close liquidation
            margin_available=5200.0,
        )

        # Should have risk warning
        assert len(preview_data.warnings) > 0
        assert any("risk" in w.lower() for w in preview_data.warnings)

    def test_build_preview_data_high_buying_power_usage(self) -> None:
        """Test preview data warns on high buying power usage."""
        flow = OrderFlowOrchestrator()
        flow.state.coin = "BTC"
        flow.state.side = "buy"
        flow.state.amount_usd = 3000.0  # High amount
        flow.state.leverage = 5

        preview_data = flow._build_preview_data(
            entry_price=98500.0,
            liquidation_price=78800.0,
            margin_available=1000.0,  # Low margin available
        )

        # Should have buying power warning
        assert len(preview_data.warnings) > 0
        assert any("buying power" in w.lower() for w in preview_data.warnings)

    def test_build_success_message(self) -> None:
        """Test success message building."""
        flow = OrderFlowOrchestrator()
        flow.state.coin = "BTC"
        flow.state.side = "buy"
        flow.state.amount_usd = 1000.0
        flow.state.leverage = 5

        execution_result = {"liquidation_distance_pct": 20.0, "avg_fill_price": 98500.0}

        message = flow._build_success_message(execution_result)

        assert "Order Executed" in message
        assert "BTC" in message
        assert "5x" in message
        assert "BUY" in message
