"""
Unit tests for CancelOrderUseCase and CancelBulkOrdersUseCase.

Tests order cancellation logic for single and bulk operations.
"""

from unittest.mock import Mock

import pytest

from src.use_cases.trading.cancel_orders import (
    CancelBulkOrdersRequest,
    CancelBulkOrdersUseCase,
    CancelOrderRequest,
    CancelOrderUseCase,
)
from tests.helpers.service_mocks import ServiceMockBuilder, create_service_with_mocks


class TestCancelOrderUseCase:
    """Test CancelOrderUseCase for single order cancellation."""

    @pytest.fixture
    def use_case(self):
        """Create CancelOrderUseCase with mocked dependencies."""
        mock_order = ServiceMockBuilder.order_service()
        mock_order.cancel_order = Mock(return_value={"status": "success"})

        return create_service_with_mocks(
            CancelOrderUseCase,
            "src.use_cases.trading.cancel_orders",
            {
                "order_service": mock_order,
            },
        )

    # ===================================================================
    # Single Order Cancel tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_cancel_single_order_success(self, use_case):
        """Test successful cancellation of a single order."""
        request = CancelOrderRequest(coin="BTC", order_id=12345)

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.coin == "BTC"
        assert response.order_id == 12345
        assert "canceled successfully" in response.message.lower()

        use_case.order_service.cancel_order.assert_called_once_with(coin="BTC", order_id=12345)

    @pytest.mark.asyncio
    async def test_cancel_order_api_error(self, use_case):
        """Test handling of API error during cancellation."""
        use_case.order_service.cancel_order = Mock(side_effect=Exception("Order not found"))

        request = CancelOrderRequest(coin="BTC", order_id=99999)

        response = await use_case.execute(request)

        assert response.status == "failed"
        assert response.coin == "BTC"
        assert response.order_id == 99999
        assert "Failed to cancel order" in response.message

    @pytest.mark.asyncio
    async def test_cancel_order_runtime_error(self, use_case):
        """Test handling of runtime error (wallet not configured)."""
        use_case.order_service.cancel_order = Mock(
            side_effect=RuntimeError("Wallet address not configured")
        )

        request = CancelOrderRequest(coin="ETH", order_id=54321)

        response = await use_case.execute(request)

        assert response.status == "failed"
        assert "Wallet address not configured" in response.message


class TestCancelBulkOrdersUseCase:
    """Test CancelBulkOrdersUseCase for bulk order cancellation."""

    @pytest.fixture
    def use_case(self):
        """Create CancelBulkOrdersUseCase with mocked dependencies."""
        mock_order = ServiceMockBuilder.order_service()
        mock_order.cancel_order = Mock(return_value={"status": "success"})
        mock_order.cancel_all_orders = Mock(return_value={"status": "success", "canceled_count": 5})

        return create_service_with_mocks(
            CancelBulkOrdersUseCase,
            "src.use_cases.trading.cancel_orders",
            {
                "order_service": mock_order,
            },
        )

    # ===================================================================
    # Bulk Cancel Specific Orders tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_cancel_multiple_orders_all_success(self, use_case):
        """Test bulk cancellation where all orders succeed."""
        request = CancelBulkOrdersRequest(
            order_ids=[("BTC", 12345), ("ETH", 67890), ("SOL", 11111)]
        )

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.total_requested == 3
        assert response.successful == 3
        assert response.failed == 0
        assert len(response.results) == 3
        assert "All 3 orders canceled successfully" in response.message

        # Verify each order was canceled
        assert use_case.order_service.cancel_order.call_count == 3

    @pytest.mark.asyncio
    async def test_cancel_multiple_orders_partial_success(self, use_case):
        """Test bulk cancellation with partial success."""

        def cancel_side_effect(coin, order_id):
            """Mock that fails for ETH order."""
            if coin == "ETH":
                raise Exception("Order not found")
            return {"status": "success"}

        use_case.order_service.cancel_order = Mock(side_effect=cancel_side_effect)

        request = CancelBulkOrdersRequest(
            order_ids=[("BTC", 12345), ("ETH", 99999), ("SOL", 11111)]
        )

        response = await use_case.execute(request)

        assert response.status == "partial"
        assert response.total_requested == 3
        assert response.successful == 2
        assert response.failed == 1
        assert len(response.results) == 3
        assert "2 succeeded, 1 failed" in response.message

        # Check individual results
        btc_result = next(r for r in response.results if r.coin == "BTC")
        assert btc_result.status == "success"

        eth_result = next(r for r in response.results if r.coin == "ETH")
        assert eth_result.status == "failed"
        assert "Order not found" in eth_result.message

        sol_result = next(r for r in response.results if r.coin == "SOL")
        assert sol_result.status == "success"

    @pytest.mark.asyncio
    async def test_cancel_multiple_orders_all_fail(self, use_case):
        """Test bulk cancellation where all orders fail."""
        use_case.order_service.cancel_order = Mock(side_effect=Exception("API unavailable"))

        request = CancelBulkOrdersRequest(order_ids=[("BTC", 12345), ("ETH", 67890)])

        response = await use_case.execute(request)

        assert response.status == "failed"
        assert response.total_requested == 2
        assert response.successful == 0
        assert response.failed == 2
        assert "All 2 orders failed" in response.message

    # ===================================================================
    # Cancel All Orders tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_cancel_all_orders_success(self, use_case):
        """Test cancel all orders functionality."""
        request = CancelBulkOrdersRequest(order_ids=[], cancel_all=True)

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.total_requested == 5  # From mock return value
        assert response.successful == 5
        assert response.failed == 0
        assert "Successfully canceled all 5 orders" in response.message

        use_case.order_service.cancel_all_orders.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_all_orders_api_error(self, use_case):
        """Test cancel all with API error."""
        use_case.order_service.cancel_all_orders = Mock(
            side_effect=Exception("API connection failed")
        )

        request = CancelBulkOrdersRequest(order_ids=[], cancel_all=True)

        response = await use_case.execute(request)

        assert response.status == "failed"
        assert response.successful == 0
        assert "Failed to cancel all orders" in response.message

    # ===================================================================
    # Edge Cases tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_empty_order_list(self, use_case):
        """Test bulk cancel with empty order list."""
        request = CancelBulkOrdersRequest(order_ids=[])

        response = await use_case.execute(request)

        assert response.status == "failed"
        assert response.total_requested == 0
        assert "No orders specified" in response.message

    @pytest.mark.asyncio
    async def test_single_order_in_bulk(self, use_case):
        """Test bulk cancel with just one order."""
        request = CancelBulkOrdersRequest(order_ids=[("BTC", 12345)])

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.total_requested == 1
        assert response.successful == 1
        assert len(response.results) == 1

    @pytest.mark.asyncio
    async def test_unexpected_error(self, use_case):
        """Test handling of unexpected errors in bulk cancel."""
        # Simulate unexpected error in the use case itself (not from service)
        use_case.order_service.cancel_order = Mock(side_effect=TypeError("Unexpected type error"))

        request = CancelBulkOrdersRequest(order_ids=[("BTC", 12345)])

        response = await use_case.execute(request)

        # Should still return a response, not crash
        assert response.status in ["failed", "partial"]
        assert response.total_requested == 1

    # ===================================================================
    # Detailed Results tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_detailed_results_structure(self, use_case):
        """Test that detailed results are properly structured."""

        def cancel_side_effect(coin, order_id):
            """Mock different results for different orders."""
            if order_id == 99999:
                raise Exception(f"Order {order_id} not found")
            return {"status": "success"}

        use_case.order_service.cancel_order = Mock(side_effect=cancel_side_effect)

        request = CancelBulkOrdersRequest(
            order_ids=[("BTC", 12345), ("ETH", 99999), ("SOL", 11111)]
        )

        response = await use_case.execute(request)

        # Check structure of results
        assert len(response.results) == 3

        for result in response.results:
            assert hasattr(result, "coin")
            assert hasattr(result, "order_id")
            assert hasattr(result, "status")
            assert hasattr(result, "message")
            assert result.status in ["success", "failed"]

        # Verify specific failure message
        eth_result = next(r for r in response.results if r.coin == "ETH")
        assert "Order 99999 not found" in eth_result.message
