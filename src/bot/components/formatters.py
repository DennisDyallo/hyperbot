"""
Formatting utilities for consistent display of financial data in Telegram messages.

All formatters handle edge cases (zero, negative, very large values) and ensure
consistent number formatting across the bot.
"""

from datetime import UTC, datetime
from typing import Final

# Constants for consistent formatting
CURRENCY_SYMBOL: Final[str] = "$"
DECIMAL_PLACES_CURRENCY: Final[int] = 2
DECIMAL_PLACES_PERCENTAGE: Final[int] = 1
LARGE_NUMBER_THRESHOLD: Final[float] = 1_000_000  # 1M

# Coin-specific decimal places (for size display)
COIN_DECIMALS: Final[dict[str, int]] = {
    "BTC": 8,
    "ETH": 6,
    "SOL": 4,
    "AVAX": 4,
    "DEFAULT": 4,
}


def format_currency(
    value: float,
    show_sign: bool = False,
    decimals: int = DECIMAL_PLACES_CURRENCY,
) -> str:
    """
    Format a USD value with proper thousands separators and sign.

    Args:
        value: The dollar amount to format.
        show_sign: If True, include '+' for positive values.
        decimals: Number of decimal places (default: 2).

    Returns:
        Formatted string like "$1,234.56" or "+$1,234.56".

    Examples:
        >>> format_currency(1234.56)
        '$1,234.56'
        >>> format_currency(1234.56, show_sign=True)
        '+$1,234.56'
        >>> format_currency(-1234.56)
        '-$1,234.56'
        >>> format_currency(0)
        '$0.00'
        >>> format_currency(1234567.89)
        '$1,234,567.89'
    """
    if value == 0:
        return f"{CURRENCY_SYMBOL}0.{('0' * decimals)}"

    abs_value = abs(value)
    sign = ""

    if value > 0 and show_sign:
        sign = "+"
    elif value < 0:
        sign = "-"

    # Format with thousands separator and specified decimals
    formatted_value = f"{abs_value:,.{decimals}f}"

    return f"{sign}{CURRENCY_SYMBOL}{formatted_value}"


def format_percentage(
    value: float,
    decimals: int = DECIMAL_PLACES_PERCENTAGE,
    show_sign: bool = True,
) -> str:
    """
    Format a percentage value with consistent decimal places.

    Args:
        value: The percentage value (e.g., 5.2 for 5.2%).
        decimals: Number of decimal places (default: 1).
        show_sign: If True, include '+' for positive values (default: True).

    Returns:
        Formatted string like "+5.2%" or "-5.2%".

    Examples:
        >>> format_percentage(5.234)
        '+5.2%'
        >>> format_percentage(-5.234)
        '-5.2%'
        >>> format_percentage(0)
        '0.0%'
        >>> format_percentage(5.234, show_sign=False)
        '5.2%'
        >>> format_percentage(100.0)
        '+100.0%'
    """
    if value == 0:
        return f"0.{('0' * decimals)}%"

    sign = ""
    if value > 0 and show_sign:
        sign = "+"
    elif value < 0:
        sign = "-"

    abs_value = abs(value)
    formatted_value = f"{abs_value:.{decimals}f}"

    return f"{sign}{formatted_value}%"


def format_coin_size(size: float, coin: str) -> str:
    """
    Format a cryptocurrency size with appropriate decimal places.

    Different coins require different precision levels (BTC needs more decimals
    than SOL due to value differences).

    Args:
        size: The coin amount.
        coin: The coin symbol (e.g., "BTC", "ETH").

    Returns:
        Formatted string like "0.01015 BTC" or "12.5000 SOL".

    Examples:
        >>> format_coin_size(0.01015234, "BTC")
        '0.01015234 BTC'
        >>> format_coin_size(12.5, "SOL")
        '12.5000 SOL'
        >>> format_coin_size(0.0, "ETH")
        '0.000000 ETH'
    """
    coin_upper = coin.upper()
    decimals = COIN_DECIMALS.get(coin_upper, COIN_DECIMALS["DEFAULT"])

    # Remove trailing zeros but keep minimum decimals
    formatted_size = f"{size:.{decimals}f}".rstrip("0").rstrip(".")

    # Ensure at least one decimal place
    if "." not in formatted_size:
        formatted_size += ".0"

    return f"{formatted_size} {coin_upper}"


def format_pnl(pnl_usd: float, pnl_pct: float) -> str:
    """
    Format PnL (Profit and Loss) with both USD and percentage, including emoji.

    Uses color-coded emojis:
        🟢 for positive PnL
        🔴 for negative PnL
        ⚪ for zero PnL

    Args:
        pnl_usd: PnL in USD.
        pnl_pct: PnL as a percentage.

    Returns:
        Formatted string like "🟢 +$123.45 (+5.2%)".

    Examples:
        >>> format_pnl(123.45, 5.234)
        '🟢 +$123.45 (+5.2%)'
        >>> format_pnl(-123.45, -5.234)
        '🔴 -$123.45 (-5.2%)'
        >>> format_pnl(0, 0)
        '⚪ $0.00 (0.0%)'
    """
    # Determine emoji based on PnL
    if pnl_usd > 0:
        emoji = "🟢"
    elif pnl_usd < 0:
        emoji = "🔴"
    else:
        emoji = "⚪"

    # Format currency and percentage
    currency_str = format_currency(pnl_usd, show_sign=True)
    pct_str = format_percentage(pnl_pct, show_sign=True)

    return f"{emoji} {currency_str} ({pct_str})"


def format_timestamp(dt: datetime, include_date: bool = True) -> str:
    """
    Format a datetime for display in Telegram messages.

    Args:
        dt: The datetime to format (aware or naive).
        include_date: If True, include date; if False, time only.

    Returns:
        Formatted string like "2025-12-01 14:30 UTC" or "14:30 UTC".

    Examples:
        >>> from datetime import UTC, datetime
        >>> dt = datetime(2025, 12, 1, 14, 30, 0, tzinfo=UTC)
        >>> format_timestamp(dt)
        '2025-12-01 14:30 UTC'
        >>> format_timestamp(dt, include_date=False)
        '14:30 UTC'
    """
    # Ensure datetime is timezone-aware (convert to UTC if naive)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    # Convert to UTC for consistency
    dt_utc = dt.astimezone(UTC)

    if include_date:
        return dt_utc.strftime("%Y-%m-%d %H:%M UTC")
    return dt_utc.strftime("%H:%M UTC")
