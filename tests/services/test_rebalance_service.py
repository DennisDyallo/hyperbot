"""
Unit tests for RebalanceService.

Tests portfolio rebalancing logic, validation, and risk management.
CRITICAL - bugs here = incorrect portfolio allocation, liquidation risk.

REFACTORED: Now using tests/helpers for service mocking.
- create_service_with_mocks replaces manual fixture boilerplate
- ServiceMockBuilder provides pre-configured mocks
- Result: Eliminated 17 duplicate fixtures, cleaner test code
"""

from unittest.mock import Mock, patch

import pytest

from src.services.rebalance_service import (
    RebalanceService,
    RebalanceTrade,
    TradeAction,
    rebalance_service,
)

# Import helpers for cleaner service mocking
from tests.helpers import ServiceMockBuilder, create_service_with_mocks


class TestRebalanceServiceValidation:
    """Test validate_target_weights method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked market data."""
        mock_market_data = Mock()
        mock_market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
        }
        return create_service_with_mocks(
            RebalanceService,
            "src.services.rebalance_service",
            {"market_data_service": mock_market_data},
        )

    def test_validate_weights_sum_100(self, service):
        """Test valid weights that sum to 100%."""
        target_weights = {"BTC": 60.0, "ETH": 40.0}

        # Should not raise
        service.validate_target_weights(target_weights)

    def test_validate_weights_with_tolerance(self, service):
        """Test weights within tolerance are accepted."""
        # 99.95% is within default 0.1% tolerance
        target_weights = {"BTC": 60.0, "ETH": 39.95}

        service.validate_target_weights(target_weights, tolerance=0.1)

    def test_validate_weights_sum_not_100_raises(self, service):
        """Test weights not summing to 100% raises ValueError."""
        target_weights = {"BTC": 60.0, "ETH": 30.0}  # Only 90%

        with pytest.raises(ValueError, match="must sum to 100%"):
            service.validate_target_weights(target_weights)

    def test_validate_negative_weight_raises(self, service):
        """Test negative weight raises ValueError."""
        target_weights = {"BTC": 60.0, "ETH": -10.0, "SOL": 50.0}

        with pytest.raises(ValueError, match="Negative weight"):
            service.validate_target_weights(target_weights)

    def test_validate_weight_exceeds_100_raises(self, service):
        """Test weight > 100% raises ValueError."""
        target_weights = {"BTC": 150.0, "ETH": -50.0}

        with pytest.raises(ValueError, match="exceeds 100%"):
            service.validate_target_weights(target_weights)

    def test_validate_invalid_coin_raises(self, service):
        """Test invalid coin symbol raises ValueError."""
        target_weights = {"INVALID": 50.0, "BTC": 50.0}

        with pytest.raises(ValueError, match="Invalid coin 'INVALID'"):
            service.validate_target_weights(target_weights)

    def test_validate_market_data_failure_raises(self, service):
        """Test market data fetch failure raises ValueError."""
        service.market_data_service.get_all_prices.side_effect = Exception("API error")
        target_weights = {"BTC": 50.0, "ETH": 50.0}

        with pytest.raises(ValueError, match="Failed to validate coins"):
            service.validate_target_weights(target_weights)


class TestRebalanceServiceCurrentAllocation:
    """Test calculate_current_allocation method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked position service."""
        return create_service_with_mocks(
            RebalanceService,
            "src.services.rebalance_service",
            {"position_service": ServiceMockBuilder.position_service()},
        )

    def test_calculate_allocation_no_positions(self, service):
        """Test allocation with no positions returns empty dict."""
        service.position_service.list_positions.return_value = []

        allocation = service.calculate_current_allocation()

        assert allocation == {}

    def test_calculate_allocation_single_position(self, service):
        """Test allocation with single position."""
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "10000.0"}}
        ]

        allocation = service.calculate_current_allocation()

        assert allocation == {"BTC": 100.0}

    def test_calculate_allocation_multiple_positions(self, service):
        """Test allocation with multiple positions."""
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "6000.0"}},
            {"position": {"coin": "ETH", "position_value": "4000.0"}},
        ]

        allocation = service.calculate_current_allocation()

        assert allocation["BTC"] == pytest.approx(60.0)
        assert allocation["ETH"] == pytest.approx(40.0)

    def test_calculate_allocation_handles_negative_values(self, service):
        """Test allocation uses absolute values (short positions)."""
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "-6000.0"}},  # Short
            {"position": {"coin": "ETH", "position_value": "4000.0"}},  # Long
        ]

        allocation = service.calculate_current_allocation()

        # Should use absolute values
        assert allocation["BTC"] == pytest.approx(60.0)
        assert allocation["ETH"] == pytest.approx(40.0)

    def test_calculate_allocation_zero_total_value(self, service):
        """Test allocation when total value is zero."""
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "0.0"}}
        ]

        allocation = service.calculate_current_allocation()

        assert allocation == {}


class TestRebalanceServiceCalculateRequiredTrades:
    """Test calculate_required_trades method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies."""
        mock_account = Mock()
        mock_account.get_account_info.return_value = {
            "margin_summary": {
                "total_ntl_pos": "10000.0"  # $10k total position value
            }
        }

        mock_market_data = Mock()
        mock_market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
        }

        return create_service_with_mocks(
            RebalanceService,
            "src.services.rebalance_service",
            {
                "position_service": ServiceMockBuilder.position_service(),
                "account_service": mock_account,
                "market_data_service": mock_market_data,
            },
        )

    def test_calculate_trades_open_new_positions(self, service):
        """Test calculating trades to open new positions from scratch."""
        # No current positions
        service.position_service.list_positions.return_value = []

        target_weights = {"BTC": 60.0, "ETH": 40.0}
        trades = service.calculate_required_trades(target_weights)

        # Should have 2 trades: open BTC and open ETH
        assert len(trades) == 2

        btc_trade = next(t for t in trades if t.coin == "BTC")
        assert btc_trade.action == TradeAction.OPEN
        assert btc_trade.current_allocation_pct == 0.0
        assert btc_trade.target_allocation_pct == 60.0
        assert btc_trade.target_usd_value == pytest.approx(6000.0)

        eth_trade = next(t for t in trades if t.coin == "ETH")
        assert eth_trade.action == TradeAction.OPEN
        assert eth_trade.target_usd_value == pytest.approx(4000.0)

    def test_calculate_trades_close_positions(self, service):
        """Test calculating trades to close all positions."""
        # Current: 100% BTC
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "10000.0"}}
        ]

        # Target: 100% ETH (close BTC, open ETH)
        target_weights = {"ETH": 100.0}
        trades = service.calculate_required_trades(target_weights)

        btc_trade = next(t for t in trades if t.coin == "BTC")
        assert btc_trade.action == TradeAction.CLOSE
        assert btc_trade.current_allocation_pct == pytest.approx(100.0)
        assert btc_trade.target_allocation_pct == 0.0

        eth_trade = next(t for t in trades if t.coin == "ETH")
        assert eth_trade.action == TradeAction.OPEN

    def test_calculate_trades_rebalance_existing(self, service):
        """Test rebalancing existing positions."""
        # Current: 80% BTC, 20% ETH
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "8000.0"}},
            {"position": {"coin": "ETH", "position_value": "2000.0"}},
        ]

        # Target: 60% BTC, 40% ETH
        target_weights = {"BTC": 60.0, "ETH": 40.0}
        trades = service.calculate_required_trades(target_weights)

        btc_trade = next(t for t in trades if t.coin == "BTC")
        assert btc_trade.action == TradeAction.DECREASE
        assert btc_trade.current_allocation_pct == pytest.approx(80.0)
        assert btc_trade.target_allocation_pct == 60.0
        assert btc_trade.trade_usd_value == pytest.approx(-2000.0)  # Sell $2k

        eth_trade = next(t for t in trades if t.coin == "ETH")
        assert eth_trade.action == TradeAction.INCREASE
        assert eth_trade.trade_usd_value == pytest.approx(2000.0)  # Buy $2k

    def test_calculate_trades_within_tolerance_skipped(self, service):
        """Test trades within tolerance are skipped."""
        # Current: 60.5% BTC, 39.5% ETH
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "6050.0"}},
            {"position": {"coin": "ETH", "position_value": "3950.0"}},
        ]

        # Target: 60% BTC, 40% ETH (diff < 1% tolerance)
        target_weights = {"BTC": 60.0, "ETH": 40.0}
        trades = service.calculate_required_trades(target_weights, tolerance_pct=1.0)

        # Both should be skipped
        assert all(t.action == TradeAction.SKIP for t in trades)

    def test_calculate_trades_min_trade_usd_filter(self, service):
        """Test trades below minimum USD are skipped."""
        # Current: 50.1% BTC, 49.9% ETH
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "5010.0"}},
            {"position": {"coin": "ETH", "position_value": "4990.0"}},
        ]

        # Target: 50% BTC, 50% ETH
        # Diff = $10, but min_trade_usd = 20
        target_weights = {"BTC": 50.0, "ETH": 50.0}
        trades = service.calculate_required_trades(
            target_weights, min_trade_usd=20.0, tolerance_pct=0.0
        )

        # Should be skipped due to min trade size
        assert all(t.action == TradeAction.SKIP for t in trades)

    def test_calculate_trades_zero_total_value_raises(self, service):
        """Test zero total position value raises ValueError."""
        service.position_service.list_positions.return_value = []
        service.account_service.get_account_info.return_value = {
            "margin_summary": {"total_ntl_pos": "0.0"}
        }

        target_weights = {"BTC": 100.0}

        with pytest.raises(ValueError, match="Total position value is 0"):
            service.calculate_required_trades(target_weights)

    def test_calculate_trades_three_way_rebalance(self, service):
        """Test rebalancing across three assets."""
        # Current: 70% BTC, 30% ETH
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "7000.0"}},
            {"position": {"coin": "ETH", "position_value": "3000.0"}},
        ]

        # Target: 50% BTC, 30% ETH, 20% SOL
        target_weights = {"BTC": 50.0, "ETH": 30.0, "SOL": 20.0}
        trades = service.calculate_required_trades(target_weights)

        assert len(trades) == 3

        btc_trade = next(t for t in trades if t.coin == "BTC")
        assert btc_trade.action == TradeAction.DECREASE
        assert btc_trade.trade_usd_value == pytest.approx(-2000.0)

        eth_trade = next(t for t in trades if t.coin == "ETH")
        assert eth_trade.action == TradeAction.SKIP  # Already at 30%

        sol_trade = next(t for t in trades if t.coin == "SOL")
        assert sol_trade.action == TradeAction.OPEN
        assert sol_trade.trade_usd_value == pytest.approx(2000.0)


class TestRebalanceServiceLeverageMethods:
    """Test leverage delegation methods."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return RebalanceService()

    def test_get_position_leverage_delegates(self, service):
        """Test get_position_leverage delegates to leverage_service."""
        with patch("src.services.rebalance_service.leverage_service") as mock_leverage:
            mock_leverage.get_coin_leverage.return_value = 5

            result = service.get_position_leverage("BTC")

            assert result == 5
            mock_leverage.get_coin_leverage.assert_called_once_with("BTC")

    def test_get_position_leverage_returns_none(self, service):
        """Test get_position_leverage returns None for no position."""
        with patch("src.services.rebalance_service.leverage_service") as mock_leverage:
            mock_leverage.get_coin_leverage.return_value = None

            result = service.get_position_leverage("ETH")

            assert result is None

    def test_set_leverage_for_coin_success(self, service):
        """Test set_leverage_for_coin delegates successfully."""
        with patch("src.services.rebalance_service.leverage_service") as mock_leverage:
            mock_leverage.set_coin_leverage.return_value = (
                True,
                "Leverage set successfully",
            )

            result = service.set_leverage_for_coin("BTC", 3)

            assert result is True
            mock_leverage.set_coin_leverage.assert_called_once_with(
                coin="BTC", leverage=3, is_cross=True
            )

    def test_set_leverage_for_coin_failure(self, service):
        """Test set_leverage_for_coin handles failure."""
        with patch("src.services.rebalance_service.leverage_service") as mock_leverage:
            mock_leverage.set_coin_leverage.return_value = (
                False,
                "Position already exists",
            )

            result = service.set_leverage_for_coin("ETH", 5)

            assert result is False

    def test_set_leverage_for_coin_isolated(self, service):
        """Test setting isolated margin leverage."""
        with patch("src.services.rebalance_service.leverage_service") as mock_leverage:
            mock_leverage.set_coin_leverage.return_value = (True, "Success")

            result = service.set_leverage_for_coin("SOL", 10, is_cross=False)

            assert result is True
            mock_leverage.set_coin_leverage.assert_called_once_with(
                coin="SOL", leverage=10, is_cross=False
            )


class TestRebalanceServiceExecuteTrade:
    """Test execute_trade method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies."""
        mock_market_data = Mock()
        mock_market_data.get_price.return_value = 50000.0
        mock_market_data.get_asset_metadata.return_value = {"szDecimals": 4}

        # Use regular Mock for order_service since rebalance_service calls it synchronously
        mock_order = Mock()
        mock_order.place_market_order = Mock()

        return create_service_with_mocks(
            RebalanceService,
            "src.services.rebalance_service",
            {
                "market_data_service": mock_market_data,
                "position_service": ServiceMockBuilder.position_service(),
                "order_service": mock_order,
            },
        )

    def test_execute_trade_skip(self, service):
        """Test executing a SKIP trade."""
        trade = RebalanceTrade(
            coin="BTC",
            action=TradeAction.SKIP,
            current_allocation_pct=50.0,
            target_allocation_pct=50.5,
            diff_pct=0.5,
            current_usd_value=5000.0,
            target_usd_value=5050.0,
            trade_usd_value=50.0,
            trade_size=None,
        )

        service.execute_trade(trade)

        assert trade.executed is True
        assert trade.success is True
        assert trade.trade_size is None  # Not calculated for SKIP

    def test_execute_trade_close(self, service):
        """Test executing a CLOSE trade."""
        service.position_service.close_position.return_value = {
            "status": "success",
            "coin": "BTC",
            "size_closed": 0.1,
        }

        trade = RebalanceTrade(
            coin="BTC",
            action=TradeAction.CLOSE,
            current_allocation_pct=20.0,
            target_allocation_pct=0.0,
            diff_pct=-20.0,
            current_usd_value=2000.0,
            target_usd_value=0.0,
            trade_usd_value=-2000.0,
            trade_size=None,
        )

        service.execute_trade(trade)

        assert trade.executed is True
        assert trade.success is True
        assert trade.trade_size == pytest.approx(0.04)  # $2000 / $50000
        service.position_service.close_position.assert_called_once_with(
            coin="BTC",
            size=None,  # None means close full position
            slippage=0.05,
        )

    def test_execute_trade_open(self, service):
        """Test executing an OPEN trade."""
        service.order_service.place_market_order.return_value = {
            "status": "ok",
            "response": {"type": "order"},
        }

        trade = RebalanceTrade(
            coin="ETH",
            action=TradeAction.OPEN,
            current_allocation_pct=0.0,
            target_allocation_pct=30.0,
            diff_pct=30.0,
            current_usd_value=0.0,
            target_usd_value=3000.0,
            trade_usd_value=3000.0,
            trade_size=None,
        )

        service.execute_trade(trade)

        assert trade.executed is True
        assert trade.success is True
        assert trade.trade_size == pytest.approx(0.06)  # $3000 / $50000
        service.order_service.place_market_order.assert_called_once_with(
            coin="ETH", is_buy=True, size=pytest.approx(0.06), slippage=0.05
        )

    def test_execute_trade_increase(self, service):
        """Test executing an INCREASE trade."""
        service.order_service.place_market_order.return_value = {"status": "ok"}

        trade = RebalanceTrade(
            coin="BTC",
            action=TradeAction.INCREASE,
            current_allocation_pct=40.0,
            target_allocation_pct=60.0,
            diff_pct=20.0,
            current_usd_value=4000.0,
            target_usd_value=6000.0,
            trade_usd_value=2000.0,
            trade_size=None,
        )

        service.execute_trade(trade)

        assert trade.success is True
        assert trade.trade_size == pytest.approx(0.04)
        service.order_service.place_market_order.assert_called_once_with(
            coin="BTC", is_buy=True, size=pytest.approx(0.04), slippage=0.05
        )

    def test_execute_trade_decrease(self, service):
        """Test executing a DECREASE trade."""
        service.order_service.place_market_order.return_value = {"status": "ok"}

        trade = RebalanceTrade(
            coin="SOL",
            action=TradeAction.DECREASE,
            current_allocation_pct=30.0,
            target_allocation_pct=10.0,
            diff_pct=-20.0,
            current_usd_value=3000.0,
            target_usd_value=1000.0,
            trade_usd_value=-2000.0,
            trade_size=None,
        )

        service.execute_trade(trade)

        assert trade.success is True
        assert trade.trade_size == pytest.approx(0.04)
        service.order_service.place_market_order.assert_called_once_with(
            coin="SOL",
            is_buy=False,  # Sell to decrease
            size=pytest.approx(0.04),
            slippage=0.05,
        )

    def test_execute_trade_with_leverage_setting(self, service):
        """Test OPEN trade sets leverage before placing order."""
        service.order_service.place_market_order.return_value = {"status": "ok"}

        trade = RebalanceTrade(
            coin="BTC",
            action=TradeAction.OPEN,
            current_allocation_pct=0.0,
            target_allocation_pct=50.0,
            diff_pct=50.0,
            current_usd_value=0.0,
            target_usd_value=5000.0,
            trade_usd_value=5000.0,
            trade_size=None,
            target_leverage=3,
        )

        with patch.object(service, "set_leverage_for_coin") as mock_set_leverage:
            mock_set_leverage.return_value = True

            service.execute_trade(trade)

            mock_set_leverage.assert_called_once_with("BTC", 3)
            assert trade.success is True

    def test_execute_trade_handles_exception(self, service):
        """Test execute_trade handles exceptions gracefully."""
        service.order_service.place_market_order.side_effect = Exception("Network error")

        trade = RebalanceTrade(
            coin="ETH",
            action=TradeAction.OPEN,
            current_allocation_pct=0.0,
            target_allocation_pct=30.0,
            diff_pct=30.0,
            current_usd_value=0.0,
            target_usd_value=3000.0,
            trade_usd_value=3000.0,
            trade_size=None,
        )

        service.execute_trade(trade)

        assert trade.executed is True
        assert trade.success is False
        assert "Network error" in trade.error

    def test_execute_trade_custom_slippage(self, service):
        """Test execute_trade with custom slippage."""
        service.order_service.place_market_order.return_value = {"status": "ok"}

        trade = RebalanceTrade(
            coin="BTC",
            action=TradeAction.OPEN,
            current_allocation_pct=0.0,
            target_allocation_pct=50.0,
            diff_pct=50.0,
            current_usd_value=0.0,
            target_usd_value=5000.0,
            trade_usd_value=5000.0,
            trade_size=None,
        )

        service.execute_trade(trade, slippage=0.10)

        service.order_service.place_market_order.assert_called_once()
        assert service.order_service.place_market_order.call_args[1]["slippage"] == 0.10


class TestRebalanceServicePreview:
    """Test preview_rebalance method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies."""
        mock_account = Mock()
        mock_account.get_account_info.return_value = {
            "margin_summary": {"total_ntl_pos": "10000.0"}
        }

        mock_market_data = Mock()
        mock_market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
        }

        return create_service_with_mocks(
            RebalanceService,
            "src.services.rebalance_service",
            {
                "position_service": ServiceMockBuilder.position_service(),
                "account_service": mock_account,
                "market_data_service": mock_market_data,
            },
        )

    def test_preview_rebalance_success(self, service):
        """Test preview_rebalance returns correct structure."""
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "8000.0"}},
            {"position": {"coin": "ETH", "position_value": "2000.0"}},
        ]

        target_weights = {"BTC": 60.0, "ETH": 40.0}
        result = service.preview_rebalance(target_weights)

        assert result.success is True
        assert "Preview" in result.message
        assert len(result.planned_trades) == 2
        assert result.executed_trades == 0
        assert result.successful_trades == 0
        assert result.failed_trades == 0
        assert result.initial_allocation == {"BTC": 80.0, "ETH": 20.0}
        assert result.final_allocation == target_weights

    def test_preview_rebalance_counts_actionable_trades(self, service):
        """Test preview counts actionable vs skipped trades."""
        # Current: 50% BTC, 50% ETH
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "5000.0"}},
            {"position": {"coin": "ETH", "position_value": "5000.0"}},
        ]

        # Target: 50.5% BTC, 49.5% ETH (within tolerance)
        target_weights = {"BTC": 50.5, "ETH": 49.5}
        result = service.preview_rebalance(target_weights)

        assert result.success is True
        assert result.skipped_trades == 2  # Both within tolerance
        assert "0 trades planned" in result.message  # No actionable trades

    def test_preview_rebalance_with_new_positions(self, service):
        """Test preview with opening new positions."""
        # Current: 100% BTC
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "10000.0"}}
        ]

        # Target: 50% BTC, 30% ETH, 20% SOL
        target_weights = {"BTC": 50.0, "ETH": 30.0, "SOL": 20.0}
        result = service.preview_rebalance(target_weights)

        assert result.success is True
        assert len(result.planned_trades) == 3

        # Check trade actions
        trades_by_coin = {t.coin: t for t in result.planned_trades}
        assert trades_by_coin["BTC"].action == TradeAction.DECREASE
        assert trades_by_coin["ETH"].action == TradeAction.OPEN
        assert trades_by_coin["SOL"].action == TradeAction.OPEN

    def test_preview_rebalance_validation_error(self, service):
        """Test preview handles validation errors."""
        service.position_service.list_positions.return_value = []

        # Invalid: weights don't sum to 100%
        target_weights = {"BTC": 60.0, "ETH": 30.0}  # Only 90%

        result = service.preview_rebalance(target_weights)

        assert result.success is False
        assert "failed" in result.message.lower()
        assert len(result.errors) > 0
        assert "100%" in result.errors[0]

    def test_preview_rebalance_with_custom_params(self, service):
        """Test preview with custom leverage and min_trade_usd."""
        service.position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "10000.0"}}
        ]

        target_weights = {"BTC": 80.0, "ETH": 20.0}
        result = service.preview_rebalance(target_weights, leverage=5, min_trade_usd=100.0)

        assert result.success is True
        assert len(result.planned_trades) == 2


class TestRebalanceServiceSingleton:
    """Test global service singleton."""

    def test_singleton_instance_exists(self):
        """Test global service instance is available."""
        assert rebalance_service is not None
        assert isinstance(rebalance_service, RebalanceService)

    def test_singleton_has_dependencies(self):
        """Test singleton has all required dependencies."""
        assert hasattr(rebalance_service, "position_service")
        assert hasattr(rebalance_service, "account_service")
        assert hasattr(rebalance_service, "order_service")
        assert hasattr(rebalance_service, "market_data_service")
        assert hasattr(rebalance_service, "risk_calculator")
