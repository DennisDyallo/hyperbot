"""
Unit tests for USDConverter.

Tests USD/coin conversion and formatting utilities used across API and Bot.
This is critical infrastructure - all conversions flow through here.
"""

from unittest.mock import patch

import pytest

from src.use_cases.common.usd_converter import USDConverter


class TestUSDConverter:
    """Test USDConverter static methods."""

    # ===================================================================
    # parse_usd_amount() tests
    # ===================================================================

    def test_parse_usd_amount_plain_number(self):
        """Test parsing plain number string."""
        assert USDConverter.parse_usd_amount("100") == 100.0
        assert USDConverter.parse_usd_amount("50.25") == 50.25
        assert USDConverter.parse_usd_amount("0.01") == 0.01

    def test_parse_usd_amount_with_dollar_sign(self):
        """Test parsing amount with $ prefix."""
        assert USDConverter.parse_usd_amount("$100") == 100.0
        assert USDConverter.parse_usd_amount("$50.25") == 50.25

    def test_parse_usd_amount_with_whitespace(self):
        """Test parsing amount with surrounding whitespace."""
        assert USDConverter.parse_usd_amount("  100  ") == 100.0
        assert USDConverter.parse_usd_amount("  $50.25  ") == 50.25

    def test_parse_usd_amount_large_amounts(self):
        """Test parsing large amounts."""
        assert USDConverter.parse_usd_amount("1000000") == 1000000.0
        assert USDConverter.parse_usd_amount("$999999.99") == 999999.99

    def test_parse_usd_amount_invalid_raises_error(self):
        """Test that invalid amounts raise ValueError."""
        with pytest.raises(ValueError, match="Invalid amount"):
            USDConverter.parse_usd_amount("abc")

        with pytest.raises(ValueError, match="Invalid amount"):
            USDConverter.parse_usd_amount("$abc")

        with pytest.raises(ValueError, match="Invalid amount"):
            USDConverter.parse_usd_amount("")

    def test_parse_usd_amount_zero_or_negative_raises_error(self):
        """Test that zero or negative amounts raise ValueError."""
        with pytest.raises(ValueError, match="must be greater than 0"):
            USDConverter.parse_usd_amount("0")

        with pytest.raises(ValueError, match="must be greater than 0"):
            USDConverter.parse_usd_amount("-50")

        with pytest.raises(ValueError, match="must be greater than 0"):
            USDConverter.parse_usd_amount("$-100")

    # ===================================================================
    # convert_usd_to_coin() tests
    # ===================================================================

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_usd_to_coin_btc(self, mock_market_service):
        """Test USD to BTC conversion with proper precision."""
        mock_market_service.get_price.return_value = 50000.0
        mock_market_service.get_asset_metadata.return_value = {"name": "BTC", "szDecimals": 5}

        coin_size, price = USDConverter.convert_usd_to_coin(100.0, "BTC")

        # 100 / 50000 = 0.002, rounded to 5 decimals
        assert coin_size == 0.002
        assert price == 50000.0
        mock_market_service.get_price.assert_called_once_with("BTC")

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_usd_to_coin_eth(self, mock_market_service):
        """Test USD to ETH conversion with proper precision."""
        mock_market_service.get_price.return_value = 3000.0
        mock_market_service.get_asset_metadata.return_value = {"name": "ETH", "szDecimals": 4}

        coin_size, price = USDConverter.convert_usd_to_coin(150.0, "ETH")

        # 150 / 3000 = 0.05, rounded to 4 decimals
        assert coin_size == 0.05
        assert price == 3000.0

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_usd_to_coin_sol(self, mock_market_service):
        """Test USD to SOL conversion."""
        mock_market_service.get_price.return_value = 150.0
        mock_market_service.get_asset_metadata.return_value = {"name": "SOL", "szDecimals": 3}

        coin_size, price = USDConverter.convert_usd_to_coin(300.0, "SOL")

        # 300 / 150 = 2.0, rounded to 3 decimals
        assert coin_size == 2.0
        assert price == 150.0

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_usd_to_coin_fallback_to_6_decimals(self, mock_market_service):
        """Test conversion falls back to 6 decimals when metadata unavailable."""
        mock_market_service.get_price.return_value = 100.0
        mock_market_service.get_asset_metadata.return_value = None  # No metadata

        coin_size, price = USDConverter.convert_usd_to_coin(50.0, "UNKNOWN")

        # 50 / 100 = 0.5, rounded to 6 decimals (default)
        assert coin_size == 0.5
        assert price == 100.0

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_usd_to_coin_large_amounts(self, mock_market_service):
        """Test conversion with large USD amounts."""
        mock_market_service.get_price.return_value = 50000.0
        mock_market_service.get_asset_metadata.return_value = {"szDecimals": 5}

        coin_size, price = USDConverter.convert_usd_to_coin(1000000.0, "BTC")

        # 1,000,000 / 50,000 = 20.0 BTC
        assert coin_size == 20.0

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_usd_to_coin_small_amounts(self, mock_market_service):
        """Test conversion with small USD amounts."""
        mock_market_service.get_price.return_value = 50000.0
        mock_market_service.get_asset_metadata.return_value = {"szDecimals": 5}

        coin_size, price = USDConverter.convert_usd_to_coin(1.0, "BTC")

        # 1 / 50000 = 0.00002
        assert coin_size == 0.00002

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_usd_to_coin_invalid_price_raises_error(self, mock_market_service):
        """Test that invalid price raises ValueError."""
        mock_market_service.get_price.return_value = 0.0

        with pytest.raises(ValueError, match="Invalid price"):
            USDConverter.convert_usd_to_coin(100.0, "INVALID")

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_usd_to_coin_negative_price_raises_error(self, mock_market_service):
        """Test that negative price raises ValueError."""
        mock_market_service.get_price.return_value = -100.0

        with pytest.raises(ValueError, match="Invalid price"):
            USDConverter.convert_usd_to_coin(100.0, "INVALID")

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_usd_to_coin_coin_not_found_raises_error(self, mock_market_service):
        """Test that coin not found raises ValueError."""
        mock_market_service.get_price.side_effect = ValueError("Coin 'NOTFOUND' not found")

        with pytest.raises(ValueError, match="Failed to get price"):
            USDConverter.convert_usd_to_coin(100.0, "NOTFOUND")

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_usd_to_coin_api_failure_raises_runtime_error(self, mock_market_service):
        """Test that API failures raise RuntimeError."""
        mock_market_service.get_price.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Failed to fetch price"):
            USDConverter.convert_usd_to_coin(100.0, "BTC")

    # ===================================================================
    # convert_coin_to_usd() tests
    # ===================================================================

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_coin_to_usd_btc(self, mock_market_service):
        """Test BTC to USD conversion."""
        mock_market_service.get_price.return_value = 50000.0

        usd_value, price = USDConverter.convert_coin_to_usd(0.5, "BTC")

        # 0.5 * 50000 = 25000
        assert usd_value == 25000.0
        assert price == 50000.0

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_coin_to_usd_eth(self, mock_market_service):
        """Test ETH to USD conversion."""
        mock_market_service.get_price.return_value = 3000.0

        usd_value, price = USDConverter.convert_coin_to_usd(10.0, "ETH")

        # 10 * 3000 = 30000
        assert usd_value == 30000.0
        assert price == 3000.0

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_coin_to_usd_zero_coin(self, mock_market_service):
        """Test conversion with zero coin amount."""
        mock_market_service.get_price.return_value = 50000.0

        usd_value, price = USDConverter.convert_coin_to_usd(0.0, "BTC")

        assert usd_value == 0.0

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_coin_to_usd_small_amount(self, mock_market_service):
        """Test conversion with very small coin amount."""
        mock_market_service.get_price.return_value = 50000.0

        usd_value, price = USDConverter.convert_coin_to_usd(0.0001, "BTC")

        # 0.0001 * 50000 = 5.0
        assert usd_value == 5.0

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_coin_to_usd_invalid_price_raises_error(self, mock_market_service):
        """Test that invalid price raises ValueError."""
        mock_market_service.get_price.return_value = 0.0

        with pytest.raises(ValueError, match="Invalid price"):
            USDConverter.convert_coin_to_usd(1.0, "INVALID")

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_coin_to_usd_coin_not_found_raises_error(self, mock_market_service):
        """Test that coin not found raises ValueError."""
        mock_market_service.get_price.side_effect = ValueError("Coin not found")

        with pytest.raises(ValueError, match="Failed to get price"):
            USDConverter.convert_coin_to_usd(1.0, "NOTFOUND")

    @patch("src.use_cases.common.usd_converter.market_data_service")
    def test_convert_coin_to_usd_api_failure_raises_runtime_error(self, mock_market_service):
        """Test that API failures raise RuntimeError."""
        mock_market_service.get_price.side_effect = Exception("API Error")

        with pytest.raises(RuntimeError, match="Failed to fetch price"):
            USDConverter.convert_coin_to_usd(1.0, "BTC")

    # ===================================================================
    # format_coin_amount() tests
    # ===================================================================

    def test_format_coin_amount_normal_amounts(self):
        """Test formatting normal coin amounts."""
        assert USDConverter.format_coin_amount(0.001234, "BTC") == "0.001234 BTC"
        assert USDConverter.format_coin_amount(1.5, "ETH") == "1.500000 ETH"
        assert USDConverter.format_coin_amount(100.123456, "SOL") == "100.123456 SOL"

    def test_format_coin_amount_very_small_amounts(self):
        """Test formatting very small amounts uses scientific notation."""
        # < 0.000001 uses scientific notation
        result = USDConverter.format_coin_amount(0.00000012, "ETH")
        assert "1.20e-07" in result
        assert "ETH" in result

    def test_format_coin_amount_zero(self):
        """Test formatting zero amount."""
        assert USDConverter.format_coin_amount(0, "BTC") == "0 BTC"
        assert USDConverter.format_coin_amount(0.0, "ETH") == "0 ETH"

    def test_format_coin_amount_negative(self):
        """Test formatting negative amounts (for display purposes)."""
        assert USDConverter.format_coin_amount(-0.5, "BTC") == "-0.500000 BTC"

    # ===================================================================
    # format_usd_amount() tests
    # ===================================================================

    def test_format_usd_amount_large_amounts(self):
        """Test formatting large USD amounts with thousands separator."""
        assert USDConverter.format_usd_amount(1234.56) == "$1,234.56"
        assert USDConverter.format_usd_amount(1000000.99) == "$1,000,000.99"
        assert USDConverter.format_usd_amount(50.0) == "$50.00"

    def test_format_usd_amount_small_amounts(self):
        """Test formatting small amounts < $1 with more decimals."""
        assert USDConverter.format_usd_amount(0.1234) == "$0.1234"
        assert USDConverter.format_usd_amount(0.5) == "$0.5000"
        assert USDConverter.format_usd_amount(0.99) == "$0.9900"

    def test_format_usd_amount_single_dollar(self):
        """Test formatting exactly $1."""
        assert USDConverter.format_usd_amount(1.0) == "$1.00"

    def test_format_usd_amount_zero(self):
        """Test formatting zero amount."""
        assert USDConverter.format_usd_amount(0.0) == "$0.0000"

    def test_format_usd_amount_negative(self):
        """Test formatting negative amounts (for losses)."""
        assert USDConverter.format_usd_amount(-100.50) == "$-100.50"

    # ===================================================================
    # format_dual_amount() tests
    # ===================================================================

    def test_format_dual_amount_normal_case(self):
        """Test formatting dual display (coin + USD)."""
        result = USDConverter.format_dual_amount(0.001234, 54.0, "BTC")

        assert "0.001234 BTC" in result
        assert "$54.00" in result
        assert "≈" in result

    def test_format_dual_amount_large_amounts(self):
        """Test dual format with large amounts."""
        result = USDConverter.format_dual_amount(10.5, 31500.0, "ETH")

        assert "10.500000 ETH" in result
        assert "$31,500.00" in result

    def test_format_dual_amount_small_coin_amount(self):
        """Test dual format with very small coin amount."""
        # Very small coin amounts use scientific notation
        result = USDConverter.format_dual_amount(0.00000012, 6.0, "BTC")

        assert "1.20e-07 BTC" in result
        assert "$6.00" in result

    def test_format_dual_amount_small_usd_value(self):
        """Test dual format with small USD value."""
        result = USDConverter.format_dual_amount(0.1, 0.15, "SOL")

        assert "0.100000 SOL" in result
        assert "$0.1500" in result

    # ===================================================================
    # round_to_decimals() tests
    # ===================================================================

    def test_round_to_decimals_normal_rounding(self):
        """Test normal decimal rounding."""
        assert USDConverter.round_to_decimals(0.123456, 4) == 0.1235
        assert USDConverter.round_to_decimals(1.5555, 2) == 1.56
        assert USDConverter.round_to_decimals(10.999, 1) == 11.0

    def test_round_to_decimals_zero_decimals(self):
        """Test rounding to zero decimal places."""
        assert USDConverter.round_to_decimals(5.7, 0) == 6.0
        assert USDConverter.round_to_decimals(5.4, 0) == 5.0

    def test_round_to_decimals_no_change_needed(self):
        """Test rounding when value already has fewer decimals."""
        assert USDConverter.round_to_decimals(1.5, 5) == 1.5
        assert USDConverter.round_to_decimals(10.0, 2) == 10.0

    def test_round_to_decimals_negative_numbers(self):
        """Test rounding negative numbers."""
        assert USDConverter.round_to_decimals(-0.123456, 4) == -0.1235
        assert USDConverter.round_to_decimals(-5.55, 1) == -5.5
