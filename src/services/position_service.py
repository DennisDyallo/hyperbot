"""
Position service for managing trading positions.
"""

from typing import Any

from src.config import logger, settings
from src.services.account_service import account_service
from src.services.hyperliquid_service import hyperliquid_service
from src.use_cases.common.response_parser import parse_hyperliquid_response


class PositionService:
    """Service for position-related operations."""

    def __init__(self):
        """Initialize position service."""
        self.hyperliquid = hyperliquid_service
        self.account = account_service

    def list_positions(self) -> list[dict[str, Any]]:
        """
        List all open positions.

        Returns:
            List of position details

        Raises:
            Exception: If API call fails
        """
        try:
            account_info = self.account.get_account_info()
            positions = account_info.get("positions", [])

            logger.debug(f"Listed {len(positions)} open positions")
            return positions  # type: ignore

        except Exception as e:
            logger.error(f"Failed to list positions: {e}")
            raise

    def get_position(self, coin: str) -> dict[str, Any] | None:
        """
        Get details for a specific position.

        Args:
            coin: Trading pair symbol (e.g., "BTC", "ETH")

        Returns:
            Position details if found, None otherwise

        Raises:
            Exception: If API call fails
        """
        try:
            positions = self.list_positions()

            for pos in positions:
                if pos["position"]["coin"] == coin:
                    logger.debug(f"Found position for {coin}")
                    return pos

            logger.debug(f"No position found for {coin}")
            return None

        except Exception as e:
            logger.error(f"Failed to get position for {coin}: {e}")
            raise

    def close_position(
        self, coin: str, size: float | None = None, slippage: float = 0.05
    ) -> dict[str, Any]:
        """
        Close a position (fully or partially).

        Args:
            coin: Trading pair symbol (e.g., "BTC", "ETH")
            size: Optional size to close (None = close entire position)
            slippage: Maximum acceptable slippage (default 5%)

        Returns:
            Dict with close result

        Raises:
            ValueError: If position doesn't exist or size is invalid
            RuntimeError: If Exchange API not available
            Exception: If API call fails
        """
        if not settings.HYPERLIQUID_WALLET_ADDRESS:
            raise RuntimeError("Wallet address not configured")

        try:
            # Verify position exists
            position = self.get_position(coin)
            if not position:
                raise ValueError(f"No open position found for {coin}")

            position_details = position["position"]
            current_size = abs(float(position_details["size"]))

            # Validate size if provided
            if size is not None:
                if size <= 0:
                    raise ValueError("Size must be positive")
                if size > current_size:
                    raise ValueError(f"Size {size} exceeds current position size {current_size}")
                close_size = size
            else:
                close_size = None  # Close entire position

            logger.info(
                f"Closing position for {coin}: "
                f"size={close_size if close_size else 'full'}, "
                f"slippage={slippage:.2%}"
            )

            # Execute close via Exchange API
            exchange = self.hyperliquid.get_exchange_client()
            result = exchange.market_close(coin=coin, sz=close_size, slippage=slippage)

            logger.info(f"Position close result: {result}")

            # Parse response and raise exception if close failed
            parse_hyperliquid_response(result, f"Close position for {coin}")

            return {
                "status": "success",
                "coin": coin,
                "size_closed": close_size if close_size else current_size,
                "result": result,
            }

        except ValueError as e:
            logger.error(f"Validation error closing position: {e}")
            raise
        except RuntimeError as e:
            logger.error(f"Runtime error closing position: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to close position for {coin}: {e}")
            raise

    def get_position_summary(self) -> dict[str, Any]:
        """
        Get summary of all positions.

        Returns:
            Dict with position summary statistics

        Raises:
            Exception: If API call fails
        """
        try:
            positions = self.list_positions()

            total_value = sum(float(p["position"]["position_value"]) for p in positions)
            total_pnl = sum(float(p["position"]["unrealized_pnl"]) for p in positions)

            # Group by long/short
            long_positions = [p for p in positions if float(p["position"]["size"]) > 0]
            short_positions = [p for p in positions if float(p["position"]["size"]) < 0]

            summary = {
                "total_positions": len(positions),
                "long_positions": len(long_positions),
                "short_positions": len(short_positions),
                "total_position_value": total_value,
                "total_unrealized_pnl": total_pnl,
                "positions": [
                    {
                        "coin": p["position"]["coin"],
                        "size": float(p["position"]["size"]),
                        "value": float(p["position"]["position_value"]),
                        "pnl": float(p["position"]["unrealized_pnl"]),
                    }
                    for p in positions
                ],
            }

            logger.debug(
                f"Position summary: {summary['total_positions']} positions, PnL=${total_pnl:.2f}"
            )

            return summary

        except Exception as e:
            logger.error(f"Failed to get position summary: {e}")
            raise


# Global service instance
position_service = PositionService()
