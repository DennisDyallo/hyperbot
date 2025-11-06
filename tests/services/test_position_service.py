"""
Unit tests for PositionService.

Tests position listing, retrieval, closing, and summary calculations.
CRITICAL - bugs here = incorrect position management, unintended losses.

REFACTORED: Now using tests/helpers for reduced boilerplate and consistency.
"""
import pytest
from unittest.mock import Mock, patch
from src.services.position_service import PositionService, position_service
from src.config import settings

# Import helpers for cleaner test code
from tests.helpers import (
    create_service_with_mocks,
    ServiceMockBuilder,
    PositionBuilder,
    assert_float_approx
)


class TestPositionServiceListPositions:
    """Test list_positions method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked account service using helper."""
        return create_service_with_mocks(
            PositionService,
            'src.services.position_service',
            {
                'account_service': ServiceMockBuilder.account_service(),
                'hyperliquid_service': ServiceMockBuilder.hyperliquid_service()
            }
        )

    def test_list_positions_success(self, service):
        """Test listing positions successfully."""
        btc_pos = PositionBuilder().with_coin("BTC").with_size(0.1).build()
        eth_pos = PositionBuilder().with_coin("ETH").with_size(2.5).build()

        service.account.get_account_info.return_value = {
            "positions": [btc_pos, eth_pos]
        }

        positions = service.list_positions()

        assert len(positions) == 2
        assert positions[0]["position"]["coin"] == "BTC"
        assert positions[1]["position"]["coin"] == "ETH"

    def test_list_positions_empty(self, service):
        """Test listing when no positions exist."""
        service.account.get_account_info.return_value = {
            "positions": []
        }

        positions = service.list_positions()

        assert positions == []

    def test_list_positions_no_positions_key(self, service):
        """Test listing when positions key missing."""
        service.account.get_account_info.return_value = {}

        positions = service.list_positions()

        assert positions == []

    def test_list_positions_api_failure(self, service):
        """Test listing raises exception on API failure."""
        service.account.get_account_info.side_effect = Exception("API error")

        with pytest.raises(Exception, match="API error"):
            service.list_positions()


class TestPositionServiceGetPosition:
    """Test get_position method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked account service using helper."""
        mock_account = ServiceMockBuilder.account_service()

        # Set up default positions
        btc_pos = PositionBuilder().with_coin("BTC").with_size(0.1).with_position_value(5000.0).build()
        eth_pos = PositionBuilder().with_coin("ETH").with_size(2.5).with_position_value(7500.0).build()
        sol_pos = PositionBuilder().with_coin("SOL").with_size(-10.0).with_position_value(-1500.0).build()

        mock_account.get_account_info.return_value = {
            "positions": [btc_pos, eth_pos, sol_pos]
        }

        return create_service_with_mocks(
            PositionService,
            'src.services.position_service',
            {
                'account_service': mock_account,
                'hyperliquid_service': ServiceMockBuilder.hyperliquid_service()
            }
        )

    def test_get_position_found(self, service):
        """Test getting existing position."""
        position = service.get_position("BTC")

        assert position is not None
        assert position["position"]["coin"] == "BTC"
        assert position["position"]["size"] == 0.1  # Float (after account_service conversion)

    def test_get_position_not_found(self, service):
        """Test getting non-existent position returns None."""
        position = service.get_position("DOGE")

        assert position is None

    def test_get_position_case_sensitive(self, service):
        """Test coin symbol is case sensitive."""
        # Should not find "btc" when position is "BTC"
        position = service.get_position("btc")

        assert position is None

    def test_get_position_api_failure(self, service):
        """Test get_position raises exception on API failure."""
        service.account.get_account_info.side_effect = Exception("API error")

        with pytest.raises(Exception, match="API error"):
            service.get_position("BTC")


class TestPositionServiceClosePosition:
    """Test close_position method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies using helper."""
        mock_account = ServiceMockBuilder.account_service()
        mock_hyperliquid = ServiceMockBuilder.hyperliquid_service()

        # Set up default position
        btc_pos = PositionBuilder().with_coin("BTC").with_size(0.5).with_position_value(25000.0).build()
        mock_account.get_account_info.return_value = {
            "positions": [btc_pos]
        }

        # Set up exchange mock
        mock_exchange = Mock()
        mock_exchange.market_close.return_value = {"status": "ok"}
        mock_hyperliquid.get_exchange_client.return_value = mock_exchange

        return create_service_with_mocks(
            PositionService,
            'src.services.position_service',
            {
                'account_service': mock_account,
                'hyperliquid_service': mock_hyperliquid
            }
        )

    def test_close_position_full(self, service):
        """Test closing entire position."""
        result = service.close_position("BTC")

        assert result["status"] == "success"
        assert result["coin"] == "BTC"
        assert result["size_closed"] == 0.5

        # Verify exchange API called with None size (close all)
        exchange = service.hyperliquid.get_exchange_client()
        exchange.market_close.assert_called_once_with(
            coin="BTC",
            sz=None,
            slippage=0.05
        )

    def test_close_position_partial(self, service):
        """Test closing partial position."""
        result = service.close_position("BTC", size=0.2)

        assert result["status"] == "success"
        assert result["coin"] == "BTC"
        assert result["size_closed"] == 0.2

        # Verify exchange API called with specific size
        exchange = service.hyperliquid.get_exchange_client()
        exchange.market_close.assert_called_once_with(
            coin="BTC",
            sz=0.2,
            slippage=0.05
        )

    def test_close_position_custom_slippage(self, service):
        """Test closing with custom slippage."""
        result = service.close_position("BTC", slippage=0.1)

        # Verify slippage parameter passed correctly
        exchange = service.hyperliquid.get_exchange_client()
        exchange.market_close.assert_called_once()
        assert exchange.market_close.call_args[1]["slippage"] == 0.1

    def test_close_position_not_found_raises(self, service):
        """Test closing non-existent position raises ValueError."""
        service.account.get_account_info.return_value = {"positions": []}

        with pytest.raises(ValueError, match="No open position found for DOGE"):
            service.close_position("DOGE")

    def test_close_position_zero_size_raises(self, service):
        """Test closing with zero size raises ValueError."""
        with pytest.raises(ValueError, match="Size must be positive"):
            service.close_position("BTC", size=0.0)

    def test_close_position_negative_size_raises(self, service):
        """Test closing with negative size raises ValueError."""
        with pytest.raises(ValueError, match="Size must be positive"):
            service.close_position("BTC", size=-0.1)

    def test_close_position_size_exceeds_raises(self, service):
        """Test closing size exceeding current position raises ValueError."""
        # Current position is 0.5
        with pytest.raises(ValueError, match="exceeds current position size"):
            service.close_position("BTC", size=1.0)

    def test_close_position_no_wallet_raises(self, service):
        """Test closing without wallet configured raises RuntimeError."""
        with patch.object(settings, 'HYPERLIQUID_WALLET_ADDRESS', None):
            with pytest.raises(RuntimeError, match="Wallet address not configured"):
                service.close_position("BTC")

    def test_close_position_api_failure(self, service):
        """Test close_position raises exception on API failure."""
        exchange = service.hyperliquid.get_exchange_client()
        exchange.market_close.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            service.close_position("BTC")

    def test_close_position_short_position(self, service):
        """Test closing short position (negative size)."""
        sol_pos = PositionBuilder().with_coin("SOL").with_size(-10.0).with_position_value(-1500.0).build()
        service.account.get_account_info.return_value = {
            "positions": [sol_pos]
        }

        result = service.close_position("SOL")

        assert result["status"] == "success"
        assert result["size_closed"] == 10.0  # Absolute value


class TestPositionServiceGetPositionSummary:
    """Test get_position_summary method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked account service using helper."""
        return create_service_with_mocks(
            PositionService,
            'src.services.position_service',
            {
                'account_service': ServiceMockBuilder.account_service(),
                'hyperliquid_service': ServiceMockBuilder.hyperliquid_service()
            }
        )

    def test_summary_with_positions(self, service):
        """Test summary with multiple positions."""
        # Use builders for clean position creation
        btc_pos = PositionBuilder()        \
            .with_coin("BTC")              \
            .with_size(0.5)                \
            .with_position_value(25000.0)  \
            .with_pnl(500.0)               \
            .build()

        eth_pos = PositionBuilder()        \
            .with_coin("ETH")              \
            .with_size(10.0)               \
            .with_position_value(30000.0)  \
            .with_pnl(-200.0)              \
            .build()

        sol_pos = PositionBuilder()        \
            .with_coin("SOL")              \
            .with_size(-20.0)              \
            .with_position_value(-3000.0)  \
            .with_pnl(100.0)               \
            .build()

        service.account.get_account_info.return_value = {
            "positions": [btc_pos, eth_pos, sol_pos]
        }

        summary = service.get_position_summary()

        assert summary["total_positions"] == 3
        assert summary["long_positions"] == 2  # BTC, ETH
        assert summary["short_positions"] == 1  # SOL
        assert_float_approx(summary["total_position_value"], 52000.0)
        assert_float_approx(summary["total_unrealized_pnl"], 400.0)
        assert len(summary["positions"]) == 3

    def test_summary_no_positions(self, service):
        """Test summary with no positions."""
        service.account.get_account_info.return_value = {
            "positions": []
        }

        summary = service.get_position_summary()

        assert summary["total_positions"] == 0
        assert summary["long_positions"] == 0
        assert summary["short_positions"] == 0
        assert summary["total_position_value"] == 0.0
        assert summary["total_unrealized_pnl"] == 0.0
        assert summary["positions"] == []

    def test_summary_only_long_positions(self, service):
        """Test summary with only long positions."""
        btc_pos = PositionBuilder().with_coin("BTC").with_size(0.5).with_pnl(500.0).build()
        eth_pos = PositionBuilder().with_coin("ETH").with_size(10.0).with_pnl(300.0).build()

        service.account.get_account_info.return_value = {
            "positions": [btc_pos, eth_pos]
        }

        summary = service.get_position_summary()

        assert summary["long_positions"] == 2
        assert summary["short_positions"] == 0

    def test_summary_only_short_positions(self, service):
        """Test summary with only short positions."""
        btc_pos = PositionBuilder().with_coin("BTC").with_size(-0.5).with_pnl(-500.0).build()

        service.account.get_account_info.return_value = {
            "positions": [btc_pos]
        }

        summary = service.get_position_summary()

        assert summary["long_positions"] == 0
        assert summary["short_positions"] == 1

    def test_summary_position_details(self, service):
        """Test individual position details in summary."""
        btc_pos = PositionBuilder()        \
            .with_coin("BTC")              \
            .with_size(0.5)                \
            .with_position_value(25000.0)  \
            .with_pnl(500.0)               \
            .build()

        service.account.get_account_info.return_value = {
            "positions": [btc_pos]
        }

        summary = service.get_position_summary()

        pos = summary["positions"][0]
        assert pos["coin"] == "BTC"
        assert pos["size"] == 0.5
        assert pos["value"] == 25000.0
        assert pos["pnl"] == 500.0

    def test_summary_api_failure(self, service):
        """Test summary raises exception on API failure."""
        service.account.get_account_info.side_effect = Exception("API error")

        with pytest.raises(Exception, match="API error"):
            service.get_position_summary()


class TestPositionServiceSingleton:
    """Test global service singleton."""

    def test_singleton_instance_exists(self):
        """Test global service instance is available."""
        assert position_service is not None
        assert isinstance(position_service, PositionService)

    def test_singleton_has_dependencies(self):
        """Test singleton has required dependencies."""
        assert hasattr(position_service, 'hyperliquid')
        assert hasattr(position_service, 'account')
