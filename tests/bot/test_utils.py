"""
Unit tests for bot utility functions.

Tests the functions in src/bot/utils.py that handle:
- USD amount parsing
- USD <-> coin conversions with precision rounding
- Formatting functions
"""
import pytest
from unittest.mock import patch, Mock
from src.bot.utils import (
    parse_usd_amount,
    convert_usd_to_coin,
    convert_coin_to_usd,
    format_coin_amount,
    format_usd_amount,
    format_dual_amount
)


# =============================================================================
# parse_usd_amount Tests
# =============================================================================

class TestParseUsdAmount:
    """Test USD amount parsing from strings."""

    def test_parse_plain_number(self):
        """Should parse plain number strings."""
        assert parse_usd_amount("100") == 100.0
        assert parse_usd_amount("50.25") == 50.25
        assert parse_usd_amount("0.01") == 0.01

    def test_parse_with_dollar_sign(self):
        """Should strip dollar sign and parse."""
        assert parse_usd_amount("$100") == 100.0
        assert parse_usd_amount("$50.25") == 50.25
        assert parse_usd_amount("$0.99") == 0.99

    def test_parse_with_whitespace(self):
        """Should strip whitespace."""
        assert parse_usd_amount("  100  ") == 100.0
        assert parse_usd_amount(" $50.25 ") == 50.25

    def test_parse_large_amounts(self):
        """Should handle large amounts."""
        assert parse_usd_amount("10000") == 10000.0
        assert parse_usd_amount("$1000000.50") == 1000000.50

    def test_parse_invalid_raises_error(self):
        """Should raise ValueError for invalid input."""
        with pytest.raises(ValueError, match="Invalid amount"):
            parse_usd_amount("abc")

        with pytest.raises(ValueError, match="Invalid amount"):
            parse_usd_amount("$")

        with pytest.raises(ValueError, match="Invalid amount"):
            parse_usd_amount("100abc")

    def test_parse_zero_or_negative_raises_error(self):
        """Should raise ValueError for zero or negative amounts."""
        with pytest.raises(ValueError, match="must be greater than 0"):
            parse_usd_amount("0")

        with pytest.raises(ValueError, match="must be greater than 0"):
            parse_usd_amount("-100")

        with pytest.raises(ValueError, match="must be greater than 0"):
            parse_usd_amount("$-50.25")


# =============================================================================
# convert_usd_to_coin Tests (Bug Fix: Precision Rounding)
# =============================================================================

class TestConvertUsdToCoin:
    """Test USD to coin conversion with precision rounding."""

    @patch('src.bot.utils.market_data_service')
    def test_convert_with_btc_precision(self, mock_service):
        """Should round to BTC's 5 decimal precision."""
        # BTC price = $104,088, szDecimals = 5
        mock_service.get_price.return_value = 104088.0
        mock_service.get_asset_metadata.return_value = {
            "name": "BTC",
            "szDecimals": 5
        }

        coin_size, price = convert_usd_to_coin(250.0, "BTC")

        # $250 / $104,088 = 0.0024014216...
        # Rounded to 5 decimals = 0.00240
        assert coin_size == pytest.approx(0.00240, abs=1e-5)
        assert price == 104088.0

        # Verify no precision error (was causing ValueError before)
        assert len(str(coin_size).split('.')[1]) <= 5

    @patch('src.bot.utils.market_data_service')
    def test_convert_with_eth_precision(self, mock_service):
        """Should round to ETH's 4 decimal precision."""
        # ETH price = $3,850.50, szDecimals = 4
        mock_service.get_price.return_value = 3850.50
        mock_service.get_asset_metadata.return_value = {
            "name": "ETH",
            "szDecimals": 4
        }

        coin_size, price = convert_usd_to_coin(100.0, "ETH")

        # $100 / $3,850.50 = 0.025971...
        # Rounded to 4 decimals = 0.0260
        assert coin_size == pytest.approx(0.0260, abs=1e-4)
        assert price == 3850.50

    @patch('src.bot.utils.market_data_service')
    def test_convert_with_sol_precision(self, mock_service):
        """Should round to SOL's 1 decimal precision."""
        # SOL price = $161.64, szDecimals = 1
        mock_service.get_price.return_value = 161.64
        mock_service.get_asset_metadata.return_value = {
            "name": "SOL",
            "szDecimals": 1
        }

        coin_size, price = convert_usd_to_coin(50.0, "SOL")

        # $50 / $161.64 = 0.309...
        # Rounded to 1 decimal = 0.3
        assert coin_size == pytest.approx(0.3, abs=0.1)
        assert price == 161.64

    @patch('src.bot.utils.market_data_service')
    def test_convert_fallback_to_6_decimals(self, mock_service):
        """Should fallback to 6 decimals if metadata unavailable."""
        mock_service.get_price.return_value = 100.0
        mock_service.get_asset_metadata.return_value = None

        coin_size, price = convert_usd_to_coin(50.0, "UNKNOWN")

        # $50 / $100 = 0.5
        # Should still work with 6 decimal fallback
        assert coin_size == 0.5
        assert price == 100.0

    @patch('src.bot.utils.market_data_service')
    def test_convert_large_amounts(self, mock_service):
        """Should handle large USD amounts correctly."""
        mock_service.get_price.return_value = 104088.0
        mock_service.get_asset_metadata.return_value = {
            "name": "BTC",
            "szDecimals": 5
        }

        coin_size, price = convert_usd_to_coin(10000.0, "BTC")

        # $10,000 / $104,088 = 0.09608...
        # Rounded to 5 decimals = 0.09608
        assert coin_size == pytest.approx(0.09608, abs=1e-5)

    @patch('src.bot.utils.market_data_service')
    def test_convert_small_amounts(self, mock_service):
        """Should handle small USD amounts correctly."""
        mock_service.get_price.return_value = 104088.0
        mock_service.get_asset_metadata.return_value = {
            "name": "BTC",
            "szDecimals": 5
        }

        coin_size, price = convert_usd_to_coin(1.0, "BTC")

        # $1 / $104,088 = 0.00000960...
        # Rounded to 5 decimals = 0.00001
        assert coin_size == pytest.approx(0.00001, abs=1e-5)

    @patch('src.bot.utils.market_data_service')
    def test_convert_invalid_price_raises_error(self, mock_service):
        """Should raise ValueError for invalid prices."""
        mock_service.get_price.return_value = 0

        with pytest.raises(ValueError, match="Invalid price"):
            convert_usd_to_coin(100.0, "BTC")

    @patch('src.bot.utils.market_data_service')
    def test_convert_coin_not_found_raises_error(self, mock_service):
        """Should raise ValueError if coin not found."""
        mock_service.get_price.side_effect = ValueError("Coin not found")

        with pytest.raises(ValueError, match="Failed to get price"):
            convert_usd_to_coin(100.0, "INVALID")


# =============================================================================
# convert_coin_to_usd Tests
# =============================================================================

class TestConvertCoinToUsd:
    """Test coin to USD conversion."""

    @patch('src.bot.utils.market_data_service')
    def test_convert_coin_to_usd(self, mock_service):
        """Should convert coin size to USD value."""
        mock_service.get_price.return_value = 104088.0

        usd_value, price = convert_coin_to_usd(0.00432, "BTC")

        # 0.00432 BTC × $104,088 = $449.66
        assert usd_value == pytest.approx(449.66, abs=0.01)
        assert price == 104088.0

    @patch('src.bot.utils.market_data_service')
    def test_convert_zero_coin(self, mock_service):
        """Should handle zero coin amount."""
        mock_service.get_price.return_value = 104088.0

        usd_value, price = convert_coin_to_usd(0.0, "BTC")

        assert usd_value == 0.0
        assert price == 104088.0


# =============================================================================
# Formatting Tests
# =============================================================================

class TestFormatCoinAmount:
    """Test coin amount formatting."""

    def test_format_normal_amounts(self):
        """Should format normal amounts with 6 decimals."""
        assert format_coin_amount(0.001234, "BTC") == "0.001234 BTC"
        assert format_coin_amount(1.5, "ETH") == "1.500000 ETH"
        assert format_coin_amount(100, "SOL") == "100.000000 SOL"

    def test_format_very_small_amounts(self):
        """Should use scientific notation for very small amounts."""
        assert format_coin_amount(0.0000001, "BTC") == "1.00e-07 BTC"
        assert format_coin_amount(0.0000005, "ETH") == "5.00e-07 ETH"

    def test_format_zero(self):
        """Should format zero correctly."""
        assert format_coin_amount(0, "BTC") == "0 BTC"
        assert format_coin_amount(0.0, "ETH") == "0 ETH"


class TestFormatUsdAmount:
    """Test USD amount formatting."""

    def test_format_large_amounts(self):
        """Should format large amounts with thousands separator."""
        assert format_usd_amount(1234.56) == "$1,234.56"
        assert format_usd_amount(1000000) == "$1,000,000.00"
        assert format_usd_amount(100) == "$100.00"

    def test_format_small_amounts(self):
        """Should format small amounts with more decimals."""
        assert format_usd_amount(0.99) == "$0.9900"
        assert format_usd_amount(0.1234) == "$0.1234"

    def test_format_single_dollar(self):
        """Should format amounts >= $1 with 2 decimals."""
        assert format_usd_amount(1.0) == "$1.00"
        assert format_usd_amount(1.99) == "$1.99"


class TestFormatDualAmount:
    """Test dual amount formatting (coin + USD)."""

    def test_format_dual_amount(self):
        """Should format both coin and USD amounts."""
        result = format_dual_amount(0.001234, 100.50, "BTC")

        assert "0.001234 BTC" in result
        assert "$100.50" in result
        assert "≈" in result

    def test_format_dual_large_amounts(self):
        """Should handle large amounts in dual format."""
        result = format_dual_amount(10.5, 125000.0, "ETH")

        assert "10.500000 ETH" in result
        assert "$125,000.00" in result
