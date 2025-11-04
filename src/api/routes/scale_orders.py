"""
API routes for scale order management.
"""
from fastapi import APIRouter, HTTPException, status
from typing import List
from src.models.scale_order import (
    ScaleOrderConfig,
    ScaleOrderPreview,
    ScaleOrderResult,
    ScaleOrder,
    ScaleOrderCancel,
    ScaleOrderStatus,
)
from src.services.scale_order_service import scale_order_service
from src.config import logger


router = APIRouter(prefix="/api/scale-orders", tags=["scale_orders"])


@router.post("/preview", response_model=ScaleOrderPreview, status_code=status.HTTP_200_OK)
async def preview_scale_order(config: ScaleOrderConfig):
    """
    Preview a scale order before placing it.

    Returns calculated price levels, sizes, and estimated average price.

    Example Request:
    ```json
    {
        "coin": "BTC",
        "is_buy": true,
        "total_size": 1.0,
        "num_orders": 5,
        "start_price": 50000.0,
        "end_price": 48000.0,
        "distribution_type": "linear",
        "time_in_force": "Gtc"
    }
    ```

    Example Response:
    ```json
    {
        "coin": "BTC",
        "is_buy": true,
        "total_size": 1.0,
        "num_orders": 5,
        "orders": [
            {"price": 50000.0, "size": 0.2, "notional": 10000.0},
            {"price": 49500.0, "size": 0.2, "notional": 9900.0},
            ...
        ],
        "estimated_avg_price": 49000.0,
        "price_range_pct": 4.0
    }
    ```
    """
    logger.info(
        f"Scale order preview requested: {config.coin} "
        f"{'BUY' if config.is_buy else 'SELL'} "
        f"{config.total_size} across {config.num_orders} orders"
    )

    try:
        preview = await scale_order_service.preview_scale_order(config)

        logger.info(
            f"Preview generated: {len(preview.orders)} orders, "
            f"avg_price=${preview.estimated_avg_price:.2f}, "
            f"range={preview.price_range_pct:.2f}%"
        )

        return preview

    except ValueError as e:
        logger.warning(f"Invalid scale order configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to generate scale order preview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate preview: {str(e)}"
        )


@router.post("/place", response_model=ScaleOrderResult, status_code=status.HTTP_201_CREATED)
async def place_scale_order(config: ScaleOrderConfig):
    """
    Place a scale order (multiple limit orders at different price levels).

    This will place multiple limit orders distributed across the specified price range.

    Example Request:
    ```json
    {
        "coin": "BTC",
        "is_buy": true,
        "total_size": 1.0,
        "num_orders": 5,
        "start_price": 50000.0,
        "end_price": 48000.0,
        "distribution_type": "linear",
        "reduce_only": false,
        "time_in_force": "Gtc"
    }
    ```

    Example Response:
    ```json
    {
        "scale_order_id": "550e8400-e29b-41d4-a716-446655440000",
        "coin": "BTC",
        "is_buy": true,
        "total_size": 1.0,
        "num_orders": 5,
        "placements": [
            {"order_id": 12345, "price": 50000.0, "size": 0.2, "status": "success"},
            ...
        ],
        "orders_placed": 5,
        "orders_failed": 0,
        "average_price": 49000.0,
        "total_placed_size": 1.0,
        "status": "completed",
        "created_at": "2025-11-04T00:00:00"
    }
    ```
    """
    logger.info(
        f"Scale order placement requested: {config.coin} "
        f"{'BUY' if config.is_buy else 'SELL'} "
        f"{config.total_size} across {config.num_orders} orders "
        f"from ${config.start_price} to ${config.end_price}"
    )

    try:
        result = await scale_order_service.place_scale_order(config)

        if result.status == "failed":
            logger.error(
                f"Scale order placement failed: {result.orders_failed}/{result.num_orders} orders failed"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"All orders failed. Check placements for details."
            )

        logger.info(
            f"Scale order placed: {result.orders_placed}/{result.num_orders} successful, "
            f"status={result.status}"
        )

        return result

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid scale order configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Runtime error placing scale order: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to place scale order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to place scale order: {str(e)}"
        )


@router.get("/", response_model=List[ScaleOrder], status_code=status.HTTP_200_OK)
async def list_scale_orders():
    """
    List all scale orders.

    Returns a list of all scale order groups, including their status and order IDs.

    Example Response:
    ```json
    [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "coin": "BTC",
            "is_buy": true,
            "total_size": 1.0,
            "num_orders": 5,
            "start_price": 50000.0,
            "end_price": 48000.0,
            "distribution_type": "linear",
            "order_ids": [12345, 12346, 12347, 12348, 12349],
            "orders_placed": 5,
            "orders_filled": 2,
            "total_filled_size": 0.4,
            "average_fill_price": 49200.0,
            "status": "active",
            "created_at": "2025-11-04T00:00:00",
            "updated_at": "2025-11-04T00:10:00"
        }
    ]
    ```
    """
    logger.info("Listing all scale orders")

    try:
        scale_orders = scale_order_service.list_scale_orders()

        logger.info(f"Retrieved {len(scale_orders)} scale orders")

        return scale_orders

    except Exception as e:
        logger.error(f"Failed to list scale orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scale orders: {str(e)}"
        )


@router.get("/{scale_order_id}", response_model=ScaleOrderStatus, status_code=status.HTTP_200_OK)
async def get_scale_order_status(scale_order_id: str):
    """
    Get status of a specific scale order.

    Returns detailed status including which orders are still open and which have filled.

    Example Response:
    ```json
    {
        "scale_order": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "coin": "BTC",
            ...
        },
        "open_orders": [
            {"oid": 12345, "coin": "BTC", "side": "B", "sz": "0.2", "limitPx": "50000.0"},
            ...
        ],
        "filled_orders": [
            {"order_id": 12348},
            {"order_id": 12349}
        ],
        "fill_percentage": 40.0
    }
    ```
    """
    logger.info(f"Getting status for scale order: {scale_order_id}")

    try:
        status_info = await scale_order_service.get_scale_order_status(scale_order_id)

        logger.info(
            f"Scale order {scale_order_id}: "
            f"{status_info.scale_order.orders_filled}/{status_info.scale_order.orders_placed} filled "
            f"({status_info.fill_percentage:.1f}%)"
        )

        return status_info

    except ValueError as e:
        logger.warning(f"Scale order not found: {scale_order_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get scale order status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scale order status: {str(e)}"
        )


@router.delete("/{scale_order_id}", status_code=status.HTTP_200_OK)
async def cancel_scale_order(scale_order_id: str, cancel_all_orders: bool = True):
    """
    Cancel a scale order.

    This will cancel all open orders in the scale order group.

    Query Parameters:
    - cancel_all_orders: Whether to cancel all open orders (default: true)

    Example Response:
    ```json
    {
        "scale_order_id": "550e8400-e29b-41d4-a716-446655440000",
        "orders_cancelled": 3,
        "total_orders": 5,
        "errors": null,
        "status": "cancelled"
    }
    ```
    """
    logger.info(
        f"Cancel scale order requested: {scale_order_id} "
        f"(cancel_all_orders={cancel_all_orders})"
    )

    try:
        cancel_request = ScaleOrderCancel(
            scale_order_id=scale_order_id,
            cancel_all_orders=cancel_all_orders
        )

        result = await scale_order_service.cancel_scale_order(cancel_request)

        logger.info(
            f"Scale order {scale_order_id} cancelled: "
            f"{result['orders_cancelled']}/{result.get('total_orders', 0)} orders cancelled"
        )

        return result

    except ValueError as e:
        logger.warning(f"Scale order not found: {scale_order_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        logger.error(f"Runtime error cancelling scale order: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to cancel scale order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel scale order: {str(e)}"
        )
