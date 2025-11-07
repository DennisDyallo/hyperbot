"""
Unit tests for Track Scale Order Use Cases.

Tests listing, status checking, and cancellation of scale orders.
CRITICAL - bugs here = inability to monitor/cancel trading operations.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.models.scale_order import ScaleOrder, ScaleOrderStatus
from src.use_cases.scale_orders.track import (
    CancelScaleOrderRequest,
    CancelScaleOrderUseCase,
    GetScaleOrderStatusRequest,
    GetScaleOrderStatusUseCase,
    ListScaleOrdersRequest,
    ListScaleOrdersUseCase,
)
from tests.helpers.service_mocks import create_service_with_mocks


class TestListScaleOrdersUseCase:
    """Test ListScaleOrdersUseCase."""

    @pytest.fixture
    def use_case(self):
        """Create ListScaleOrdersUseCase with mocked dependencies."""
        mock_scale_order = Mock()

        return create_service_with_mocks(
            ListScaleOrdersUseCase,
            "src.use_cases.scale_orders.track",
            {"scale_order_service": mock_scale_order},
        )

    @pytest.fixture
    def sample_scale_orders(self):
        """Sample scale orders."""
        return [
            ScaleOrder(
                id="scale_1",
                coin="BTC",
                is_buy=True,
                total_usd_amount=10000.0,
                total_coin_size=0.2,
                num_orders=5,
                start_price=50000.0,
                end_price=48000.0,
                distribution_type="linear",
                order_ids=[1001, 1002, 1003],
                orders_placed=5,
                orders_filled=2,
                status="active",
            ),
            ScaleOrder(
                id="scale_2",
                coin="ETH",
                is_buy=False,
                total_usd_amount=5000.0,
                total_coin_size=1.6,
                num_orders=3,
                start_price=3000.0,
                end_price=3300.0,
                distribution_type="linear",
                order_ids=[2001, 2002],
                orders_placed=3,
                orders_filled=1,
                status="active",
            ),
            ScaleOrder(
                id="scale_3",
                coin="BTC",
                is_buy=True,
                total_usd_amount=20000.0,
                total_coin_size=0.4,
                num_orders=10,
                start_price=51000.0,
                end_price=48000.0,
                distribution_type="geometric",
                order_ids=[],  # All filled/cancelled
                orders_placed=10,
                orders_filled=10,
                status="completed",
            ),
        ]

    # ===================================================================
    # List All Orders tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_list_all_scale_orders(self, use_case, sample_scale_orders):
        """Test listing all scale orders."""
        use_case.scale_order_service.list_scale_orders.return_value = sample_scale_orders

        request = ListScaleOrdersRequest(active_only=False)

        response = await use_case.execute(request)

        assert len(response.scale_orders) == 3
        assert response.total_count == 3
        assert response.active_count == 2  # scale_1 and scale_2 have order_ids

    @pytest.mark.asyncio
    async def test_list_active_only(self, use_case, sample_scale_orders):
        """Test listing only active scale orders."""
        use_case.scale_order_service.list_scale_orders.return_value = sample_scale_orders

        request = ListScaleOrdersRequest(active_only=True)

        response = await use_case.execute(request)

        # Should only return scale_1 and scale_2 (have open orders)
        assert len(response.scale_orders) == 2
        assert response.scale_orders[0].id == "scale_1"
        assert response.scale_orders[1].id == "scale_2"
        assert response.active_count == 2

    @pytest.mark.asyncio
    async def test_list_no_scale_orders(self, use_case):
        """Test listing when no scale orders exist."""
        use_case.scale_order_service.list_scale_orders.return_value = []

        request = ListScaleOrdersRequest()

        response = await use_case.execute(request)

        assert len(response.scale_orders) == 0
        assert response.total_count == 0
        assert response.active_count == 0

    # ===================================================================
    # Filter by Coin tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_list_filter_by_coin(self, use_case, sample_scale_orders):
        """Test filtering scale orders by coin."""
        use_case.scale_order_service.list_scale_orders.return_value = sample_scale_orders

        request = ListScaleOrdersRequest(coin="BTC", active_only=False)

        response = await use_case.execute(request)

        # Should only return BTC orders (scale_1 and scale_3)
        assert len(response.scale_orders) == 2
        assert all(o.coin == "BTC" for o in response.scale_orders)

    @pytest.mark.asyncio
    async def test_list_filter_coin_no_matches(self, use_case, sample_scale_orders):
        """Test filtering by coin with no matches."""
        use_case.scale_order_service.list_scale_orders.return_value = sample_scale_orders

        request = ListScaleOrdersRequest(coin="SOL", active_only=False)

        response = await use_case.execute(request)

        assert len(response.scale_orders) == 0
        assert response.total_count == 3  # Total unchanged

    # ===================================================================
    # Error Handling tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_list_service_failure_raises_runtime_error(self, use_case):
        """Test service failure raises RuntimeError."""
        use_case.scale_order_service.list_scale_orders.side_effect = Exception("Database error")

        request = ListScaleOrdersRequest()

        with pytest.raises(RuntimeError, match="Failed to list scale orders"):
            await use_case.execute(request)


class TestGetScaleOrderStatusUseCase:
    """Test GetScaleOrderStatusUseCase."""

    @pytest.fixture
    def use_case(self):
        """Create GetScaleOrderStatusUseCase with mocked dependencies."""
        mock_scale_order = Mock()
        mock_scale_order.get_scale_order_status = AsyncMock()

        return create_service_with_mocks(
            GetScaleOrderStatusUseCase,
            "src.use_cases.scale_orders.track",
            {"scale_order_service": mock_scale_order},
        )

    @pytest.fixture
    def sample_status(self):
        """Sample scale order status."""
        scale_order = ScaleOrder(
            id="scale_123",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.2,
            num_orders=5,
            start_price=50000.0,
            end_price=48000.0,
            distribution_type="linear",
            order_ids=[1001, 1002, 1003],
            orders_placed=5,
            orders_filled=2,
            status="active",
        )

        return ScaleOrderStatus(
            scale_order=scale_order,
            open_orders=[
                {"order_id": 1001, "price": 50000.0, "size": 0.04},
                {"order_id": 1002, "price": 49500.0, "size": 0.04},
                {"order_id": 1003, "price": 49000.0, "size": 0.04},
            ],
            filled_orders=[
                {"order_id": 1004, "price": 48500.0, "size": 0.04, "filled_size": 0.04},
                {"order_id": 1005, "price": 48000.0, "size": 0.04, "filled_size": 0.04},
            ],
            fill_percentage=40.0,
        )

    # ===================================================================
    # Get Status tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_get_status_success(self, use_case, sample_status):
        """Test getting scale order status."""
        use_case.scale_order_service.get_scale_order_status.return_value = sample_status

        request = GetScaleOrderStatusRequest(scale_order_id="scale_123")

        response = await use_case.execute(request)

        use_case.scale_order_service.get_scale_order_status.assert_called_once_with("scale_123")
        assert response.status.scale_order.id == "scale_123"
        assert response.status.fill_percentage == 40.0
        assert len(response.status.open_orders) == 3
        assert len(response.status.filled_orders) == 2

    @pytest.mark.asyncio
    async def test_get_status_not_found_raises_value_error(self, use_case):
        """Test getting status for non-existent scale order."""
        use_case.scale_order_service.get_scale_order_status.return_value = None

        request = GetScaleOrderStatusRequest(scale_order_id="nonexistent")

        with pytest.raises(ValueError, match="Scale order not found"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_get_status_service_failure_raises_runtime_error(self, use_case):
        """Test service failure raises RuntimeError."""
        use_case.scale_order_service.get_scale_order_status.side_effect = Exception("API error")

        request = GetScaleOrderStatusRequest(scale_order_id="scale_123")

        with pytest.raises(RuntimeError, match="Failed to get scale order status"):
            await use_case.execute(request)


class TestCancelScaleOrderUseCase:
    """Test CancelScaleOrderUseCase."""

    @pytest.fixture
    def use_case(self):
        """Create CancelScaleOrderUseCase with mocked dependencies."""
        mock_scale_order = Mock()
        mock_scale_order.cancel_scale_order = AsyncMock()

        return create_service_with_mocks(
            CancelScaleOrderUseCase,
            "src.use_cases.scale_orders.track",
            {"scale_order_service": mock_scale_order},
        )

    # ===================================================================
    # Cancel Success tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_cancel_all_orders_success(self, use_case):
        """Test cancelling all orders in scale order."""
        # Service returns a Dict with cancellation results
        result = {
            "scale_order_id": "scale_123",
            "orders_cancelled": 3,
            "total_orders": 3,
            "errors": None,
            "status": "cancelled",
        }

        use_case.scale_order_service.cancel_scale_order.return_value = result

        request = CancelScaleOrderRequest(scale_order_id="scale_123")

        response = await use_case.execute(request)

        # Verify service was called with ScaleOrderCancel object
        assert use_case.scale_order_service.cancel_scale_order.call_count == 1
        call_arg = use_case.scale_order_service.cancel_scale_order.call_args[0][0]
        assert call_arg.scale_order_id == "scale_123"
        assert call_arg.cancel_all_orders is True

        # Verify response
        assert response.result["orders_cancelled"] == 3
        assert response.result["errors"] is None

    @pytest.mark.asyncio
    async def test_cancel_partial_success(self, use_case):
        """Test partial cancellation (some orders fail to cancel)."""
        # Service returns a Dict with errors when partial cancellation
        result = {
            "scale_order_id": "scale_123",
            "orders_cancelled": 2,
            "total_orders": 3,
            "errors": ["Order 1003 already filled"],
            "status": "cancelled",
        }

        use_case.scale_order_service.cancel_scale_order.return_value = result

        request = CancelScaleOrderRequest(scale_order_id="scale_123")

        response = await use_case.execute(request)

        assert response.result["orders_cancelled"] == 2
        assert len(response.result["errors"]) == 1
        assert "Order 1003" in response.result["errors"][0]

    # ===================================================================
    # Cancel Failure tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_cancel_not_found_raises_value_error(self, use_case):
        """Test cancelling non-existent scale order."""
        use_case.scale_order_service.cancel_scale_order.side_effect = ValueError(
            "Scale order not found: nonexistent"
        )

        request = CancelScaleOrderRequest(scale_order_id="nonexistent")

        with pytest.raises(ValueError, match="Scale order not found"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_cancel_service_failure_raises_runtime_error(self, use_case):
        """Test service failure raises RuntimeError."""
        use_case.scale_order_service.cancel_scale_order.side_effect = Exception("API error")

        request = CancelScaleOrderRequest(scale_order_id="scale_123")

        with pytest.raises(RuntimeError, match="Failed to cancel scale order"):
            await use_case.execute(request)
