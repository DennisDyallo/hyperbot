"""
Scale Order Service for placing multiple limit orders at different price levels.

Scale orders allow gradual position building or exit by placing a series of
limit orders distributed across a price range.
"""

from datetime import datetime

from src.config import logger
from src.models.scale_order import (
    OrderPlacement,
    ScaleOrder,
    ScaleOrderCancel,
    ScaleOrderConfig,
    ScaleOrderPreview,
    ScaleOrderResult,
    ScaleOrderStatus,
)
from src.services.hyperliquid_service import hyperliquid_service


class ScaleOrderService:
    """Service for managing scale orders."""

    def __init__(self):
        """Initialize scale order service."""
        self.hyperliquid = hyperliquid_service
        # In-memory storage for scale orders (in production, use database)
        self._scale_orders: dict[str, ScaleOrder] = {}

    def _calculate_price_levels(
        self, start_price: float, end_price: float, num_orders: int
    ) -> list[float]:
        """
        Calculate price levels for scale order.

        Args:
            start_price: Starting price
            end_price: Ending price
            num_orders: Number of price levels

        Returns:
            List of price levels
        """
        if num_orders == 1:
            return [start_price]

        # Linear distribution
        price_step = (end_price - start_price) / (num_orders - 1)
        return [start_price + (i * price_step) for i in range(num_orders)]

    def _calculate_geometric_sizes(
        self,
        total_usd_amount: float,
        price_levels: list[float],
        num_orders: int,
        ratio: float = 1.5,
    ) -> list[float]:
        """
        Calculate sizes with geometric distribution (weighted USD towards first orders).

        Args:
            total_usd_amount: Total USD amount to distribute
            price_levels: Price levels for each order
            num_orders: Number of orders
            ratio: Geometric ratio (default 1.5 = each order gets 1.5x USD of previous)

        Returns:
            List of coin sizes (weighted USD distribution)
        """
        if num_orders == 1:
            return [total_usd_amount / price_levels[0]]

        # Calculate geometric series sum for USD distribution
        # S = a * (1 - r^n) / (1 - r)
        # We need to find 'a' such that S = total_usd_amount
        geometric_sum = (1 - ratio**num_orders) / (1 - ratio)
        first_usd = total_usd_amount / geometric_sum

        # Generate USD amounts per order
        usd_amounts = [first_usd * (ratio**i) for i in range(num_orders)]

        # Ensure exact total (adjust for floating point errors)
        actual_total_usd = sum(usd_amounts)
        if actual_total_usd != total_usd_amount:
            adjustment = total_usd_amount / actual_total_usd
            usd_amounts = [u * adjustment for u in usd_amounts]

        # Convert USD amounts to coin sizes at each price level
        sizes = [usd / price for usd, price in zip(usd_amounts, price_levels, strict=False)]

        return sizes

    def _calculate_linear_sizes(
        self, total_usd_amount: float, price_levels: list[float], num_orders: int
    ) -> list[float]:
        """
        Calculate sizes with linear distribution (equal USD per order).

        Args:
            total_usd_amount: Total USD amount to distribute
            price_levels: Price levels for each order
            num_orders: Number of orders

        Returns:
            List of coin sizes (equal USD per order)
        """
        usd_per_order = total_usd_amount / num_orders
        # Convert USD to coin size at each price level
        sizes = [usd_per_order / price for price in price_levels]
        return sizes

    def _round_price(self, price: float, tick_size: float = 0.01) -> float:
        """
        Round price to valid tick size.

        Args:
            price: Price to round
            tick_size: Minimum price increment

        Returns:
            Rounded price
        """
        return round(price / tick_size) * tick_size

    def _round_size(self, size: float, size_decimals: int = 4) -> float:
        """
        Round size to valid decimals.

        Args:
            size: Size to round
            size_decimals: Number of decimal places

        Returns:
            Rounded size
        """
        return round(size, size_decimals)

    async def preview_scale_order(self, config: ScaleOrderConfig) -> ScaleOrderPreview:
        """
        Preview a scale order before placing it.

        Args:
            config: Scale order configuration

        Returns:
            Preview of the scale order

        Example:
            >>> config = ScaleOrderConfig(
            ...     coin="BTC",
            ...     is_buy=True,
            ...     total_usd_amount=50000.0,
            ...     num_orders=5,
            ...     start_price=50000,
            ...     end_price=48000
            ... )
            >>> preview = await service.preview_scale_order(config)
            >>> print(f"Avg price: ${preview.estimated_avg_price:.2f}")
        """
        logger.info(
            f"Previewing scale order: {config.coin} "
            f"{'BUY' if config.is_buy else 'SELL'} "
            f"${config.total_usd_amount} across {config.num_orders} orders"
        )

        # Calculate price levels
        price_levels = self._calculate_price_levels(
            config.start_price, config.end_price, config.num_orders
        )

        # Calculate sizes (coin quantities from USD amounts)
        if config.distribution_type == "geometric":
            sizes = self._calculate_geometric_sizes(
                config.total_usd_amount, price_levels, config.num_orders, config.geometric_ratio
            )
        else:
            sizes = self._calculate_linear_sizes(
                config.total_usd_amount, price_levels, config.num_orders
            )

        # Round values
        price_levels = [self._round_price(p) for p in price_levels]
        sizes = [self._round_size(s) for s in sizes]

        # Calculate total coin size
        total_coin_size = sum(sizes)

        # Create order list
        orders = [
            {"price": price, "size": size, "notional": price * size}
            for price, size in zip(price_levels, sizes, strict=False)
        ]

        # Calculate estimated average price
        total_notional = sum(o["notional"] for o in orders)
        estimated_avg_price = total_notional / total_coin_size

        # Calculate price range percentage
        price_range_pct = abs(config.end_price - config.start_price) / config.start_price * 100

        return ScaleOrderPreview(
            coin=config.coin,
            is_buy=config.is_buy,
            total_usd_amount=config.total_usd_amount,
            total_coin_size=total_coin_size,
            num_orders=config.num_orders,
            orders=orders,
            estimated_avg_price=estimated_avg_price,
            price_range_pct=price_range_pct,
        )

    async def place_scale_order(self, config: ScaleOrderConfig) -> ScaleOrderResult:
        """
        Place a scale order.

        Args:
            config: Scale order configuration

        Returns:
            Result of placing the scale order

        Raises:
            RuntimeError: If service not initialized
            ValueError: If configuration invalid

        Example:
            >>> config = ScaleOrderConfig(
            ...     coin="BTC",
            ...     is_buy=True,
            ...     total_usd_amount=50000.0,
            ...     num_orders=5,
            ...     start_price=50000,
            ...     end_price=48000
            ... )
            >>> result = await service.place_scale_order(config)
            >>> print(f"Placed {result.orders_placed}/{result.num_orders} orders")
        """
        logger.info(
            f"Placing scale order: {config.coin} "
            f"{'BUY' if config.is_buy else 'SELL'} "
            f"${config.total_usd_amount} across {config.num_orders} orders "
            f"from ${config.start_price} to ${config.end_price}"
        )

        # Ensure Hyperliquid service is initialized
        if not self.hyperliquid.is_initialized():
            await self.hyperliquid.initialize()  # type: ignore

        # Get preview to calculate orders
        preview = await self.preview_scale_order(config)

        # Place each order
        placements: list[OrderPlacement] = []
        successful_order_ids: list[int] = []

        for order in preview.orders:
            try:
                # Place limit order
                result = await self.hyperliquid.place_limit_order(
                    coin=config.coin,
                    is_buy=config.is_buy,
                    size=order["size"],
                    price=order["price"],
                    reduce_only=config.reduce_only,
                    time_in_force=config.time_in_force,
                )

                # Handle result - ensure it's a dict
                if not isinstance(result, dict):
                    raise ValueError(f"Unexpected result type: {type(result)}, value: {result}")

                # Check if successful
                if result.get("status") == "ok":
                    # Extract order ID from response
                    statuses = result.get("response", {}).get("data", {}).get("statuses", [])
                    if statuses and "resting" in statuses[0]:
                        order_id = statuses[0]["resting"]["oid"]
                        successful_order_ids.append(order_id)

                        placements.append(
                            OrderPlacement(  # type: ignore
                                order_id=order_id,
                                price=order["price"],
                                size=order["size"],
                                status="success",
                            )
                        )
                        logger.info(
                            f"✓ Order {len(placements)}/{config.num_orders}: "
                            f"{config.coin} {order['size']} @ ${order['price']}"
                        )
                    else:
                        # Order executed immediately (filled)
                        placements.append(
                            OrderPlacement(  # type: ignore
                                order_id=None,
                                price=order["price"],
                                size=order["size"],
                                status="success",
                            )
                        )
                        logger.info(
                            f"✓ Order {len(placements)}/{config.num_orders}: "
                            f"{config.coin} {order['size']} @ ${order['price']} (filled immediately)"
                        )
                else:
                    # Order failed
                    error_msg = result.get("response", {}).get("message", "Unknown error")
                    placements.append(
                        OrderPlacement(
                            order_id=None,
                            price=order["price"],
                            size=order["size"],
                            status="failed",
                            error=error_msg,
                        )
                    )
                    logger.warning(
                        f"✗ Order {len(placements)}/{config.num_orders} failed: {error_msg}"
                    )

            except Exception as e:
                logger.error(f"Failed to place order at ${order['price']}: {e}")
                placements.append(
                    OrderPlacement(
                        order_id=None,
                        price=order["price"],
                        size=order["size"],
                        status="failed",
                        error=str(e),
                    )
                )

        # Calculate results
        orders_placed = sum(1 for p in placements if p.status == "success")
        orders_failed = sum(1 for p in placements if p.status == "failed")
        total_placed_size = sum(p.size for p in placements if p.status == "success")

        # Calculate average price of placed orders
        average_price = None
        if orders_placed > 0:
            total_notional = sum(p.price * p.size for p in placements if p.status == "success")
            average_price = total_notional / total_placed_size

        # Determine overall status
        if orders_placed == config.num_orders:
            status = "completed"
        elif orders_placed > 0:
            status = "partial"
        else:
            status = "failed"

        # Create result
        result = ScaleOrderResult(
            coin=config.coin,
            is_buy=config.is_buy,
            total_usd_amount=config.total_usd_amount,
            total_coin_size=preview.total_coin_size,
            num_orders=config.num_orders,
            placements=placements,
            orders_placed=orders_placed,
            orders_failed=orders_failed,
            average_price=average_price,
            total_placed_size=total_placed_size,
            status=status,  # type: ignore
        )

        # Store scale order
        scale_order = ScaleOrder(
            id=result.scale_order_id,  # type: ignore
            coin=config.coin,
            is_buy=config.is_buy,
            total_usd_amount=config.total_usd_amount,
            total_coin_size=preview.total_coin_size,
            num_orders=config.num_orders,
            start_price=config.start_price,
            end_price=config.end_price,
            distribution_type=config.distribution_type,
            order_ids=successful_order_ids,
            orders_placed=orders_placed,
            status="active" if status in ["completed", "partial"] else "failed",
        )
        self._scale_orders[scale_order.id] = scale_order

        logger.info(
            f"Scale order {result.scale_order_id}: "  # type: ignore
            f"{orders_placed}/{config.num_orders} orders placed, "
            f"status={status}"
        )

        return result  # type: ignore

    async def cancel_scale_order(self, cancel_request: ScaleOrderCancel) -> dict:
        """
        Cancel a scale order (cancel all open orders in the group).

        Args:
            cancel_request: Cancel request

        Returns:
            Dict with cancellation results

        Raises:
            ValueError: If scale order not found
        """
        scale_order_id = cancel_request.scale_order_id

        if scale_order_id not in self._scale_orders:
            raise ValueError(f"Scale order {scale_order_id} not found")

        scale_order = self._scale_orders[scale_order_id]

        logger.info(f"Cancelling scale order {scale_order_id}")

        if not cancel_request.cancel_all_orders:
            # Just mark as cancelled
            scale_order.status = "cancelled"
            scale_order.updated_at = datetime.now()
            return {"scale_order_id": scale_order_id, "orders_cancelled": 0, "status": "cancelled"}

        # Cancel all open orders
        cancelled_count = 0
        errors = []

        for order_id in scale_order.order_ids:
            try:
                result = await self.hyperliquid.cancel_order(
                    coin=scale_order.coin, order_id=order_id
                )

                if result.get("status") == "ok":
                    cancelled_count += 1
                else:
                    errors.append(
                        f"Order {order_id}: {result.get('response', {}).get('message', 'Unknown error')}"
                    )

            except Exception as e:
                logger.error(f"Failed to cancel order {order_id}: {e}")
                errors.append(f"Order {order_id}: {str(e)}")

        # Update scale order status
        scale_order.status = "cancelled"
        scale_order.updated_at = datetime.now()

        logger.info(
            f"Cancelled {cancelled_count}/{len(scale_order.order_ids)} orders "
            f"for scale order {scale_order_id}"
        )

        return {
            "scale_order_id": scale_order_id,
            "orders_cancelled": cancelled_count,
            "total_orders": len(scale_order.order_ids),
            "errors": errors if errors else None,
            "status": "cancelled",
        }

    async def get_scale_order_status(self, scale_order_id: str) -> ScaleOrderStatus:
        """
        Get status of a scale order.

        Args:
            scale_order_id: ID of the scale order

        Returns:
            Status information

        Raises:
            ValueError: If scale order not found
        """
        if scale_order_id not in self._scale_orders:
            raise ValueError(f"Scale order {scale_order_id} not found")

        scale_order = self._scale_orders[scale_order_id]

        # Get current open orders
        open_orders_response = await self.hyperliquid.get_open_orders()
        all_open_orders = open_orders_response

        # Filter for this scale order's orders
        open_orders = [
            order for order in all_open_orders if order.get("oid") in scale_order.order_ids
        ]

        # Calculate filled orders (orders that were placed but no longer open)
        open_order_ids = {o.get("oid") for o in open_orders}
        filled_order_ids = [oid for oid in scale_order.order_ids if oid not in open_order_ids]

        # Update scale order metrics
        scale_order.orders_filled = len(filled_order_ids)

        # Calculate fill percentage
        fill_percentage = (
            (scale_order.orders_filled / scale_order.orders_placed * 100)
            if scale_order.orders_placed > 0
            else 0
        )

        # Update status if all filled
        if (
            scale_order.orders_filled == scale_order.orders_placed
            and scale_order.status == "active"
        ):
            scale_order.status = "completed"
            scale_order.completed_at = datetime.now()
            scale_order.updated_at = datetime.now()

        return ScaleOrderStatus(
            scale_order=scale_order,
            open_orders=open_orders,
            filled_orders=[{"order_id": oid} for oid in filled_order_ids],
            fill_percentage=fill_percentage,
        )

    def list_scale_orders(self) -> list[ScaleOrder]:
        """
        List all scale orders.

        Returns:
            List of scale orders
        """
        return list(self._scale_orders.values())

    def get_scale_order(self, scale_order_id: str) -> ScaleOrder | None:
        """
        Get a specific scale order by ID.

        Args:
            scale_order_id: ID of the scale order

        Returns:
            Scale order if found, None otherwise
        """
        return self._scale_orders.get(scale_order_id)


# Global service instance
scale_order_service = ScaleOrderService()
