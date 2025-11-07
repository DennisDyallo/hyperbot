"""
USD/Coin conversion utilities.

This module provides centralized USD to coin (and vice versa) conversion logic
that is shared between API and Bot interfaces. It eliminates duplicate conversion
logic and provides consistent formatting across all interfaces.

Previously this logic was scattered in src/bot/utils.py and only available to the Bot.
Now it's available to both API and Bot through the Use Case layer.
"""

from src.config import logger
from src.services.market_data_service import market_data_service


class USDConverter:
    """
    Centralized USD/Coin conversion and formatting utilities.

    All methods are static since this is a stateless utility class.
    Uses market_data_service to fetch current prices for conversions.
    """

    @staticmethod
    def parse_usd_amount(amount_str: str) -> float:
        """
        Parse USD amount from string (strips $ if present).

        Args:
            amount_str: String like "100", "$100", "50.25"

        Returns:
            USD amount as float

        Raises:
            ValueError: If amount is invalid or <= 0

        Examples:
            >>> USDConverter.parse_usd_amount("100")
            100.0
            >>> USDConverter.parse_usd_amount("$50.25")
            50.25
        """
        # Strip whitespace
        amount_str = amount_str.strip()

        # Remove $ prefix if present
        if amount_str.startswith("$"):
            amount_str = amount_str[1:]

        # Parse as float
        try:
            amount = float(amount_str)
        except ValueError as e:
            raise ValueError(f"Invalid amount: {amount_str}. Must be a number.") from e

        # Validate > 0
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        return amount

    @staticmethod
    def convert_usd_to_coin(usd_amount: float, coin: str) -> tuple[float, float]:
        """
        Convert USD amount to coin size using current market price.
        Rounds to the correct precision based on asset's szDecimals.

        Args:
            usd_amount: USD dollar amount
            coin: Asset symbol (e.g., 'BTC', 'ETH')

        Returns:
            Tuple of (coin_size, current_price)

        Raises:
            ValueError: If coin not found or price unavailable
            RuntimeError: If price fetch fails

        Examples:
            >>> USDConverter.convert_usd_to_coin(100.0, "BTC")
            (0.00185185, 54000.0)  # If BTC price is $54,000
        """
        try:
            # Fetch current price
            current_price = market_data_service.get_price(coin)

            if current_price is None or current_price <= 0:
                raise ValueError(f"Invalid price for {coin}: {current_price}")

            # Calculate coin size
            coin_size = usd_amount / current_price

            # Get asset metadata for precision
            asset_meta = market_data_service.get_asset_metadata(coin)
            if asset_meta and "szDecimals" in asset_meta:
                decimals = asset_meta["szDecimals"]
                coin_size = round(coin_size, decimals)
                logger.debug(f"Rounded coin size to {decimals} decimals: {coin_size}")
            else:
                # Fallback to 6 decimals if metadata not available
                coin_size = round(coin_size, 6)
                logger.warning(f"Asset metadata not found for {coin}, using 6 decimal default")

            logger.debug(
                f"USD to coin conversion: ${usd_amount} / ${current_price} = {coin_size} {coin}"
            )

            return coin_size, current_price

        except ValueError as e:
            # Coin not found or invalid
            raise ValueError(f"Failed to get price for {coin}: {str(e)}") from e
        except Exception as e:
            # Other errors
            logger.exception(f"Error converting USD to coin for {coin}")
            raise RuntimeError(f"Failed to fetch price for {coin}: {str(e)}") from e

    @staticmethod
    def convert_coin_to_usd(coin_size: float, coin: str) -> tuple[float, float]:
        """
        Convert coin size to USD value using current market price.

        Args:
            coin_size: Amount of coins
            coin: Asset symbol (e.g., 'BTC', 'ETH')

        Returns:
            Tuple of (usd_value, current_price)

        Raises:
            ValueError: If coin not found or price unavailable
            RuntimeError: If price fetch fails

        Examples:
            >>> USDConverter.convert_coin_to_usd(0.01, "BTC")
            (540.0, 54000.0)  # If BTC price is $54,000
        """
        try:
            # Fetch current price
            current_price = market_data_service.get_price(coin)

            if current_price is None or current_price <= 0:
                raise ValueError(f"Invalid price for {coin}: {current_price}")

            # Calculate USD value
            usd_value = coin_size * current_price

            logger.debug(
                f"Coin to USD conversion: {coin_size} {coin} × ${current_price} = ${usd_value}"
            )

            return usd_value, current_price

        except ValueError as e:
            # Coin not found or invalid
            raise ValueError(f"Failed to get price for {coin}: {str(e)}") from e
        except Exception as e:
            # Other errors
            logger.exception(f"Error converting coin to USD for {coin}")
            raise RuntimeError(f"Failed to fetch price for {coin}: {str(e)}") from e

    @staticmethod
    def format_coin_amount(coin_size: float, coin: str) -> str:
        """
        Format coin amount with appropriate precision.

        Uses 6 decimal places for most coins, or scientific notation for very small amounts.

        Args:
            coin_size: Amount of coins
            coin: Asset symbol

        Returns:
            Formatted string like "0.001234 BTC" or "1.23e-7 ETH"

        Examples:
            >>> USDConverter.format_coin_amount(0.001234, "BTC")
            '0.001234 BTC'
            >>> USDConverter.format_coin_amount(0.00000012, "ETH")
            '1.20e-07 ETH'
        """
        if coin_size == 0:
            return f"0 {coin}"

        # Use scientific notation for very small amounts
        if abs(coin_size) < 0.000001:
            return f"{coin_size:.2e} {coin}"

        # Use 6 decimal places for normal amounts
        return f"{coin_size:.6f} {coin}"

    @staticmethod
    def format_usd_amount(usd_value: float) -> str:
        """
        Format USD amount with appropriate precision and thousands separators.

        Args:
            usd_value: USD dollar amount

        Returns:
            Formatted string like "$1,234.56" or "$0.12"

        Examples:
            >>> USDConverter.format_usd_amount(1234.56)
            '$1,234.56'
            >>> USDConverter.format_usd_amount(0.1234)
            '$0.1234'
        """
        if abs(usd_value) >= 1:
            # Use 2 decimal places with thousands separator for amounts >= $1
            return f"${usd_value:,.2f}"
        else:
            # Use more decimals for amounts < $1
            return f"${usd_value:.4f}"

    @staticmethod
    def format_dual_amount(coin_size: float, usd_value: float, coin: str) -> str:
        """
        Format a display showing both coin amount and USD value.

        Args:
            coin_size: Amount of coins
            usd_value: USD dollar value
            coin: Asset symbol

        Returns:
            Formatted string like "0.001234 BTC ($54.00)" or "$100.00 (0.00185 BTC)"

        Examples:
            >>> USDConverter.format_dual_amount(0.001234, 54.0, "BTC")
            '0.001234 BTC (≈$54.00)'
        """
        coin_str = USDConverter.format_coin_amount(coin_size, coin)
        usd_str = USDConverter.format_usd_amount(usd_value)

        return f"{coin_str} (≈{usd_str})"

    @staticmethod
    def round_to_decimals(value: float, decimals: int) -> float:
        """
        Round value to specified decimal places.

        Args:
            value: Value to round
            decimals: Number of decimal places

        Returns:
            Rounded value

        Examples:
            >>> USDConverter.round_to_decimals(0.123456, 4)
            0.1235
        """
        return round(value, decimals)
