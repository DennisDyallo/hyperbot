"""
Unit tests for ListOrdersUseCase.

Tests order listing logic with filters for coin, side, and order type.
"""

from unittest.mock import Mock

import pytest

from src.use_cases.trading.list_orders import (
    ListOrdersRequest,
    ListOrdersUseCase,
    OrderInfo,
)
from tests.helpers.service_mocks import ServiceMockBuilder, create_service_with_mocks


class TestListOrdersUseCase:
    """Test ListOrdersUseCase."""

    @pytest.fixture
    def mock_orders_data(self):
        """Sample orders data from Hyperliquid API."""
        return [
            {
                "coin": "BTC",
                "oid": 12345,
                "side": "B",  # Buy
                "orderType": {"limit": {"tif": "Gtc"}},
                "sz": "0.5",
                "limitPx": "45000.0",
                "szDecimals": "0.5",  # Remaining size
                "timestamp": 1732896000000,
                "reduceOnly": False,
            },
            {
                "coin": "ETH",
                "oid": 67890,
                "side": "A",  # Ask (Sell)
                "orderType": {"limit": {"tif": "Ioc"}},
                "sz": "2.0",
                "limitPx": "3000.0",
                "szDecimals": "2.0",
                "timestamp": 1732896100000,
                "reduceOnly": True,
            },
            {
                "coin": "BTC",
                "oid": 54321,
                "side": "A",  # Sell
                "orderType": {"limit": {"tif": "Gtc"}},
                "sz": "0.3",
                "limitPx": "48000.0",
                "szDecimals": "0.3",
                "timestamp": 1732896200000,
                "reduceOnly": False,
            },
        ]

    @pytest.fixture
    def use_case(self, mock_orders_data):
        """Create ListOrdersUseCase with mocked dependencies."""
        mock_order = ServiceMockBuilder.order_service()
        mock_order.list_open_orders = Mock(return_value=mock_orders_data)

        return create_service_with_mocks(
            ListOrdersUseCase,
            "src.use_cases.trading.list_orders",
            {
                "order_service": mock_order,
            },
        )

    # ===================================================================
    # List All Orders tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_list_all_orders_success(self, use_case):
        """Test listing all orders without filters."""
        request = ListOrdersRequest()

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.total_count == 3
        assert len(response.orders) == 3
        assert response.message == "Found 3 orders"
        assert response.filters_applied == {
            "coin": None,
            "side": None,
            "order_type": None,
        }

        # Verify list_open_orders called with no filters
        use_case.order_service.list_open_orders.assert_called_once_with(
            coin=None, side=None, order_type=None
        )

    # ===================================================================
    # Filter by Coin tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_filter_by_coin(self, use_case, mock_orders_data):
        """Test filtering orders by coin."""
        # Mock returns only BTC orders
        btc_orders = [o for o in mock_orders_data if o["coin"] == "BTC"]
        use_case.order_service.list_open_orders = Mock(return_value=btc_orders)

        request = ListOrdersRequest(coin="BTC")

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.total_count == 2
        assert all(o.coin == "BTC" for o in response.orders)
        assert response.filters_applied["coin"] == "BTC"

        use_case.order_service.list_open_orders.assert_called_once_with(
            coin="BTC", side=None, order_type=None
        )

    # ===================================================================
    # Filter by Side tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_filter_by_buy_side(self, use_case, mock_orders_data):
        """Test filtering orders by buy side."""
        # Mock returns only buy orders
        buy_orders = [o for o in mock_orders_data if o["side"] == "B"]
        use_case.order_service.list_open_orders = Mock(return_value=buy_orders)

        request = ListOrdersRequest(side="buy")

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.total_count == 1
        assert all(o.side == "buy" for o in response.orders)
        assert response.filters_applied["side"] == "buy"

        use_case.order_service.list_open_orders.assert_called_once_with(
            coin=None, side="buy", order_type=None
        )

    @pytest.mark.asyncio
    async def test_filter_by_sell_side(self, use_case, mock_orders_data):
        """Test filtering orders by sell side."""
        # Mock returns only sell orders
        sell_orders = [o for o in mock_orders_data if o["side"] == "A"]
        use_case.order_service.list_open_orders = Mock(return_value=sell_orders)

        request = ListOrdersRequest(side="sell")

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.total_count == 2
        assert all(o.side == "sell" for o in response.orders)

    # ===================================================================
    # Filter by Order Type tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_filter_by_order_type(self, use_case, mock_orders_data):
        """Test filtering orders by order type (limit)."""
        request = ListOrdersRequest(order_type="limit")

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.total_count == 3  # All are limit orders
        assert all(o.order_type == "limit" for o in response.orders)

    # ===================================================================
    # Combined Filters tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_combined_filters(self, use_case, mock_orders_data):
        """Test combining multiple filters."""
        # Mock returns BTC sell orders
        filtered = [o for o in mock_orders_data if o["coin"] == "BTC" and o["side"] == "A"]
        use_case.order_service.list_open_orders = Mock(return_value=filtered)

        request = ListOrdersRequest(coin="BTC", side="sell")

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.total_count == 1
        assert response.orders[0].coin == "BTC"
        assert response.orders[0].side == "sell"

    # ===================================================================
    # Empty Results tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_no_orders_found(self, use_case):
        """Test when no orders match filters."""
        use_case.order_service.list_open_orders = Mock(return_value=[])

        request = ListOrdersRequest(coin="SOL")

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.total_count == 0
        assert len(response.orders) == 0
        assert response.message == "Found 0 orders"

    # ===================================================================
    # Order Parsing tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_order_info_parsing(self, use_case):
        """Test that orders are correctly parsed into OrderInfo models."""
        request = ListOrdersRequest()

        response = await use_case.execute(request)

        # Verify first order (BTC buy)
        btc_buy = response.orders[0]
        assert isinstance(btc_buy, OrderInfo)
        assert btc_buy.coin == "BTC"
        assert btc_buy.order_id == 12345
        assert btc_buy.side == "buy"
        assert btc_buy.order_type == "limit"
        assert btc_buy.size == 0.5
        assert btc_buy.limit_price == 45000.0
        assert btc_buy.remaining_size == 0.5
        assert btc_buy.reduce_only is False

        # Verify second order (ETH sell)
        eth_sell = response.orders[1]
        assert eth_sell.coin == "ETH"
        assert eth_sell.order_id == 67890
        assert eth_sell.side == "sell"
        assert eth_sell.reduce_only is True

    # ===================================================================
    # Error Handling tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_invalid_filter_value(self, use_case):
        """Test handling of invalid filter values."""
        use_case.order_service.list_open_orders = Mock(
            side_effect=ValueError("Invalid side: invalid")
        )

        request = ListOrdersRequest(side="invalid")

        response = await use_case.execute(request)

        assert response.status == "failed"
        assert response.total_count == 0
        assert "Invalid filter" in response.message

    @pytest.mark.asyncio
    async def test_api_error(self, use_case):
        """Test handling of API errors."""
        use_case.order_service.list_open_orders = Mock(
            side_effect=Exception("API connection failed")
        )

        request = ListOrdersRequest()

        response = await use_case.execute(request)

        assert response.status == "failed"
        assert response.total_count == 0
        assert "Error" in response.message

    @pytest.mark.asyncio
    async def test_malformed_order_skipped(self, use_case):
        """Test that malformed orders are handled gracefully with defaults."""
        # Include one malformed order (missing required fields)
        malformed_orders = [
            {
                "coin": "BTC",
                "oid": 12345,
                "side": "B",
                "orderType": {"limit": {"tif": "Gtc"}},
                "sz": "0.5",
                "limitPx": "45000.0",
                "szDecimals": "0.5",
            },
            {
                # Malformed - only has minimal fields
                "coin": "ETH",
                "oid": 99999,
            },
        ]
        use_case.order_service.list_open_orders = Mock(return_value=malformed_orders)

        request = ListOrdersRequest()

        response = await use_case.execute(request)

        # Both orders should be returned (malformed gets default values)
        assert response.status == "success"
        assert response.total_count == 2

        # First order should be fully populated
        assert response.orders[0].coin == "BTC"
        assert response.orders[0].order_id == 12345

        # Second order should have defaults for missing fields
        assert response.orders[1].coin == "ETH"
        assert response.orders[1].order_id == 99999
        assert response.orders[1].order_type == "unknown"  # Default when orderType missing
