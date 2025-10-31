"""
Order service for managing trading orders.
"""
from typing import Dict, Any, List, Optional
from src.services.hyperliquid_service import hyperliquid_service
from src.config import logger, settings


def _parse_hyperliquid_response(result: Dict[str, Any], operation: str) -> None:
    """
    Parse Hyperliquid API response and raise exception if operation failed.

    Hyperliquid returns 'status: ok' even when orders fail. The actual
    success/failure is nested in response.data.statuses array.

    Args:
        result: The response from Hyperliquid API
        operation: Description of the operation (for error messages)

    Raises:
        RuntimeError: If the operation failed according to Hyperliquid
    """
    # Check top-level status
    if result.get("status") != "ok":
        error_msg = result.get("error", "Unknown error")
        raise RuntimeError(f"{operation} failed: {error_msg}")

    # Check nested statuses for errors
    response = result.get("response", {})
    data = response.get("data", {})
    statuses = data.get("statuses", [])

    for status in statuses:
        # Check for error field
        if "error" in status:
            raise ValueError(f"{operation} failed: {status['error']}")

        # Check for resting field (order placed but not filled)
        if "resting" in status:
            # This is OK - limit orders will rest in the book
            continue

        # Check for filled field (success)
        if "filled" in status:
            # Success case
            continue


class OrderService:
    """Service for order-related operations."""

    def __init__(self):
        """Initialize order service."""
        self.hyperliquid = hyperliquid_service

    def list_open_orders(self) -> List[Dict[str, Any]]:
        """
        List all open orders.

        Returns:
            List of open orders

        Raises:
            RuntimeError: If wallet address not configured
            Exception: If API call fails
        """
        if not settings.HYPERLIQUID_WALLET_ADDRESS:
            raise RuntimeError("Wallet address not configured")

        try:
            info_client = self.hyperliquid.get_info_client()
            orders = info_client.open_orders(settings.HYPERLIQUID_WALLET_ADDRESS)

            logger.debug(f"Listed {len(orders)} open orders")
            return orders

        except Exception as e:
            logger.error(f"Failed to list open orders: {e}")
            raise

    def place_market_order(
        self, coin: str, is_buy: bool, size: float, slippage: float = 0.05
    ) -> Dict[str, Any]:
        """
        Place a market order.

        Args:
            coin: Trading pair symbol (e.g., "BTC", "ETH")
            is_buy: True for buy, False for sell
            size: Order size
            slippage: Maximum acceptable slippage (default 5%)

        Returns:
            Dict with order result

        Raises:
            ValueError: If size is invalid
            RuntimeError: If Exchange API not available
            Exception: If API call fails
        """
        if size <= 0:
            raise ValueError("Size must be positive")

        if not settings.HYPERLIQUID_WALLET_ADDRESS:
            raise RuntimeError("Wallet address not configured")

        try:
            side = "buy" if is_buy else "sell"
            logger.info(
                f"Placing market order: {coin} {side} {size} (slippage={slippage:.2%})"
            )

            exchange = self.hyperliquid.get_exchange_client()
            result = exchange.market_open(
                name=coin, is_buy=is_buy, sz=size, slippage=slippage
            )

            logger.info(f"Market order result: {result}")

            # Parse response and raise exception if order failed
            _parse_hyperliquid_response(result, f"Market {side} order for {coin}")

            return {
                "status": "success",
                "coin": coin,
                "side": side,
                "size": size,
                "order_type": "market",
                "result": result,
            }

        except ValueError as e:
            logger.error(f"Validation error placing market order: {e}")
            raise
        except RuntimeError as e:
            logger.error(f"Runtime error placing market order: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            raise

    def place_limit_order(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        limit_price: float,
        time_in_force: str = "Gtc",
    ) -> Dict[str, Any]:
        """
        Place a limit order.

        Args:
            coin: Trading pair symbol (e.g., "BTC", "ETH")
            is_buy: True for buy, False for sell
            size: Order size
            limit_price: Limit price
            time_in_force: Time in force ("Gtc", "Ioc", "Alo") - default "Gtc"

        Returns:
            Dict with order result

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If Exchange API not available
            Exception: If API call fails
        """
        if size <= 0:
            raise ValueError("Size must be positive")
        if limit_price <= 0:
            raise ValueError("Limit price must be positive")

        valid_tif = ["Gtc", "Ioc", "Alo"]
        if time_in_force not in valid_tif:
            raise ValueError(f"time_in_force must be one of {valid_tif}")

        if not settings.HYPERLIQUID_WALLET_ADDRESS:
            raise RuntimeError("Wallet address not configured")

        try:
            side = "buy" if is_buy else "sell"
            logger.info(
                f"Placing limit order: {coin} {side} {size} @ ${limit_price} (TIF={time_in_force})"
            )

            exchange = self.hyperliquid.get_exchange_client()
            result = exchange.order(
                name=coin,
                is_buy=is_buy,
                sz=size,
                limit_px=limit_price,
                order_type={"limit": {"tif": time_in_force}},
            )

            logger.info(f"Limit order result: {result}")

            # Parse response and raise exception if order failed
            _parse_hyperliquid_response(result, f"Limit {side} order for {coin}")

            return {
                "status": "success",
                "coin": coin,
                "side": side,
                "size": size,
                "limit_price": limit_price,
                "order_type": "limit",
                "time_in_force": time_in_force,
                "result": result,
            }

        except ValueError as e:
            logger.error(f"Validation error placing limit order: {e}")
            raise
        except RuntimeError as e:
            logger.error(f"Runtime error placing limit order: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            raise

    def cancel_order(self, coin: str, order_id: int) -> Dict[str, Any]:
        """
        Cancel a specific order.

        Args:
            coin: Trading pair symbol
            order_id: Order ID to cancel

        Returns:
            Dict with cancel result

        Raises:
            RuntimeError: If Exchange API not available
            Exception: If API call fails
        """
        if not settings.HYPERLIQUID_WALLET_ADDRESS:
            raise RuntimeError("Wallet address not configured")

        try:
            logger.info(f"Canceling order: {coin} order_id={order_id}")

            exchange = self.hyperliquid.get_exchange_client()
            result = exchange.cancel(name=coin, oid=order_id)

            logger.info(f"Cancel order result: {result}")

            # Parse response and raise exception if cancellation failed
            _parse_hyperliquid_response(result, f"Cancel order {coin}#{order_id}")

            return {
                "status": "success",
                "coin": coin,
                "order_id": order_id,
                "result": result,
            }

        except RuntimeError as e:
            logger.error(f"Runtime error canceling order: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise

    def cancel_all_orders(self) -> Dict[str, Any]:
        """
        Cancel all open orders.

        Returns:
            Dict with cancel result and count of canceled orders

        Raises:
            RuntimeError: If Exchange API not available
            Exception: If API call fails
        """
        if not settings.HYPERLIQUID_WALLET_ADDRESS:
            raise RuntimeError("Wallet address not configured")

        try:
            logger.info("Canceling all open orders")

            # Get all open orders first
            open_orders = self.list_open_orders()

            if not open_orders:
                logger.info("No open orders to cancel")
                return {
                    "status": "success",
                    "canceled_count": 0,
                    "result": {"message": "No open orders to cancel"},
                }

            # Cancel each order
            exchange = self.hyperliquid.get_exchange_client()
            results = []
            failed_orders = []

            for order in open_orders:
                coin = order.get("coin")
                oid = order.get("oid")
                try:
                    result = exchange.cancel(name=coin, oid=oid)
                    _parse_hyperliquid_response(result, f"Cancel order {coin}#{oid}")
                    results.append(result)
                    logger.debug(f"Canceled order {coin}#{oid}: {result}")
                except (ValueError, RuntimeError) as e:
                    logger.warning(f"Failed to cancel order {coin}#{oid}: {e}")
                    failed_orders.append({"coin": coin, "oid": oid, "error": str(e)})

            # If any orders failed to cancel, raise exception
            if failed_orders:
                raise RuntimeError(
                    f"Failed to cancel {len(failed_orders)} orders: {failed_orders}"
                )

            logger.info(f"Canceled {len(results)} orders")

            return {
                "status": "success",
                "canceled_count": len(results),
                "result": results,
            }

        except RuntimeError as e:
            logger.error(f"Runtime error canceling all orders: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            raise


# Global service instance
order_service = OrderService()
