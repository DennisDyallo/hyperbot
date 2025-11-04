"""
Unit tests for LeverageService.

Tests leverage management, validation, and liquidation price estimation.
"""
import pytest
from unittest.mock import Mock, patch
from src.services.leverage_service import LeverageService, LeverageValidation, LiquidationEstimate, LeverageSetting


class TestLeverageService:
    """Test LeverageService methods."""

    @pytest.fixture
    def mock_hyperliquid_service(self):
        """Mock HyperliquidService."""
        mock_hl = Mock()
        mock_hl.is_initialized.return_value = True
        return mock_hl

    @pytest.fixture
    def mock_position_service(self):
        """Mock PositionService."""
        return Mock()

    @pytest.fixture
    def service(self, mock_hyperliquid_service, mock_position_service):
        """Create LeverageService instance with mocked dependencies."""
        with patch('src.services.leverage_service.hyperliquid_service', mock_hyperliquid_service):
            with patch('src.services.leverage_service.position_service', mock_position_service):
                svc = LeverageService()
                return svc

    # ===================================================================
    # get_coin_leverage() tests
    # ===================================================================

    def test_get_coin_leverage_with_position(self, service, mock_position_service):
        """Test getting leverage for coin with open position."""
        mock_position_service.list_positions.return_value = [
            {
                "coin": "BTC",
                "leverage_value": 3
            }
        ]

        leverage = service.get_coin_leverage("BTC")

        assert leverage == 3

    def test_get_coin_leverage_no_position(self, service, mock_position_service):
        """Test getting leverage for coin without position returns None."""
        mock_position_service.list_positions.return_value = []

        leverage = service.get_coin_leverage("BTC")

        assert leverage is None

    # ===================================================================
    # validate_leverage() tests
    # ===================================================================

    def test_validate_leverage_within_soft_limit(self, service, mock_position_service):
        """Test validation for leverage within soft limit (≤5x)."""
        mock_position_service.list_positions.return_value = []

        result = service.validate_leverage(3)

        assert result.is_valid is True
        assert result.warning_level.value == "OK"
        assert result.can_proceed is True
        assert "recommended" in result.message.lower()

    def test_validate_leverage_high_warning(self, service, mock_position_service):
        """Test validation for high leverage (6-10x) shows warning."""
        mock_position_service.list_positions.return_value = []

        result = service.validate_leverage(7)

        assert result.is_valid is True
        assert result.warning_level.value == "HIGH"
        assert result.can_proceed is True
        assert "moderate risk" in result.message.lower() or "high" in result.message.lower()

    def test_validate_leverage_extreme_warning(self, service, mock_position_service):
        """Test validation for extreme leverage (>10x) shows strong warning."""
        mock_position_service.list_positions.return_value = []

        result = service.validate_leverage(15)

        assert result.is_valid is True
        assert result.warning_level.value == "EXTREME"
        assert result.can_proceed is True
        assert "extreme" in result.message.lower() or "very high" in result.message.lower()

    def test_validate_leverage_with_existing_position(self, service, mock_position_service):
        """Test validation fails when position already exists."""
        mock_position_service.list_positions.return_value = [
            {
                "coin": "BTC",
                "leverage_value": 3
            }
        ]

        result = service.validate_leverage(5, coin="BTC")

        assert result.is_valid is False
        assert result.can_proceed is False
        assert result.current_leverage == 3
        assert result.has_open_position is True
        assert "cannot change" in result.message.lower() or "already exists" in result.message.lower()

    # ===================================================================
    # set_coin_leverage() tests
    # ===================================================================

    def test_set_coin_leverage_success(self, service, mock_hyperliquid_service, mock_position_service):
        """Test successfully setting leverage when no position exists."""
        mock_position_service.list_positions.return_value = []
        mock_exchange = Mock()
        mock_exchange.update_leverage.return_value = {"status": "ok"}
        mock_hyperliquid_service.get_exchange_client.return_value = mock_exchange

        success, message = service.set_coin_leverage("BTC", 3)

        assert success is True
        assert "success" in message.lower()
        mock_exchange.update_leverage.assert_called_once()

    def test_set_coin_leverage_fails_with_existing_position(self, service, mock_position_service):
        """Test setting leverage fails when position already exists."""
        mock_position_service.list_positions.return_value = [
            {
                "coin": "BTC",
                "leverage_value": 2
            }
        ]

        success, message = service.set_coin_leverage("BTC", 5)

        assert success is False
        assert "cannot" in message.lower() or "exists" in message.lower()

    def test_set_coin_leverage_handles_api_error(self, service, mock_hyperliquid_service, mock_position_service):
        """Test setting leverage handles API errors gracefully."""
        mock_position_service.list_positions.return_value = []
        mock_exchange = Mock()
        mock_exchange.update_leverage.side_effect = Exception("API Error")
        mock_hyperliquid_service.get_exchange_client.return_value = mock_exchange

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
        # Should be around 68,333 (100000 * (1 - 1/3 + 0.05))
        assert 65000 < result.estimated_liquidation_price < 70000

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
        # Distance should be about 15% (1/10 - 0.05 = 0.15 = 15%)
        distance_pct = abs(result.liquidation_distance_pct)
        assert 10 < distance_pct < 20  # Should be around 15%
        assert result.risk_level in ["HIGH", "MODERATE"]

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

    def test_get_all_leverage_settings(self, service, mock_position_service):
        """Test getting leverage settings for all positions."""
        mock_position_service.list_positions.return_value = [
            {
                "coin": "BTC",
                "leverage_value": 3,
                "leverage_type": "cross",
                "position_value": 10000.0
            },
            {
                "coin": "ETH",
                "leverage_value": 5,
                "leverage_type": "isolated",
                "position_value": 5000.0
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

    def test_get_all_leverage_settings_no_positions(self, service, mock_position_service):
        """Test getting leverage settings when no positions exist."""
        mock_position_service.list_positions.return_value = []

        settings = service.get_all_leverage_settings()

        assert len(settings) == 0

    # ===================================================================
    # get_leverage_for_order() tests
    # ===================================================================

    def test_get_leverage_for_order_with_position(self, service, mock_position_service):
        """Test getting leverage for order when position exists."""
        mock_position_service.list_positions.return_value = [
            {
                "coin": "BTC",
                "leverage_value": 4
            }
        ]

        leverage = service.get_leverage_for_order("BTC", default_leverage=3)

        # Should return existing position leverage
        assert leverage == 4

    def test_get_leverage_for_order_no_position_uses_default(self, service, mock_position_service):
        """Test getting leverage for order uses default when no position."""
        mock_position_service.list_positions.return_value = []

        leverage = service.get_leverage_for_order("BTC", default_leverage=3)

        # Should return default leverage
        assert leverage == 3

    def test_get_leverage_for_order_no_position_no_default(self, service, mock_position_service):
        """Test getting leverage for order without position or default."""
        mock_position_service.list_positions.return_value = []

        leverage = service.get_leverage_for_order("BTC")

        # Should return settings default (3)
        assert leverage == 3
