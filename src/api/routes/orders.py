"""
Orders API routes.
Handles order placement, cancellation, and management.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from src.services import order_service
from src.api.models import OrderResponse, CancelOrderResponse
from src.use_cases.trading import PlaceOrderUseCase, PlaceOrderRequest
from src.config import logger

router = APIRouter(prefix="/api/orders", tags=["Orders"])

# Initialize use cases
place_order_use_case = PlaceOrderUseCase()


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
async def list_open_orders():
    """
    List all open orders.

    Returns:
        List of open orders
    """
    try:
        orders = order_service.list_open_orders()
        return orders
    except RuntimeError as e:
        logger.error(f"Runtime error listing orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to list open orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch open orders")


@router.post("/market", response_model=OrderResponse)
async def place_market_order(request: MarketOrderRequest = Body(...)):
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
        use_case_request = PlaceOrderRequest(
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
            }
        }
    except ValueError as e:
        logger.error(f"Validation error placing market order: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Runtime error placing market order: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to place market order: {e}")
        raise HTTPException(status_code=500, detail="Failed to place market order")


@router.post("/limit", response_model=OrderResponse)
async def place_limit_order(request: LimitOrderRequest = Body(...)):
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
        use_case_request = PlaceOrderRequest(
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
            }
        }
    except ValueError as e:
        logger.error(f"Validation error placing limit order: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Runtime error placing limit order: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to place limit order: {e}")
        raise HTTPException(status_code=500, detail="Failed to place limit order")


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
        result = order_service.cancel_order(coin=coin, order_id=order_id)
        return result
    except RuntimeError as e:
        logger.error(f"Runtime error canceling order: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel order")


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
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel all orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel all orders")
