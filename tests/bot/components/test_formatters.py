"""Tests for formatting utilities."""

from datetime import UTC, datetime

from src.bot.components.formatters import (
    format_coin_size,
    format_currency,
    format_percentage,
    format_pnl,
    format_timestamp,
)


class TestFormatCurrency:
    """Test currency formatting."""

    def test_positive_value(self) -> None:
        """Test formatting positive currency values."""
        assert format_currency(1234.56) == "$1,234.56"
        assert format_currency(1000000.00) == "$1,000,000.00"

    def test_negative_value(self) -> None:
        """Test formatting negative currency values."""
        assert format_currency(-1234.56) == "-$1,234.56"
        assert format_currency(-1000000.00) == "-$1,000,000.00"

    def test_zero_value(self) -> None:
        """Test formatting zero."""
        assert format_currency(0) == "$0.00"
        assert format_currency(0.0) == "$0.00"

    def test_show_sign_positive(self) -> None:
        """Test showing sign for positive values."""
        assert format_currency(1234.56, show_sign=True) == "+$1,234.56"
        assert format_currency(0, show_sign=True) == "$0.00"

    def test_show_sign_negative(self) -> None:
        """Test sign is always shown for negative values."""
        assert format_currency(-1234.56, show_sign=False) == "-$1,234.56"
        assert format_currency(-1234.56, show_sign=True) == "-$1,234.56"

    def test_custom_decimals(self) -> None:
        """Test custom decimal places."""
        assert format_currency(1234.5678, decimals=4) == "$1,234.5678"
        # Rounding, not truncation
        assert format_currency(1234.5, decimals=0) == "$1,234"

    def test_very_large_values(self) -> None:
        """Test formatting very large values."""
        assert format_currency(1234567890.12) == "$1,234,567,890.12"

    def test_very_small_values(self) -> None:
        """Test formatting very small values."""
        assert format_currency(0.01) == "$0.01"
        assert format_currency(0.001) == "$0.00"  # Rounds to 2 decimals


class TestFormatPercentage:
    """Test percentage formatting."""

    def test_positive_percentage(self) -> None:
        """Test formatting positive percentages."""
        assert format_percentage(5.234) == "+5.2%"
        assert format_percentage(100.0) == "+100.0%"

    def test_negative_percentage(self) -> None:
        """Test formatting negative percentages."""
        assert format_percentage(-5.234) == "-5.2%"
        assert format_percentage(-100.0) == "-100.0%"

    def test_zero_percentage(self) -> None:
        """Test formatting zero percentage."""
        assert format_percentage(0) == "0.0%"
        assert format_percentage(0.0) == "0.0%"

    def test_no_sign(self) -> None:
        """Test formatting without sign."""
        assert format_percentage(5.234, show_sign=False) == "5.2%"
        assert format_percentage(-5.234, show_sign=False) == "-5.2%"  # Always show for negative

    def test_custom_decimals(self) -> None:
        """Test custom decimal places."""
        assert format_percentage(5.234, decimals=2) == "+5.23%"
        assert format_percentage(5.234, decimals=0) == "+5%"

    def test_rounding(self) -> None:
        """Test rounding behavior."""
        assert format_percentage(5.25) == "+5.2%"
        assert format_percentage(5.26) == "+5.3%"


class TestFormatCoinSize:
    """Test coin size formatting."""

    def test_btc_formatting(self) -> None:
        """Test BTC uses 8 decimal places."""
        assert format_coin_size(0.01015234, "BTC") == "0.01015234 BTC"
        assert format_coin_size(1.0, "BTC") == "1.0 BTC"

    def test_eth_formatting(self) -> None:
        """Test ETH uses 6 decimal places."""
        assert format_coin_size(12.123456, "ETH") == "12.123456 ETH"

    def test_sol_formatting(self) -> None:
        """Test SOL uses 4 decimal places."""
        assert format_coin_size(12.5, "SOL") == "12.5 SOL"
        assert format_coin_size(12.5678, "SOL") == "12.5678 SOL"

    def test_case_insensitive(self) -> None:
        """Test coin symbol is case insensitive."""
        assert format_coin_size(1.0, "btc") == "1.0 BTC"
        assert format_coin_size(1.0, "Btc") == "1.0 BTC"

    def test_zero_value(self) -> None:
        """Test zero coin size."""
        assert format_coin_size(0.0, "BTC") == "0.0 BTC"
        assert format_coin_size(0.0, "ETH") == "0.0 ETH"

    def test_trailing_zeros_removed(self) -> None:
        """Test trailing zeros are removed."""
        assert format_coin_size(1.00000000, "BTC") == "1.0 BTC"
        assert format_coin_size(0.10000000, "BTC") == "0.1 BTC"

    def test_unknown_coin_uses_default(self) -> None:
        """Test unknown coins use default decimal places."""
        assert "UNKNOWN" in format_coin_size(12.5678, "UNKNOWN")


class TestFormatPnL:
    """Test PnL formatting."""

    def test_positive_pnl(self) -> None:
        """Test positive PnL with green emoji."""
        result = format_pnl(123.45, 5.234)
        assert result == "🟢 +$123.45 (+5.2%)"

    def test_negative_pnl(self) -> None:
        """Test negative PnL with red emoji."""
        result = format_pnl(-123.45, -5.234)
        assert result == "🔴 -$123.45 (-5.2%)"

    def test_zero_pnl(self) -> None:
        """Test zero PnL with white emoji."""
        result = format_pnl(0, 0)
        assert result == "⚪ $0.00 (0.0%)"

    def test_large_pnl(self) -> None:
        """Test large PnL values."""
        result = format_pnl(123456.78, 50.0)
        assert result == "🟢 +$123,456.78 (+50.0%)"

    def test_small_positive_pnl(self) -> None:
        """Test very small positive PnL."""
        result = format_pnl(0.01, 0.001)
        assert result == "🟢 +$0.01 (+0.0%)"


class TestFormatTimestamp:
    """Test timestamp formatting."""

    def test_with_date(self) -> None:
        """Test formatting with date included."""
        dt = datetime(2025, 12, 1, 14, 30, 0, tzinfo=UTC)
        assert format_timestamp(dt) == "2025-12-01 14:30 UTC"

    def test_without_date(self) -> None:
        """Test formatting time only."""
        dt = datetime(2025, 12, 1, 14, 30, 0, tzinfo=UTC)
        assert format_timestamp(dt, include_date=False) == "14:30 UTC"

    def test_naive_datetime_converted_to_utc(self) -> None:
        """Test naive datetime is converted to UTC."""
        dt_naive = datetime(2025, 12, 1, 14, 30, 0)  # No timezone
        result = format_timestamp(dt_naive)
        assert result == "2025-12-01 14:30 UTC"

    def test_different_timezone_converted_to_utc(self) -> None:
        """Test datetime in different timezone is converted to UTC."""
        from datetime import timedelta, timezone

        # Create a datetime in EST (UTC-5)
        est = timezone(timedelta(hours=-5))
        dt_est = datetime(2025, 12, 1, 9, 30, 0, tzinfo=est)

        # Should be converted to UTC (14:30 UTC = 9:30 EST)
        result = format_timestamp(dt_est)
        assert result == "2025-12-01 14:30 UTC"

    def test_midnight(self) -> None:
        """Test midnight time formatting."""
        dt = datetime(2025, 12, 1, 0, 0, 0, tzinfo=UTC)
        assert format_timestamp(dt) == "2025-12-01 00:00 UTC"
