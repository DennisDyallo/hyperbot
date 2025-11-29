"""
List Orders Use Case.

Unified logic for listing outstanding (open/unfilled) orders across all interfaces.
Supports filtering by coin, side, and order type.
"""

from typing import Any

from pydantic import BaseModel, Field

from src.config import logger
from src.services.order_service import order_service
from src.use_cases.base import BaseUseCase


class ListOrdersRequest(BaseModel):
    """Request model for listing orders."""

    coin: str | None = Field(None, description="Filter by coin (e.g., BTC, ETH). None = all coins")
    side: str | None = Field(None, description="Filter by side (buy/sell). None = both sides")
    order_type: str | None = Field(
        None, description="Filter by order type (limit/market). None = all types"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "coin": "BTC",
                "side": "buy",
                "order_type": "limit",
            }
        }


class OrderInfo(BaseModel):
    """Information about a single order."""

    coin: str = Field(..., description="Asset symbol")
    order_id: int = Field(..., description="Order ID")
    side: str = Field(..., description="Order side (buy/sell)")
    order_type: str = Field(..., description="Order type (limit/market)")
    size: float = Field(..., description="Order size")
    limit_price: float | None = Field(None, description="Limit price (if limit order)")
    filled_size: float = Field(0.0, description="Filled size")
    remaining_size: float = Field(..., description="Remaining size to fill")
    timestamp: int | None = Field(None, description="Order timestamp")
    reduce_only: bool = Field(False, description="Reduce-only flag")

    class Config:
        json_schema_extra = {
            "example": {
                "coin": "BTC",
                "order_id": 12345,
                "side": "buy",
                "order_type": "limit",
                "size": 0.5,
                "limit_price": 45000.0,
                "filled_size": 0.0,
                "remaining_size": 0.5,
                "timestamp": 1732896000000,
                "reduce_only": False,
            }
        }


class ListOrdersResponse(BaseModel):
    """Response model for listing orders."""

    status: str = Field(..., description="Operation status (success/failed)")
    orders: list[OrderInfo] = Field(..., description="List of orders matching filters")
    total_count: int = Field(..., description="Total number of orders")
    filters_applied: dict[str, str | None] = Field(..., description="Filters that were applied")
    message: str = Field(..., description="Success/error message")


class ListOrdersUseCase(BaseUseCase[ListOrdersRequest, ListOrdersResponse]):
    """
    Use case for listing outstanding orders with optional filters.

    Features:
    - List all open/unfilled orders
    - Filter by coin symbol
    - Filter by side (buy/sell)
    - Filter by order type (limit/market)
    - Normalized response format across all interfaces

    Example:
        >>> request = ListOrdersRequest(coin="BTC", side="buy")
        >>> use_case = ListOrdersUseCase()
        >>> response = await use_case.execute(request)
        >>> print(f"Found {response.total_count} BTC buy orders")
    """

    def __init__(self):
        """Initialize use case with required services."""
        self.order_service = order_service

    async def execute(self, request: ListOrdersRequest) -> ListOrdersResponse:
        """
        Execute list orders use case.

        Args:
            request: List orders request with optional filters

        Returns:
            ListOrdersResponse with orders and metadata

        Raises:
            ValueError: If invalid filter values provided
            RuntimeError: If wallet not configured
            Exception: If API call fails
        """
        try:
            logger.info(
                f"Listing orders with filters: coin={request.coin}, "
                f"side={request.side}, type={request.order_type}"
            )

            # Fetch orders with filters
            raw_orders = self.order_service.list_open_orders(
                coin=request.coin,
                side=request.side,
                order_type=request.order_type,
            )

            # Parse orders into normalized format
            orders = []
            for raw_order in raw_orders:
                try:
                    order_info = self._parse_order(raw_order)
                    orders.append(order_info)
                except Exception as e:
                    logger.warning(f"Failed to parse order: {e}. Raw: {raw_order}")
                    continue

            logger.info(f"Found {len(orders)} orders matching filters")

            return ListOrdersResponse(
                status="success",
                orders=orders,
                total_count=len(orders),
                filters_applied={
                    "coin": request.coin,
                    "side": request.side,
                    "order_type": request.order_type,
                },
                message=f"Found {len(orders)} order{'s' if len(orders) != 1 else ''}",
            )

        except ValueError as e:
            logger.error(f"Validation error listing orders: {e}")
            return ListOrdersResponse(
                status="failed",
                orders=[],
                total_count=0,
                filters_applied={
                    "coin": request.coin,
                    "side": request.side,
                    "order_type": request.order_type,
                },
                message=f"Invalid filter: {str(e)}",
            )

        except Exception as e:
            logger.error(f"Failed to list orders: {e}")
            return ListOrdersResponse(
                status="failed",
                orders=[],
                total_count=0,
                filters_applied={
                    "coin": request.coin,
                    "side": request.side,
                    "order_type": request.order_type,
                },
                message=f"Error: {str(e)}",
            )

    def _parse_order(self, raw_order: dict[str, Any]) -> OrderInfo:
        """
        Parse raw order data from Hyperliquid API into OrderInfo model.

        Args:
            raw_order: Raw order dict from API

        Returns:
            Parsed OrderInfo object

        Raises:
            KeyError: If required fields missing
            ValueError: If data format invalid
        """
        # Extract side (B = Buy, A = Ask/Sell)
        side_code = raw_order.get("side", "")
        side = "buy" if side_code == "B" else "sell"

        # Extract order type from nested structure
        order_type_obj = raw_order.get("orderType", {})
        if isinstance(order_type_obj, dict):
            # {"limit": {"tif": "Gtc"}} -> "limit"
            order_type = next(iter(order_type_obj.keys()), "unknown")
        else:
            order_type = str(order_type_obj).lower()

        # Extract sizes
        size = float(raw_order.get("sz", 0))
        filled_size = size - float(raw_order.get("szDecimals", size))  # Approximation
        remaining_size = float(raw_order.get("szDecimals", size))

        # Extract limit price (if limit order)
        limit_price = None
        if "limitPx" in raw_order:
            limit_price = float(raw_order["limitPx"])

        return OrderInfo(
            coin=raw_order["coin"],
            order_id=int(raw_order["oid"]),
            side=side,
            order_type=order_type,
            size=size,
            limit_price=limit_price,
            filled_size=filled_size,
            remaining_size=remaining_size,
            timestamp=raw_order.get("timestamp"),
            reduce_only=raw_order.get("reduceOnly", False),
        )
