"""
Unit tests for RebalanceService.

Tests portfolio rebalancing logic, validation, and risk management.
CRITICAL - bugs here = incorrect portfolio allocation, liquidation risk.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.rebalance_service import (
    RebalanceService,
    TradeAction,
    RebalanceTrade,
    rebalance_service
)
from src.services.risk_calculator import RiskLevel


class TestRebalanceServiceValidation:
    """Test validate_target_weights method."""

    @pytest.fixture
    def mock_market_data(self):
        """Mock market data service."""
        mock = Mock()
        mock.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0
        }
        return mock

    @pytest.fixture
    def service(self, mock_market_data):
        """Create service with mocked dependencies."""
        with patch('src.services.rebalance_service.market_data_service', mock_market_data):
            svc = RebalanceService()
            svc.market_data_service = mock_market_data
            return svc

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

    def test_validate_invalid_coin_raises(self, service, mock_market_data):
        """Test invalid coin symbol raises ValueError."""
        target_weights = {"INVALID": 50.0, "BTC": 50.0}

        with pytest.raises(ValueError, match="Invalid coin 'INVALID'"):
            service.validate_target_weights(target_weights)

    def test_validate_market_data_failure_raises(self, service, mock_market_data):
        """Test market data fetch failure raises ValueError."""
        mock_market_data.get_all_prices.side_effect = Exception("API error")
        target_weights = {"BTC": 50.0, "ETH": 50.0}

        with pytest.raises(ValueError, match="Failed to validate coins"):
            service.validate_target_weights(target_weights)


class TestRebalanceServiceCurrentAllocation:
    """Test calculate_current_allocation method."""

    @pytest.fixture
    def mock_position_service(self):
        """Mock position service."""
        return Mock()

    @pytest.fixture
    def service(self, mock_position_service):
        """Create service with mocked position service."""
        with patch('src.services.rebalance_service.position_service', mock_position_service):
            svc = RebalanceService()
            svc.position_service = mock_position_service
            return svc

    def test_calculate_allocation_no_positions(self, service, mock_position_service):
        """Test allocation with no positions returns empty dict."""
        mock_position_service.list_positions.return_value = []

        allocation = service.calculate_current_allocation()

        assert allocation == {}

    def test_calculate_allocation_single_position(self, service, mock_position_service):
        """Test allocation with single position."""
        mock_position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "10000.0"}}
        ]

        allocation = service.calculate_current_allocation()

        assert allocation == {"BTC": 100.0}

    def test_calculate_allocation_multiple_positions(self, service, mock_position_service):
        """Test allocation with multiple positions."""
        mock_position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "6000.0"}},
            {"position": {"coin": "ETH", "position_value": "4000.0"}}
        ]

        allocation = service.calculate_current_allocation()

        assert allocation["BTC"] == pytest.approx(60.0)
        assert allocation["ETH"] == pytest.approx(40.0)

    def test_calculate_allocation_handles_negative_values(self, service, mock_position_service):
        """Test allocation uses absolute values (short positions)."""
        mock_position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "-6000.0"}},  # Short
            {"position": {"coin": "ETH", "position_value": "4000.0"}}   # Long
        ]

        allocation = service.calculate_current_allocation()

        # Should use absolute values
        assert allocation["BTC"] == pytest.approx(60.0)
        assert allocation["ETH"] == pytest.approx(40.0)

    def test_calculate_allocation_zero_total_value(self, service, mock_position_service):
        """Test allocation when total value is zero."""
        mock_position_service.list_positions.return_value = [
            {"position": {"coin": "BTC", "position_value": "0.0"}}
        ]

        allocation = service.calculate_current_allocation()

        assert allocation == {}


# TODO: Add tests for calculate_required_trades
# This method has complex dependencies (account_service, market_data_service)
# and calculates total_value internally from account info.
# Requires more complex mocking setup. Covered by use case tests for now.


# TODO: Add tests for leverage management methods
# get_position_leverage() and set_leverage_for_coin() delegate to leverage_service
# Requires complex mocking of leverage_service singleton. Test via use cases for now.


class TestRebalanceServiceSingleton:
    """Test global service singleton."""

    def test_singleton_instance_exists(self):
        """Test global service instance is available."""
        assert rebalance_service is not None
        assert isinstance(rebalance_service, RebalanceService)

    def test_singleton_has_dependencies(self):
        """Test singleton has all required dependencies."""
        assert hasattr(rebalance_service, 'position_service')
        assert hasattr(rebalance_service, 'account_service')
        assert hasattr(rebalance_service, 'order_service')
        assert hasattr(rebalance_service, 'market_data_service')
        assert hasattr(rebalance_service, 'risk_calculator')
