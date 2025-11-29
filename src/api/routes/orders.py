"""
Orders API routes.
Handles order placement, cancellation, and management.
"""

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.models import CancelOrderResponse, OrderResponse
from src.config import logger
from src.services import order_service
from src.use_cases.trading import (
    CancelBulkOrdersRequest,
    CancelBulkOrdersUseCase,
    CancelOrderRequest,
    CancelOrderUseCase,
    ListOrdersRequest,
    ListOrdersUseCase,
    PlaceOrderRequest,
    PlaceOrderUseCase,
)

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# Initialize use cases
place_order_use_case = PlaceOrderUseCase()
list_orders_use_case = ListOrdersUseCase()
cancel_order_use_case = CancelOrderUseCase()
cancel_bulk_orders_use_case = CancelBulkOrdersUseCase()


class MarketOrderRequest(BaseModel):
    """Request body for placing a market order."""

    coin: str = Field(description="Trading pair symbol (e.g., BTC, ETH)")
    is_buy: bool = Field(description="True for buy, False for sell")
    size: float = Field(gt=0, description="Order size (must be positive)")
    slippage: float = Field(0.05, description="Maximum acceptable slippage (default 5%)")


class LimitOrderRequest(BaseModel):
    """Request body for placing a limit order."""

    coin: str = Field(description="Trading pair symbol (e.g., BTC, ETH)")
    is_buy: bool = Field(description="True for buy, False for sell")
    size: float = Field(gt=0, description="Order size (must be positive)")
    limit_price: float = Field(gt=0, description="Limit price (must be positive)")
    time_in_force: str = Field("Gtc", description="Time in force: Gtc, Ioc, or Alo")


@router.get("/")
async def list_open_orders(
    coin: str | None = Query(None, description="Filter by coin (e.g., BTC, ETH)"),
    side: str | None = Query(None, description="Filter by side (buy/sell)"),
    order_type: str | None = Query(None, description="Filter by order type (limit/market)"),
):
    """
    List all open orders with optional filters.

    Query Parameters:
        coin: Filter by coin symbol (e.g., BTC, ETH)
        side: Filter by side (buy or sell)
        order_type: Filter by order type (limit or market)

    Returns:
        List of open orders matching the filters
    """
    try:
        # Use the ListOrdersUseCase for consistent logic
        request = ListOrdersRequest(coin=coin, side=side, order_type=order_type)
        response = await list_orders_use_case.execute(request)

        if response.status == "failed":
            raise HTTPException(status_code=400, detail=response.message)

        # Return orders in a format consistent with the old endpoint
        return {
            "status": response.status,
            "total_count": response.total_count,
            "filters": response.filters_applied,
            "orders": [
                {
                    "coin": order.coin,
                    "oid": order.order_id,
                    "side": order.side,
                    "orderType": order.order_type,
                    "size": order.size,
                    "limitPx": order.limit_price,
                    "remainingSize": order.remaining_size,
                    "reduceOnly": order.reduce_only,
                }
                for order in response.orders
            ],
        }
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Runtime error listing orders: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to list open orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch open orders") from e


@router.post("/market", response_model=OrderResponse)
async def place_market_order(request: MarketOrderRequest = Body(...)):  # noqa: B008
    """
    Place a market order.

    Args:
        request: Market order parameters

    Returns:
        Order placement result

    Raises:
        400: Invalid parameters
        500: Exchange API error
    """
    try:
        # Adapt API request to use case request
        use_case_request = PlaceOrderRequest(  # type: ignore
            coin=request.coin,
            is_buy=request.is_buy,
            coin_size=request.size,  # API uses coin size directly
            is_market=True,
            slippage=request.slippage,
        )

        # Execute use case
        response = await place_order_use_case.execute(use_case_request)

        # Adapt use case response to API response format
        return {
            "status": response.status,
            "coin": response.coin,
            "side": response.side.lower(),
            "size": response.size,
            "order_type": response.order_type.lower(),
            "result": {
                "message": response.message,
                "usd_value": response.usd_value,
                "price": response.price,
            },
        }
    except ValueError as e:
        logger.error(f"Validation error placing market order: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        logger.error(f"Runtime error placing market order: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to place market order: {e}")
        raise HTTPException(status_code=500, detail="Failed to place market order") from e


@router.post("/limit", response_model=OrderResponse)
async def place_limit_order(request: LimitOrderRequest = Body(...)):  # noqa: B008
    """
    Place a limit order.

    Args:
        request: Limit order parameters

    Returns:
        Order placement result

    Raises:
        400: Invalid parameters
        500: Exchange API error
    """
    try:
        # Adapt API request to use case request
        use_case_request = PlaceOrderRequest(  # type: ignore
            coin=request.coin,
            is_buy=request.is_buy,
            coin_size=request.size,  # API uses coin size directly
            is_market=False,
            limit_price=request.limit_price,
            time_in_force=request.time_in_force,
        )

        # Execute use case
        response = await place_order_use_case.execute(use_case_request)

        # Adapt use case response to API response format
        return {
            "status": response.status,
            "coin": response.coin,
            "side": response.side.lower(),
            "size": response.size,
            "order_type": response.order_type.lower(),
            "limit_price": response.price,
            "time_in_force": request.time_in_force,
            "result": {
                "message": response.message,
                "usd_value": response.usd_value,
                "order_id": response.order_id,
            },
        }
    except ValueError as e:
        logger.error(f"Validation error placing limit order: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        logger.error(f"Runtime error placing limit order: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to place limit order: {e}")
        raise HTTPException(status_code=500, detail="Failed to place limit order") from e


@router.delete("/{coin}/{order_id}", response_model=CancelOrderResponse)
async def cancel_order(coin: str, order_id: int):
    """
    Cancel a specific order.

    Args:
        coin: Trading pair symbol
        order_id: Order ID to cancel

    Returns:
        Cancel operation result

    Raises:
        500: Exchange API error
    """
    try:
        # Use CancelOrderUseCase for consistent logic
        request = CancelOrderRequest(coin=coin, order_id=order_id)
        response = await cancel_order_use_case.execute(request)

        if response.status == "failed":
            raise HTTPException(status_code=400, detail=response.message)

        return {
            "status": response.status,
            "coin": response.coin,
            "order_id": response.order_id,
            "result": {"message": response.message},
        }
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"Runtime error canceling order: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel order") from e


class BulkCancelRequest(BaseModel):
    """Request body for bulk order cancellation."""

    order_ids: list[tuple[str, int]] = Field(
        default_factory=list,
        description="List of (coin, order_id) tuples to cancel. Empty if cancel_all=True",
    )
    cancel_all: bool = Field(
        False, description="If True, cancel ALL open orders (ignores order_ids)"
    )


@router.post("/cancel-bulk")
async def cancel_bulk_orders(request: BulkCancelRequest = Body(...)):  # noqa: B008
    """
    Cancel multiple orders at once or cancel all orders.

    Request Body:
        order_ids: List of [coin, order_id] pairs to cancel
        cancel_all: If true, cancel ALL open orders (ignores order_ids)

    Returns:
        Detailed results for each cancellation

    Raises:
        400: Invalid request
        500: Exchange API error

    Examples:
        Cancel specific orders:
        ```json
        {
            "order_ids": [["BTC", 12345], ["ETH", 67890]],
            "cancel_all": false
        }
        ```

        Cancel all orders:
        ```json
        {
            "cancel_all": true
        }
        ```
    """
    try:
        # Use CancelBulkOrdersUseCase
        use_case_request = CancelBulkOrdersRequest(
            order_ids=request.order_ids, cancel_all=request.cancel_all
        )
        response = await cancel_bulk_orders_use_case.execute(use_case_request)

        return {
            "status": response.status,
            "total_requested": response.total_requested,
            "successful": response.successful,
            "failed": response.failed,
            "message": response.message,
            "results": [
                {
                    "coin": result.coin,
                    "order_id": result.order_id,
                    "status": result.status,
                    "message": result.message,
                }
                for result in response.results
            ],
        }
    except ValueError as e:
        logger.error(f"Validation error in bulk cancel: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to cancel bulk orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel orders") from e


@router.delete("/all", response_model=CancelOrderResponse)
async def cancel_all_orders():
    """
    Cancel all open orders.

    Returns:
        Cancel operation result

    Raises:
        500: Exchange API error
    """
    try:
        result = order_service.cancel_all_orders()
        return result
    except RuntimeError as e:
        logger.error(f"Runtime error canceling all orders: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to cancel all orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel all orders") from e
