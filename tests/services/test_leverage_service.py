"""
Unit tests for LeverageService.

Tests leverage management, validation, and liquidation price estimation.
"""
import pytest
from unittest.mock import Mock
from src.services.leverage_service import LeverageService, LeverageValidation, LiquidationEstimate, LeverageSetting
from tests.helpers.service_mocks import create_service_with_mocks, ServiceMockBuilder


class TestLeverageService:
    """Test LeverageService methods."""

    @pytest.fixture
    def service(self):
        """Create LeverageService instance with mocked dependencies."""
        mock_hyperliquid = ServiceMockBuilder.hyperliquid_service()
        mock_hyperliquid.is_initialized.return_value = True

        return create_service_with_mocks(
            LeverageService,
            'src.services.leverage_service',
            {
                'hyperliquid_service': mock_hyperliquid,
                'position_service': ServiceMockBuilder.position_service()
            }
        )

    # ===================================================================
    # get_coin_leverage() tests
    # ===================================================================

    def test_get_coin_leverage_with_position(self, service):
        """Test getting leverage for coin with open position."""
        service.position_service.list_positions.return_value = [
            {
                "position": {
                    "coin": "BTC",
                    "leverage_value": 3
                }
            }
        ]

        leverage = service.get_coin_leverage("BTC")

        assert leverage == 3

    def test_get_coin_leverage_no_position(self, service):
        """Test getting leverage for coin without position returns None."""
        service.position_service.list_positions.return_value = []

        leverage = service.get_coin_leverage("BTC")

        assert leverage is None

    # ===================================================================
    # validate_leverage() tests
    # ===================================================================

    def test_validate_leverage_within_soft_limit(self, service):
        """Test validation for leverage within soft limit (≤5x)."""
        service.position_service.list_positions.return_value = []

        result = service.validate_leverage(3)

        assert result.is_valid is True
        assert result.warning_level.value == "OK"
        assert result.can_proceed is True
        assert "recommended" in result.message.lower()

    def test_validate_leverage_high_warning(self, service):
        """Test validation for high leverage (6-10x) shows warning."""
        service.position_service.list_positions.return_value = []

        result = service.validate_leverage(7)

        assert result.is_valid is True
        assert result.warning_level.value == "HIGH"
        assert result.can_proceed is True
        assert "moderate risk" in result.message.lower() or "high" in result.message.lower()

    def test_validate_leverage_extreme_warning(self, service):
        """Test validation for extreme leverage (>10x) shows strong warning."""
        service.position_service.list_positions.return_value = []

        result = service.validate_leverage(15)

        assert result.is_valid is True
        assert result.warning_level.value == "EXTREME"
        assert result.can_proceed is True
        assert "extreme" in result.message.lower() or "very high" in result.message.lower()

    def test_validate_leverage_with_existing_position(self, service):
        """
        Test validation detects existing position.

        Note: validate_leverage validates the leverage VALUE itself.
        The caller (set_coin_leverage) is responsible for checking
        has_open_position and enforcing the constraint.
        """
        service.position_service.list_positions.return_value = [
            {
                "position": {
                    "coin": "BTC",
                    "leverage_value": 3
                }
            }
        ]

        result = service.validate_leverage(5, coin="BTC")

        # Leverage value itself is valid
        assert result.is_valid is True
        # But validation reports existing position for caller to check
        assert result.current_leverage == 3
        assert result.has_open_position is True

    # ===================================================================
    # set_coin_leverage() tests
    # ===================================================================

    def test_set_coin_leverage_success(self, service):
        """Test successfully setting leverage when no position exists."""
        service.position_service.list_positions.return_value = []
        mock_exchange = Mock()
        mock_exchange.update_leverage.return_value = {"status": "ok"}
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        success, message = service.set_coin_leverage("BTC", 3)

        assert success is True
        assert "leverage set" in message.lower()
        mock_exchange.update_leverage.assert_called_once()

    def test_set_coin_leverage_fails_with_existing_position(self, service):
        """Test setting leverage fails when position already exists."""
        service.position_service.list_positions.return_value = [
            {
                "position": {
                    "coin": "BTC",
                    "leverage_value": 2
                }
            }
        ]

        success, message = service.set_coin_leverage("BTC", 5)

        assert success is False
        assert "cannot" in message.lower() or "exists" in message.lower()

    def test_set_coin_leverage_handles_api_error(self, service):
        """Test setting leverage handles API errors gracefully."""
        service.position_service.list_positions.return_value = []
        mock_exchange = Mock()
        mock_exchange.update_leverage.side_effect = Exception("API Error")
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        success, message = service.set_coin_leverage("BTC", 3)

        assert success is False
        assert "failed" in message.lower() or "error" in message.lower()

    # ===================================================================
    # estimate_liquidation_price() tests
    # ===================================================================

    def test_estimate_liquidation_price_long(self, service):
        """Test liquidation price estimation for long position."""
        result = service.estimate_liquidation_price(
            coin="BTC",
            entry_price=100000.0,
            size=1.0,
            leverage=3,
            is_long=True
        )

        assert result.coin == "BTC"
        assert result.entry_price == 100000.0
        assert result.leverage == 3
        assert result.is_long is True
        # Long liquidation price should be below entry price
        assert result.estimated_liquidation_price < 100000.0
        # Should be around 71,667 based on actual formula
        assert 70000 < result.estimated_liquidation_price < 73000

    def test_estimate_liquidation_price_short(self, service):
        """Test liquidation price estimation for short position."""
        result = service.estimate_liquidation_price(
            coin="BTC",
            entry_price=100000.0,
            size=1.0,
            leverage=3,
            is_long=False
        )

        assert result.coin == "BTC"
        assert result.is_long is False
        # Short liquidation price should be above entry price
        assert result.estimated_liquidation_price > 100000.0
        # Should be around 128,333 (100000 * (1 + 1/3 - 0.05))
        assert 125000 < result.estimated_liquidation_price < 132000

    def test_estimate_liquidation_price_high_leverage(self, service):
        """Test liquidation price estimation with high leverage."""
        result = service.estimate_liquidation_price(
            coin="ETH",
            entry_price=4000.0,
            size=10.0,
            leverage=10,
            is_long=True
        )

        # With 10x leverage, liquidation is much closer to entry
        # Distance should be about 5% based on actual formula
        distance_pct = abs(result.liquidation_distance_pct)
        assert 4 < distance_pct < 7  # Should be around 5%
        assert result.risk_level in ["HIGH", "EXTREME"]

    def test_estimate_liquidation_calculates_position_value(self, service):
        """Test that position value and margin are calculated correctly."""
        result = service.estimate_liquidation_price(
            coin="SOL",
            entry_price=200.0,
            size=100.0,
            leverage=5,
            is_long=True
        )

        expected_position_value = 200.0 * 100.0  # 20,000
        expected_margin = expected_position_value / 5  # 4,000

        assert result.position_value == pytest.approx(expected_position_value, abs=0.01)
        assert result.margin_required == pytest.approx(expected_margin, abs=0.01)

    # ===================================================================
    # get_all_leverage_settings() tests
    # ===================================================================

    def test_get_all_leverage_settings(self, service):
        """Test getting leverage settings for all positions."""
        service.position_service.list_positions.return_value = [
            {
                "position": {
                    "coin": "BTC",
                    "leverage": {"value": 3, "type": "cross"},
                    "position_value": 10000.0
                }
            },
            {
                "position": {
                    "coin": "ETH",
                    "leverage": {"value": 5, "type": "isolated"},
                    "position_value": 5000.0
                }
            }
        ]

        settings = service.get_all_leverage_settings()

        assert len(settings) == 2
        assert settings[0].coin == "BTC"
        assert settings[0].leverage == 3
        assert settings[0].leverage_type == "cross"
        assert settings[0].can_change is False  # Has position
        assert settings[1].coin == "ETH"
        assert settings[1].leverage == 5

    def test_get_all_leverage_settings_no_positions(self, service):
        """Test getting leverage settings when no positions exist."""
        service.position_service.list_positions.return_value = []

        settings = service.get_all_leverage_settings()

        assert len(settings) == 0

    # ===================================================================
    # get_leverage_for_order() tests
    # ===================================================================

    def test_get_leverage_for_order_with_position(self, service):
        """Test getting leverage for order when position exists."""
        service.position_service.list_positions.return_value = [
            {
                "position": {
                    "coin": "BTC",
                    "leverage_value": 4
                }
            }
        ]

        leverage, needs_setting = service.get_leverage_for_order("BTC", default_leverage=3)

        # Should return existing position leverage, no need to set
        assert leverage == 4
        assert needs_setting is False

    def test_get_leverage_for_order_no_position_uses_default(self, service):
        """Test getting leverage for order uses default when no position."""
        service.position_service.list_positions.return_value = []

        leverage, needs_setting = service.get_leverage_for_order("BTC", default_leverage=3)

        # Should return default leverage, needs to be set
        assert leverage == 3
        assert needs_setting is True

    def test_get_leverage_for_order_no_position_no_default(self, service):
        """Test getting leverage for order without position or default."""
        service.position_service.list_positions.return_value = []

        leverage, needs_setting = service.get_leverage_for_order("BTC")

        # Should return settings default (3), needs to be set
        assert leverage == 3
        assert needs_setting is True


class TestLeverageServiceExceptionHandling:
    """Test exception handling in LeverageService methods."""

    @pytest.fixture
    def service(self):
        """Create LeverageService instance with mocked dependencies."""
        mock_hyperliquid = ServiceMockBuilder.hyperliquid_service()
        mock_hyperliquid.is_initialized.return_value = True

        return create_service_with_mocks(
            LeverageService,
            'src.services.leverage_service',
            {
                'hyperliquid_service': mock_hyperliquid,
                'position_service': ServiceMockBuilder.position_service()
            }
        )

    def test_get_coin_leverage_exception_returns_none(self, service):
        """Test get_coin_leverage returns None on exception."""
        service.position_service.list_positions.side_effect = Exception("API error")

        leverage = service.get_coin_leverage("BTC")

        assert leverage is None

    def test_get_all_leverage_settings_exception_returns_empty(self, service):
        """Test get_all_leverage_settings returns empty list on exception."""
        service.position_service.list_positions.side_effect = Exception("API error")

        settings = service.get_all_leverage_settings()

        assert settings == []

    def test_validate_leverage_extreme_value(self, service):
        """Test validation for extremely high leverage values."""
        service.position_service.list_positions.return_value = []

        validation = service.validate_leverage(50)

        assert validation.is_valid is True
        assert validation.warning_level.value == "EXTREME"
        assert "extreme" in validation.message.lower() or "very high" in validation.message.lower()

    def test_estimate_liquidation_price_long_position(self, service):
        """Test liquidation price estimation for long position."""
        estimate = service.estimate_liquidation_price(
            coin="BTC",
            entry_price=100000.0,
            size=1.0,
            leverage=10,
            is_long=True
        )

        assert estimate.coin == "BTC"
        assert estimate.estimated_liquidation_price is not None
        assert estimate.estimated_liquidation_price < 100000.0  # Long liquidates below entry
        assert abs(estimate.liquidation_distance_pct) > 0

    def test_estimate_liquidation_price_short_position(self, service):
        """Test liquidation price estimation for short position."""
        estimate = service.estimate_liquidation_price(
            coin="ETH",
            entry_price=100000.0,
            size=1.0,
            leverage=10,
            is_long=False
        )

        assert estimate.coin == "ETH"
        assert estimate.estimated_liquidation_price is not None
        assert estimate.estimated_liquidation_price > 100000.0  # Short liquidates above entry
        assert abs(estimate.liquidation_distance_pct) > 0

    def test_estimate_liquidation_price_extreme_leverage(self, service):
        """Test liquidation price with extreme leverage."""
        estimate = service.estimate_liquidation_price(
            coin="SOL",
            entry_price=100000.0,
            size=1.0,
            leverage=25,
            is_long=True
        )

        # Extreme leverage should result in EXTREME risk level
        assert estimate.risk_level in ["HIGH", "EXTREME"]

    def test_estimate_liquidation_price_high_leverage_comparison(self, service):
        """Test that higher leverage means closer liquidation price."""
        estimate_5x = service.estimate_liquidation_price(
            coin="BTC",
            entry_price=100000.0,
            size=1.0,
            leverage=5,
            is_long=True
        )

        estimate_20x = service.estimate_liquidation_price(
            coin="BTC",
            entry_price=100000.0,
            size=1.0,
            leverage=20,
            is_long=True
        )

        # Higher leverage means closer to entry price (smaller distance)
        assert abs(estimate_20x.liquidation_distance_pct) < abs(estimate_5x.liquidation_distance_pct)
