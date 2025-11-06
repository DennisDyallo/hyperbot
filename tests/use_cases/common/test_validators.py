"""
Unit tests for validators utility.

Tests centralized validation logic for orders and portfolios.
"""
import pytest
from src.use_cases.common.validators import (
    ValidationError,
    OrderValidator,
    PortfolioValidator,
)


class TestOrderValidator:
    """Test OrderValidator class."""

    def test_validate_positive_amount_success(self):
        """Test validating positive amounts."""
        OrderValidator.validate_positive_amount(100.0, "Test amount")
        OrderValidator.validate_positive_amount(0.001, "Small amount")

    def test_validate_positive_amount_zero_fails(self):
        """Test zero amount fails validation."""
        with pytest.raises(ValidationError, match="Amount must be greater than 0"):
            OrderValidator.validate_positive_amount(0.0, "Amount")

    def test_validate_positive_amount_negative_fails(self):
        """Test negative amount fails validation."""
        with pytest.raises(ValidationError, match="Amount must be greater than 0"):
            OrderValidator.validate_positive_amount(-10.0, "Amount")

    def test_validate_size_success(self):
        """Test size validation success."""
        OrderValidator.validate_size(0.01, "BTC")
        OrderValidator.validate_size(1.0, "ETH")

    def test_validate_size_with_min_size(self):
        """Test size validation with minimum size."""
        OrderValidator.validate_size(0.01, "BTC", min_size=0.001)

    def test_validate_size_below_minimum_fails(self):
        """Test size below minimum fails."""
        with pytest.raises(ValidationError, match="below minimum"):
            OrderValidator.validate_size(0.0005, "BTC", min_size=0.001)

    def test_validate_price_success(self):
        """Test price validation success."""
        OrderValidator.validate_price(50000.0, "BTC")
        OrderValidator.validate_price(1000.50, "ETH")

    def test_validate_price_with_tick_size(self):
        """Test price validation with tick size."""
        OrderValidator.validate_price(50000.0, "BTC", tick_size=1.0)
        OrderValidator.validate_price(1000.5, "ETH", tick_size=0.5)

    def test_validate_price_not_divisible_by_tick_fails(self):
        """Test price not divisible by tick size fails."""
        with pytest.raises(ValidationError, match="not divisible by tick size"):
            OrderValidator.validate_price(50001.5, "BTC", tick_size=1.0)

    def test_validate_leverage_low_risk(self):
        """Test leverage validation for low risk (1-3x)."""
        result = OrderValidator.validate_leverage(3, "BTC")
        assert result["valid"] is True
        assert result["risk_level"] == "LOW"
        assert len(result["warnings"]) == 0

    def test_validate_leverage_moderate_risk(self):
        """Test leverage validation for moderate risk (4-5x)."""
        result = OrderValidator.validate_leverage(5, "BTC")
        assert result["valid"] is True
        assert result["risk_level"] == "MODERATE"
        assert len(result["warnings"]) > 0

    def test_validate_leverage_high_risk(self):
        """Test leverage validation for high risk (6-10x)."""
        result = OrderValidator.validate_leverage(8, "BTC")
        assert result["valid"] is True
        assert result["risk_level"] == "HIGH"
        assert len(result["warnings"]) > 0

    def test_validate_leverage_extreme_risk(self):
        """Test leverage validation for extreme risk (>10x)."""
        result = OrderValidator.validate_leverage(15, "BTC")
        assert result["valid"] is True
        assert result["risk_level"] == "EXTREME"
        assert len(result["warnings"]) > 0
        assert "extremely high" in result["warnings"][0].lower()

    def test_validate_leverage_below_minimum_fails(self):
        """Test leverage below 1x fails."""
        with pytest.raises(ValidationError, match="at least 1x"):
            OrderValidator.validate_leverage(0, "BTC")

    def test_validate_leverage_above_maximum_fails(self):
        """Test leverage above 50x fails."""
        with pytest.raises(ValidationError, match="cannot exceed 50x"):
            OrderValidator.validate_leverage(51, "BTC")

    def test_validate_coin_symbol_success(self):
        """Test coin symbol validation success."""
        OrderValidator.validate_coin_symbol("BTC")
        OrderValidator.validate_coin_symbol("ETH")
        OrderValidator.validate_coin_symbol("  SOL  ")  # With whitespace

    def test_validate_coin_symbol_with_valid_list(self):
        """Test coin symbol validation with valid list."""
        OrderValidator.validate_coin_symbol("BTC", ["BTC", "ETH", "SOL"])

    def test_validate_coin_symbol_not_in_valid_list_fails(self):
        """Test coin symbol not in valid list fails."""
        with pytest.raises(ValidationError, match="Invalid coin symbol"):
            OrderValidator.validate_coin_symbol("INVALID", ["BTC", "ETH"])

    def test_validate_coin_symbol_empty_fails(self):
        """Test empty coin symbol fails."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            OrderValidator.validate_coin_symbol("")

    def test_validate_percentage_success(self):
        """Test percentage validation success."""
        OrderValidator.validate_percentage(0.0)
        OrderValidator.validate_percentage(50.0)
        OrderValidator.validate_percentage(100.0)

    def test_validate_percentage_out_of_range_fails(self):
        """Test percentage out of range fails."""
        with pytest.raises(ValidationError, match="must be between 0 and 100"):
            OrderValidator.validate_percentage(150.0)

        with pytest.raises(ValidationError, match="must be between 0 and 100"):
            OrderValidator.validate_percentage(-10.0)

    def test_validate_slippage_success(self):
        """Test slippage validation success."""
        OrderValidator.validate_slippage(5.0)
        OrderValidator.validate_slippage(2.0)

    def test_validate_slippage_invalid_fails(self):
        """Test invalid slippage fails."""
        with pytest.raises(ValidationError, match="must be between 0 and 100"):
            OrderValidator.validate_slippage(150.0)

    def test_validate_order_count_success(self):
        """Test order count validation success."""
        OrderValidator.validate_order_count(5)
        OrderValidator.validate_order_count(1)
        OrderValidator.validate_order_count(20)

    def test_validate_order_count_out_of_range_fails(self):
        """Test order count out of range fails."""
        with pytest.raises(ValidationError, match="must be between"):
            OrderValidator.validate_order_count(0)

        with pytest.raises(ValidationError, match="must be between"):
            OrderValidator.validate_order_count(50)


class TestPortfolioValidator:
    """Test PortfolioValidator class."""

    def test_validate_weights_success(self):
        """Test weights validation success."""
        PortfolioValidator.validate_weights({"BTC": 50.0, "ETH": 50.0})
        PortfolioValidator.validate_weights({"BTC": 33.33, "ETH": 33.33, "SOL": 33.34})

    def test_validate_weights_sum_not_100_fails(self):
        """Test weights not summing to 100% fails."""
        with pytest.raises(ValidationError, match="must sum to 100%"):
            PortfolioValidator.validate_weights({"BTC": 40.0, "ETH": 50.0})

    def test_validate_weights_empty_fails(self):
        """Test empty weights fails."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            PortfolioValidator.validate_weights({})

    def test_validate_weights_negative_fails(self):
        """Test negative weight fails."""
        # Sum is 100%, no weight >100%, but SOL is negative
        with pytest.raises(ValidationError, match="cannot be negative"):
            PortfolioValidator.validate_weights({"BTC": 60.0, "ETH": 50.0, "SOL": -10.0})

    def test_validate_weights_over_100_fails(self):
        """Test individual weight over 100% fails."""
        # Sum is 100%, but BTC weight exceeds 100%
        with pytest.raises(ValidationError, match="cannot exceed 100%"):
            PortfolioValidator.validate_weights({"BTC": 150.0, "ETH": -50.0})

    def test_validate_margin_ratio_safe(self):
        """Test safe margin ratio."""
        result = PortfolioValidator.validate_margin_ratio(10.0)
        assert result["safe"] is True
        assert result["risk_level"] == "SAFE"
        assert len(result["warnings"]) == 0

    def test_validate_margin_ratio_low_risk(self):
        """Test low risk margin ratio (30-50%)."""
        result = PortfolioValidator.validate_margin_ratio(40.0)
        assert result["safe"] is True
        assert result["risk_level"] == "LOW"

    def test_validate_margin_ratio_moderate_risk(self):
        """Test moderate risk margin ratio (50-70%)."""
        result = PortfolioValidator.validate_margin_ratio(60.0)
        assert result["safe"] is True
        assert result["risk_level"] == "MODERATE"
        assert len(result["warnings"]) > 0

    def test_validate_margin_ratio_high_risk(self):
        """Test high risk margin ratio (70-90%)."""
        result = PortfolioValidator.validate_margin_ratio(80.0)
        assert result["safe"] is False
        assert result["risk_level"] == "HIGH"
        assert len(result["warnings"]) > 0

    def test_validate_margin_ratio_critical_risk(self):
        """Test critical risk margin ratio (>=90%)."""
        result = PortfolioValidator.validate_margin_ratio(95.0)
        assert result["safe"] is False
        assert result["risk_level"] == "CRITICAL"
        assert len(result["warnings"]) > 0
        assert "critical" in result["warnings"][0].lower()

    # ===================================================================
    # Additional edge case tests
    # ===================================================================

    def test_validate_positive_amount_custom_field_name(self):
        """Test custom field name appears in error message."""
        with pytest.raises(ValidationError, match="Price"):
            OrderValidator.validate_positive_amount(0.0, "Price")

    def test_validate_size_zero_fails(self):
        """Test zero size fails validation."""
        with pytest.raises(ValidationError, match="Order size must be greater than 0"):
            OrderValidator.validate_size(0.0, "BTC")

    def test_validate_size_negative_fails(self):
        """Test negative size fails validation."""
        with pytest.raises(ValidationError, match="Order size must be greater than 0"):
            OrderValidator.validate_size(-0.5, "BTC")

    def test_validate_price_zero_fails(self):
        """Test zero price fails validation."""
        with pytest.raises(ValidationError, match="Price must be greater than 0"):
            OrderValidator.validate_price(0.0, "BTC")

    def test_validate_price_negative_fails(self):
        """Test negative price fails validation."""
        with pytest.raises(ValidationError, match="Price must be greater than 0"):
            OrderValidator.validate_price(-100.0, "BTC")

    def test_validate_leverage_without_coin(self):
        """Test leverage validation without coin symbol."""
        result = OrderValidator.validate_leverage(3)
        assert result["valid"] is True
        assert result["risk_level"] == "LOW"

    def test_validate_leverage_boundary_1x(self):
        """Test leverage at minimum boundary (1x)."""
        result = OrderValidator.validate_leverage(1)
        assert result["valid"] is True

    def test_validate_leverage_boundary_50x(self):
        """Test leverage at maximum boundary (50x)."""
        result = OrderValidator.validate_leverage(50)
        assert result["valid"] is True
        assert result["risk_level"] == "EXTREME"

    def test_validate_coin_symbol_whitespace_only_fails(self):
        """Test whitespace-only coin symbol fails."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            OrderValidator.validate_coin_symbol("   ")

    def test_validate_coin_symbol_case_insensitive(self):
        """Test coin symbol validation is case-insensitive."""
        # Should normalize to uppercase
        OrderValidator.validate_coin_symbol("btc", ["BTC", "ETH"])
        OrderValidator.validate_coin_symbol("BtC", ["BTC", "ETH"])

    def test_validate_percentage_boundary_0(self):
        """Test percentage at 0% boundary."""
        OrderValidator.validate_percentage(0.0)

    def test_validate_percentage_boundary_100(self):
        """Test percentage at 100% boundary."""
        OrderValidator.validate_percentage(100.0)

    def test_validate_percentage_custom_field_name(self):
        """Test custom field name in percentage error."""
        with pytest.raises(ValidationError, match="Weight"):
            OrderValidator.validate_percentage(150.0, "Weight")

    def test_validate_slippage_high_warning(self):
        """Test high slippage (>10%) logs warning but doesn't fail."""
        # Should not raise, but should log warning
        OrderValidator.validate_slippage(15.0)

    def test_validate_slippage_zero(self):
        """Test zero slippage is valid."""
        OrderValidator.validate_slippage(0.0)

    def test_validate_order_count_custom_range(self):
        """Test order count with custom min/max."""
        OrderValidator.validate_order_count(5, min_count=2, max_count=10)

    def test_validate_order_count_custom_range_below_min_fails(self):
        """Test order count below custom minimum fails."""
        with pytest.raises(ValidationError, match="must be between 2 and 10"):
            OrderValidator.validate_order_count(1, min_count=2, max_count=10)

    def test_validate_order_count_custom_range_above_max_fails(self):
        """Test order count above custom maximum fails."""
        with pytest.raises(ValidationError, match="must be between 2 and 10"):
            OrderValidator.validate_order_count(11, min_count=2, max_count=10)

    def test_validate_weights_single_asset(self):
        """Test weights validation with single asset at 100%."""
        PortfolioValidator.validate_weights({"BTC": 100.0})

    def test_validate_weights_floating_point_tolerance(self):
        """Test weights validation allows small floating point errors."""
        # Should pass due to 0.01% tolerance (33.33 + 33.33 + 33.34 = 100.00)
        PortfolioValidator.validate_weights({"BTC": 33.33, "ETH": 33.33, "SOL": 33.34})

    def test_validate_margin_ratio_boundary_30(self):
        """Test margin ratio at 30% boundary (SAFE/LOW)."""
        result = PortfolioValidator.validate_margin_ratio(30.0)
        assert result["risk_level"] == "LOW"

    def test_validate_margin_ratio_boundary_50(self):
        """Test margin ratio at 50% boundary (LOW/MODERATE)."""
        result = PortfolioValidator.validate_margin_ratio(50.0)
        assert result["risk_level"] == "MODERATE"

    def test_validate_margin_ratio_boundary_70(self):
        """Test margin ratio at 70% boundary (MODERATE/HIGH)."""
        result = PortfolioValidator.validate_margin_ratio(70.0)
        assert result["risk_level"] == "HIGH"
        assert result["safe"] is False

    def test_validate_margin_ratio_boundary_90(self):
        """Test margin ratio at 90% boundary (HIGH/CRITICAL)."""
        result = PortfolioValidator.validate_margin_ratio(90.0)
        assert result["risk_level"] == "CRITICAL"
        assert result["safe"] is False

    def test_validate_margin_ratio_zero(self):
        """Test margin ratio at 0% (no margin used)."""
        result = PortfolioValidator.validate_margin_ratio(0.0)
        assert result["safe"] is True
        assert result["risk_level"] == "SAFE"
        assert len(result["warnings"]) == 0

    def test_validate_price_tick_size_exact_multiple(self):
        """Test price that is exact multiple of tick size."""
        OrderValidator.validate_price(100.0, "BTC", tick_size=10.0)
        OrderValidator.validate_price(1000.0, "BTC", tick_size=100.0)

    def test_validate_price_tick_size_floating_point_tolerance(self):
        """Test price validation tolerates floating point errors."""
        # Price very close to tick size multiple (within 1e-10 tolerance)
        OrderValidator.validate_price(100.00000000001, "BTC", tick_size=1.0)
