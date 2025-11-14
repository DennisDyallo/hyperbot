"""
Market data service for fetching prices and market information.
"""

from typing import Any

from src.config import logger
from src.services.hyperliquid_service import hyperliquid_service


class MarketDataService:
    """Service for market data operations."""

    def __init__(self):
        """Initialize market data service."""
        self.hyperliquid = hyperliquid_service

    def get_all_prices(self) -> dict[str, float]:
        """
        Get current mid prices for all trading pairs.

        Returns:
            Dict mapping coin symbols to their current prices

        Raises:
            RuntimeError: If Info API not available
            Exception: If API call fails

        Example:
            >>> prices = market_data_service.get_all_prices()
            >>> print(f"BTC: ${prices['BTC']:,.2f}")
        """
        try:
            info_client = self.hyperliquid.get_info_client()
            prices = info_client.all_mids()

            logger.debug(f"Fetched prices for {len(prices)} trading pairs")

            # Convert to float for consistency
            return {coin: float(price) for coin, price in prices.items()}

        except Exception as e:
            logger.error(f"Failed to fetch all prices: {e}")
            raise

    def get_price(self, coin: str) -> float:
        """
        Get current mid price for a specific coin.

        Args:
            coin: Trading pair symbol (e.g., "BTC", "ETH")

        Returns:
            Current mid price as float

        Raises:
            ValueError: If coin not found
            RuntimeError: If Info API not available
            Exception: If API call fails

        Example:
            >>> btc_price = market_data_service.get_price("BTC")
            >>> print(f"BTC: ${btc_price:,.2f}")
        """
        try:
            prices = self.get_all_prices()

            if coin not in prices:
                available = ", ".join(sorted(prices.keys())[:10])
                raise ValueError(f"Coin '{coin}' not found. Available coins: {available}...")

            price = prices[coin]
            logger.debug(f"Price for {coin}: ${price:,.2f}")

            return price

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch price for {coin}: {e}")
            raise

    def get_market_info(self) -> dict[str, Any]:
        """
        Get exchange metadata including available pairs, tick sizes, and limits.

        Returns:
            Dict containing market metadata

        Raises:
            RuntimeError: If Info API not available
            Exception: If API call fails

        Example:
            >>> meta = market_data_service.get_market_info()
            >>> print(f"Available pairs: {len(meta['universe'])}")
        """
        try:
            info_client = self.hyperliquid.get_info_client()
            meta = info_client.meta()

            logger.debug("Fetched market metadata")

            return meta  # type: ignore

        except Exception as e:
            logger.error(f"Failed to fetch market metadata: {e}")
            raise

    def get_order_book(self, coin: str) -> dict[str, Any]:
        """
        Get Level 2 order book snapshot for a specific coin.

        Args:
            coin: Trading pair symbol (e.g., "BTC", "ETH")

        Returns:
            Dict containing order book with bids and asks

        Raises:
            ValueError: If coin invalid
            RuntimeError: If Info API not available
            Exception: If API call fails

        Example:
            >>> book = market_data_service.get_order_book("BTC")
            >>> print(f"Best bid: {book['levels'][0][0]['px']}")
        """
        if not coin:
            raise ValueError("Coin symbol is required")

        try:
            info_client = self.hyperliquid.get_info_client()
            snapshot = info_client.l2_snapshot(coin)

            logger.debug(f"Fetched order book for {coin}")

            return snapshot  # type: ignore

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to fetch order book for {coin}: {e}")
            raise

    def get_asset_metadata(self, coin: str) -> dict[str, Any] | None:
        """
        Get metadata for a specific asset (tick size, min size, etc.).

        Args:
            coin: Trading pair symbol (e.g., "BTC", "ETH")

        Returns:
            Dict containing asset metadata, or None if not found

        Raises:
            RuntimeError: If Info API not available
            Exception: If API call fails

        Example:
            >>> meta = market_data_service.get_asset_metadata("BTC")
            >>> print(f"Tick size: {meta['szDecimals']}")
        """
        try:
            market_info = self.get_market_info()
            universe = market_info.get("universe", [])

            # Find the asset in the universe
            for asset in universe:
                if asset.get("name") == coin:
                    logger.debug(f"Found metadata for {coin}")
                    return asset  # type: ignore

            logger.warning(f"Asset metadata not found for {coin}")
            return None

        except Exception as e:
            logger.error(f"Failed to fetch asset metadata for {coin}: {e}")
            raise


# Global service instance
market_data_service = MarketDataService()
