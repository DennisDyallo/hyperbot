"""
Unit tests for OrderService.

Tests order placement, cancellation, and listing functionality.

MIGRATED: Now using tests/helpers for service mocking.
- create_service_with_mocks replaces manual fixture boilerplate
- ServiceMockBuilder provides pre-configured hyperliquid mock
"""

from unittest.mock import Mock, patch

import pytest

from src.services.order_service import OrderService

# Import helpers for cleaner service mocking
from tests.helpers import ServiceMockBuilder, create_service_with_mocks


class TestOrderService:
    """Test OrderService methods."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with wallet address."""
        with patch("src.services.order_service.settings") as mock_settings:
            mock_settings.HYPERLIQUID_WALLET_ADDRESS = "0x1234567890abcdef"
            yield mock_settings

    @pytest.fixture
    def service(self, mock_settings):
        """Create OrderService instance with mocked dependencies."""
        return create_service_with_mocks(
            OrderService,
            "src.services.order_service",
            {"hyperliquid_service": ServiceMockBuilder.hyperliquid_service()},
        )

    # ===================================================================
    # list_open_orders() tests
    # ===================================================================

    def test_list_open_orders_success(self, service, mock_settings):
        """Test successfully listing open orders."""
        mock_info = Mock()
        mock_info.open_orders.return_value = [
            {"coin": "BTC", "oid": 123, "side": "B", "sz": 0.5, "limitPx": 50000},
            {"coin": "ETH", "oid": 124, "side": "A", "sz": 10.0, "limitPx": 3000},
        ]
        service.hyperliquid.get_info_client.return_value = mock_info

        orders = service.list_open_orders()

        assert len(orders) == 2
        assert orders[0]["coin"] == "BTC"
        assert orders[1]["coin"] == "ETH"
        mock_info.open_orders.assert_called_once_with("0x1234567890abcdef")

    def test_list_open_orders_empty(self, service, mock_settings):
        """Test listing open orders when none exist."""
        mock_info = Mock()
        mock_info.open_orders.return_value = []
        service.hyperliquid.get_info_client.return_value = mock_info

        orders = service.list_open_orders()

        assert len(orders) == 0

    def test_list_open_orders_no_wallet_address(self, service, mock_settings):
        """Test list_open_orders fails when wallet address not configured."""
        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None

        with pytest.raises(RuntimeError, match="Wallet address not configured"):
            service.list_open_orders()

    def test_list_open_orders_api_failure(self, service, mock_settings):
        """Test list_open_orders handles API failures."""
        mock_info = Mock()
        mock_info.open_orders.side_effect = Exception("API Error")
        service.hyperliquid.get_info_client.return_value = mock_info

        with pytest.raises(Exception, match="API Error"):
            service.list_open_orders()

    # ===================================================================
    # place_market_order() tests
    # ===================================================================

    def test_place_market_order_buy_success(self, service, mock_settings):
        """Test successfully placing a market buy order."""
        mock_exchange = Mock()
        mock_exchange.market_open.return_value = {
            "status": "ok",
            "response": {"type": "order", "data": {"statuses": [{"filled": {"totalSz": "0.1"}}]}},
        }
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        result = service.place_market_order(coin="BTC", is_buy=True, size=0.1, slippage=0.05)

        assert result["status"] == "success"
        assert result["coin"] == "BTC"
        assert result["side"] == "buy"
        assert result["size"] == 0.1
        assert result["order_type"] == "market"
        mock_exchange.market_open.assert_called_once_with(
            name="BTC", is_buy=True, sz=0.1, slippage=0.05
        )

    def test_place_market_order_sell_success(self, service, mock_settings):
        """Test successfully placing a market sell order."""
        mock_exchange = Mock()
        mock_exchange.market_open.return_value = {
            "status": "ok",
            "response": {"type": "order", "data": {"statuses": [{"filled": {"totalSz": "0.5"}}]}},
        }
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        result = service.place_market_order(coin="ETH", is_buy=False, size=0.5)

        assert result["status"] == "success"
        assert result["side"] == "sell"
        assert result["coin"] == "ETH"

    def test_place_market_order_invalid_size_zero(self, service, mock_settings):
        """Test place_market_order fails with zero size."""
        with pytest.raises(ValueError, match="Size must be positive"):
            service.place_market_order(coin="BTC", is_buy=True, size=0)

    def test_place_market_order_invalid_size_negative(self, service, mock_settings):
        """Test place_market_order fails with negative size."""
        with pytest.raises(ValueError, match="Size must be positive"):
            service.place_market_order(coin="BTC", is_buy=True, size=-0.5)

    def test_place_market_order_no_wallet_address(self, service, mock_settings):
        """Test place_market_order fails when wallet address not configured."""
        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None

        with pytest.raises(RuntimeError, match="Wallet address not configured"):
            service.place_market_order(coin="BTC", is_buy=True, size=0.1)

    def test_place_market_order_api_error_response(self, service, mock_settings):
        """Test place_market_order handles API error responses."""
        mock_exchange = Mock()
        # Hyperliquid returns "ok" but error is in nested statuses array
        mock_exchange.market_open.return_value = {
            "status": "ok",
            "response": {"data": {"statuses": [{"error": "Insufficient margin"}]}},
        }
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        with pytest.raises(ValueError, match="Insufficient margin"):
            service.place_market_order(coin="BTC", is_buy=True, size=0.1)

    def test_place_market_order_api_failure(self, service, mock_settings):
        """Test place_market_order handles API exceptions."""
        mock_exchange = Mock()
        mock_exchange.market_open.side_effect = Exception("Network error")
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        with pytest.raises(Exception, match="Network error"):
            service.place_market_order(coin="BTC", is_buy=True, size=0.1)

    # ===================================================================
    # place_limit_order() tests
    # ===================================================================

    def test_place_limit_order_buy_success(self, service, mock_settings):
        """Test successfully placing a limit buy order."""
        mock_exchange = Mock()
        mock_exchange.order.return_value = {
            "status": "ok",
            "response": {"type": "order", "data": {"statuses": [{"resting": {"oid": 12345}}]}},
        }
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        result = service.place_limit_order(
            coin="BTC", is_buy=True, size=0.5, limit_price=50000.0, time_in_force="Gtc"
        )

        assert result["status"] == "success"
        assert result["coin"] == "BTC"
        assert result["side"] == "buy"
        assert result["size"] == 0.5
        assert result["limit_price"] == 50000.0
        assert result["order_type"] == "limit"
        assert result["time_in_force"] == "Gtc"
        mock_exchange.order.assert_called_once_with(
            name="BTC", is_buy=True, sz=0.5, limit_px=50000.0, order_type={"limit": {"tif": "Gtc"}}
        )

    def test_place_limit_order_sell_success(self, service, mock_settings):
        """Test successfully placing a limit sell order."""
        mock_exchange = Mock()
        mock_exchange.order.return_value = {
            "status": "ok",
            "response": {"type": "order", "data": {"statuses": [{"resting": {"oid": 12346}}]}},
        }
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        result = service.place_limit_order(coin="ETH", is_buy=False, size=10.0, limit_price=3000.0)

        assert result["status"] == "success"
        assert result["side"] == "sell"
        assert result["coin"] == "ETH"

    def test_place_limit_order_with_ioc_tif(self, service, mock_settings):
        """Test placing limit order with IOC time-in-force."""
        mock_exchange = Mock()
        mock_exchange.order.return_value = {
            "status": "ok",
            "response": {"type": "order", "data": {"statuses": [{"filled": {}}]}},
        }
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        result = service.place_limit_order(
            coin="SOL", is_buy=True, size=100.0, limit_price=150.0, time_in_force="Ioc"
        )

        assert result["time_in_force"] == "Ioc"
        call_args = mock_exchange.order.call_args
        assert call_args.kwargs["order_type"] == {"limit": {"tif": "Ioc"}}

    def test_place_limit_order_with_alo_tif(self, service, mock_settings):
        """Test placing limit order with ALO time-in-force."""
        mock_exchange = Mock()
        mock_exchange.order.return_value = {
            "status": "ok",
            "response": {"type": "order", "data": {"statuses": [{"resting": {}}]}},
        }
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        result = service.place_limit_order(
            coin="AVAX", is_buy=True, size=50.0, limit_price=40.0, time_in_force="Alo"
        )

        assert result["time_in_force"] == "Alo"

    def test_place_limit_order_invalid_size_zero(self, service, mock_settings):
        """Test place_limit_order fails with zero size."""
        with pytest.raises(ValueError, match="Size must be positive"):
            service.place_limit_order(coin="BTC", is_buy=True, size=0, limit_price=50000.0)

    def test_place_limit_order_invalid_size_negative(self, service, mock_settings):
        """Test place_limit_order fails with negative size."""
        with pytest.raises(ValueError, match="Size must be positive"):
            service.place_limit_order(coin="BTC", is_buy=True, size=-1.0, limit_price=50000.0)

    def test_place_limit_order_invalid_price_zero(self, service, mock_settings):
        """Test place_limit_order fails with zero price."""
        with pytest.raises(ValueError, match="Limit price must be positive"):
            service.place_limit_order(coin="BTC", is_buy=True, size=0.5, limit_price=0)

    def test_place_limit_order_invalid_price_negative(self, service, mock_settings):
        """Test place_limit_order fails with negative price."""
        with pytest.raises(ValueError, match="Limit price must be positive"):
            service.place_limit_order(coin="BTC", is_buy=True, size=0.5, limit_price=-50000.0)

    def test_place_limit_order_invalid_time_in_force(self, service, mock_settings):
        """Test place_limit_order fails with invalid time_in_force."""
        with pytest.raises(ValueError, match="time_in_force must be one of"):
            service.place_limit_order(
                coin="BTC", is_buy=True, size=0.5, limit_price=50000.0, time_in_force="INVALID"
            )

    def test_place_limit_order_no_wallet_address(self, service, mock_settings):
        """Test place_limit_order fails when wallet address not configured."""
        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None

        with pytest.raises(RuntimeError, match="Wallet address not configured"):
            service.place_limit_order(coin="BTC", is_buy=True, size=0.5, limit_price=50000.0)

    def test_place_limit_order_api_error_response(self, service, mock_settings):
        """Test place_limit_order handles API error responses."""
        mock_exchange = Mock()
        # Hyperliquid returns "ok" but error is in nested statuses array
        mock_exchange.order.return_value = {
            "status": "ok",
            "response": {"data": {"statuses": [{"error": "Price not divisible by tick size"}]}},
        }
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        with pytest.raises(ValueError, match="Price not divisible by tick size"):
            service.place_limit_order(coin="BTC", is_buy=True, size=0.5, limit_price=50000.12345)

    # ===================================================================
    # cancel_order() tests
    # ===================================================================

    def test_cancel_order_success(self, service, mock_settings):
        """Test successfully canceling an order."""
        mock_exchange = Mock()
        mock_exchange.cancel.return_value = {
            "status": "ok",
            "response": {"type": "cancel", "data": {"statuses": ["success"]}},
        }
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        result = service.cancel_order(coin="BTC", order_id=12345)

        assert result["status"] == "success"
        assert result["coin"] == "BTC"
        assert result["order_id"] == 12345
        mock_exchange.cancel.assert_called_once_with(name="BTC", oid=12345)

    def test_cancel_order_no_wallet_address(self, service, mock_settings):
        """Test cancel_order fails when wallet address not configured."""
        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None

        with pytest.raises(RuntimeError, match="Wallet address not configured"):
            service.cancel_order(coin="BTC", order_id=12345)

    def test_cancel_order_api_error_response(self, service, mock_settings):
        """Test cancel_order handles API error responses."""
        mock_exchange = Mock()
        # Hyperliquid returns "ok" but error is in nested statuses array
        mock_exchange.cancel.return_value = {
            "status": "ok",
            "response": {"data": {"statuses": [{"error": "Order not found"}]}},
        }
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        with pytest.raises(ValueError, match="Order not found"):
            service.cancel_order(coin="BTC", order_id=99999)

    def test_cancel_order_api_failure(self, service, mock_settings):
        """Test cancel_order handles API exceptions."""
        mock_exchange = Mock()
        mock_exchange.cancel.side_effect = Exception("Network error")
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        with pytest.raises(Exception, match="Network error"):
            service.cancel_order(coin="BTC", order_id=12345)

    # ===================================================================
    # cancel_all_orders() tests
    # ===================================================================

    def test_cancel_all_orders_success(self, service, mock_settings):
        """Test successfully canceling all orders."""
        # Mock list_open_orders to return some orders
        mock_info = Mock()
        mock_info.open_orders.return_value = [
            {"coin": "BTC", "oid": 123},
            {"coin": "ETH", "oid": 124},
            {"coin": "SOL", "oid": 125},
        ]

        # Mock exchange cancel calls
        mock_exchange = Mock()
        mock_exchange.cancel.return_value = {
            "status": "ok",
            "response": {"type": "cancel", "data": {"statuses": ["success"]}},
        }

        service.hyperliquid.get_info_client.return_value = mock_info
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        result = service.cancel_all_orders()

        assert result["status"] == "success"
        assert result["canceled_count"] == 3
        assert len(result["result"]) == 3
        # Verify cancel was called for each order
        assert mock_exchange.cancel.call_count == 3

    def test_cancel_all_orders_no_open_orders(self, service, mock_settings):
        """Test cancel_all_orders when no orders exist."""
        mock_info = Mock()
        mock_info.open_orders.return_value = []
        service.hyperliquid.get_info_client.return_value = mock_info

        result = service.cancel_all_orders()

        assert result["status"] == "success"
        assert result["canceled_count"] == 0
        assert "No open orders" in result["result"]["message"]

    def test_cancel_all_orders_partial_failure(self, service, mock_settings):
        """Test cancel_all_orders when some cancellations fail."""
        mock_info = Mock()
        mock_info.open_orders.return_value = [
            {"coin": "BTC", "oid": 123},
            {"coin": "ETH", "oid": 124},
        ]

        # First cancel succeeds, second fails
        mock_exchange = Mock()
        mock_exchange.cancel.side_effect = [
            {"status": "ok", "response": {"type": "cancel", "data": {"statuses": ["success"]}}},
            {"status": "err", "response": {"type": "error", "error": "Order not found"}},
        ]

        service.hyperliquid.get_info_client.return_value = mock_info
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        with pytest.raises(RuntimeError, match="Failed to cancel 1 orders"):
            service.cancel_all_orders()

    def test_cancel_all_orders_no_wallet_address(self, service, mock_settings):
        """Test cancel_all_orders fails when wallet address not configured."""
        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None

        with pytest.raises(RuntimeError, match="Wallet address not configured"):
            service.cancel_all_orders()

    def test_cancel_all_orders_list_failure(self, service, mock_settings):
        """Test cancel_all_orders handles failures in listing orders."""
        mock_info = Mock()
        mock_info.open_orders.side_effect = Exception("API Error")
        service.hyperliquid.get_info_client.return_value = mock_info

        with pytest.raises(Exception, match="API Error"):
            service.cancel_all_orders()
