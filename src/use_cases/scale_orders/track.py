"""
Track Scale Order Use Case.

Unified logic for tracking and managing scale orders.
Provides status, fill progress, and cancellation functionality.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from src.use_cases.base import BaseUseCase
from src.models.scale_order import ScaleOrder, ScaleOrderStatus, ScaleOrderCancel
from src.services.scale_order_service import scale_order_service
from src.config import logger


# ============================================================================
# List Scale Orders
# ============================================================================

class ListScaleOrdersRequest(BaseModel):
    """Request model for listing scale orders."""
    coin: Optional[str] = Field(None, description="Filter by coin (optional)")
    active_only: bool = Field(True, description="Only show active scale orders")

    class Config:
        json_schema_extra = {
            "example": {
                "coin": None,
                "active_only": True
            }
        }


class ListScaleOrdersResponse(BaseModel):
    """Response model for listing scale orders."""
    scale_orders: List[ScaleOrder]
    total_count: int
    active_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "scale_orders": [
                    {
                        "scale_order_id": "scale_123",
                        "coin": "BTC",
                        "is_buy": True,
                        "num_orders": 5,
                        "created_at": "2025-11-05T20:00:00Z"
                    }
                ],
                "total_count": 1,
                "active_count": 1
            }
        }


class ListScaleOrdersUseCase(BaseUseCase[ListScaleOrdersRequest, ListScaleOrdersResponse]):
    """
    Use case for listing scale orders with unified logic for API and Bot.

    Features:
    - Lists all scale orders or filters by coin
    - Option to show only active orders
    - Provides counts for tracking

    Example:
        >>> request = ListScaleOrdersRequest(active_only=True)
        >>> use_case = ListScaleOrdersUseCase()
        >>> response = await use_case.execute(request)
        >>> print(f"Found {response.active_count} active scale orders")
    """

    def __init__(self):
        """Initialize use case with scale order service."""
        self.scale_order_service = scale_order_service

    async def execute(self, request: ListScaleOrdersRequest) -> ListScaleOrdersResponse:
        """
        Execute list scale orders use case.

        Args:
            request: List request with optional filters

        Returns:
            List response with scale orders and counts

        Raises:
            RuntimeError: If listing fails
        """
        try:
            logger.debug(f"Listing scale orders: coin={request.coin}, active_only={request.active_only}")

            # Get all scale orders from service
            all_orders = self.scale_order_service.list_scale_orders()

            # Apply filters
            filtered_orders = all_orders

            if request.coin:
                filtered_orders = [o for o in filtered_orders if o.coin == request.coin]

            if request.active_only:
                # Active = has at least one open order
                filtered_orders = [
                    o for o in filtered_orders
                    if any(p.order_id for p in o.orders_placed if p.order_id)
                ]

            active_count = len([
                o for o in all_orders
                if any(p.order_id for p in o.orders_placed if p.order_id)
            ])

            logger.debug(
                f"Found {len(filtered_orders)} scale orders "
                f"({active_count} active)"
            )

            return ListScaleOrdersResponse(
                scale_orders=filtered_orders,
                total_count=len(all_orders),
                active_count=active_count
            )

        except Exception as e:
            logger.error(f"Failed to list scale orders: {e}")
            raise RuntimeError(f"Failed to list scale orders: {str(e)}")


# ============================================================================
# Get Scale Order Status
# ============================================================================

class GetScaleOrderStatusRequest(BaseModel):
    """Request model for getting scale order status."""
    scale_order_id: str = Field(..., description="Scale order ID")

    class Config:
        json_schema_extra = {
            "example": {
                "scale_order_id": "scale_123"
            }
        }


class GetScaleOrderStatusResponse(BaseModel):
    """Response model for scale order status."""
    status: ScaleOrderStatus

    class Config:
        json_schema_extra = {
            "example": {
                "status": {
                    "scale_order_id": "scale_123",
                    "coin": "BTC",
                    "is_buy": True,
                    "num_orders": 5,
                    "open_orders": 3,
                    "filled_orders": 2,
                    "cancelled_orders": 0,
                    "fill_percentage": 40.0,
                    "created_at": "2025-11-05T20:00:00Z"
                }
            }
        }


class GetScaleOrderStatusUseCase(BaseUseCase[GetScaleOrderStatusRequest, GetScaleOrderStatusResponse]):
    """
    Use case for getting scale order status with unified logic for API and Bot.

    Features:
    - Retrieves current status of scale order
    - Shows fill progress and open orders
    - Includes order details and timestamps

    Example:
        >>> request = GetScaleOrderStatusRequest(scale_order_id="scale_123")
        >>> use_case = GetScaleOrderStatusUseCase()
        >>> response = await use_case.execute(request)
        >>> print(f"Fill progress: {response.status.fill_percentage:.1f}%")
    """

    def __init__(self):
        """Initialize use case with scale order service."""
        self.scale_order_service = scale_order_service

    async def execute(self, request: GetScaleOrderStatusRequest) -> GetScaleOrderStatusResponse:
        """
        Execute get scale order status use case.

        Args:
            request: Status request with scale order ID

        Returns:
            Status response with current state

        Raises:
            ValueError: If scale order not found
            RuntimeError: If status check fails
        """
        try:
            logger.debug(f"Getting status for scale order: {request.scale_order_id}")

            # Get status from service
            status = await self.scale_order_service.get_scale_order_status(request.scale_order_id)

            if not status:
                raise ValueError(f"Scale order not found: {request.scale_order_id}")

            logger.debug(
                f"Scale order {request.scale_order_id}: "
                f"{status.filled_orders}/{status.num_orders} filled "
                f"({status.fill_percentage:.1f}%)"
            )

            return GetScaleOrderStatusResponse(status=status)

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to get scale order status: {e}")
            raise RuntimeError(f"Failed to get scale order status: {str(e)}")


# ============================================================================
# Cancel Scale Order
# ============================================================================

class CancelScaleOrderRequest(BaseModel):
    """Request model for cancelling scale order."""
    scale_order_id: str = Field(..., description="Scale order ID")

    class Config:
        json_schema_extra = {
            "example": {
                "scale_order_id": "scale_123"
            }
        }


class CancelScaleOrderResponse(BaseModel):
    """Response model for scale order cancellation."""
    result: ScaleOrderCancel

    class Config:
        json_schema_extra = {
            "example": {
                "result": {
                    "scale_order_id": "scale_123",
                    "orders_cancelled": 3,
                    "cancellation_errors": [],
                    "success": True,
                    "message": "Successfully cancelled 3 orders"
                }
            }
        }


class CancelScaleOrderUseCase(BaseUseCase[CancelScaleOrderRequest, CancelScaleOrderResponse]):
    """
    Use case for cancelling scale orders with unified logic for API and Bot.

    Features:
    - Cancels all open orders in scale order group
    - Reports cancellation success/failure
    - Handles partial cancellation scenarios

    Example:
        >>> request = CancelScaleOrderRequest(scale_order_id="scale_123")
        >>> use_case = CancelScaleOrderUseCase()
        >>> response = await use_case.execute(request)
        >>> print(f"Cancelled {response.result.orders_cancelled} orders")
    """

    def __init__(self):
        """Initialize use case with scale order service."""
        self.scale_order_service = scale_order_service

    async def execute(self, request: CancelScaleOrderRequest) -> CancelScaleOrderResponse:
        """
        Execute cancel scale order use case.

        Args:
            request: Cancel request with scale order ID

        Returns:
            Cancel response with results

        Raises:
            ValueError: If scale order not found
            RuntimeError: If cancellation fails
        """
        try:
            logger.info(f"Cancelling scale order: {request.scale_order_id}")

            # Cancel via service
            result = await self.scale_order_service.cancel_scale_order(request.scale_order_id)

            if result.success:
                logger.info(
                    f"Successfully cancelled scale order {request.scale_order_id}: "
                    f"{result.orders_cancelled} orders cancelled"
                )
            else:
                logger.warning(
                    f"Scale order {request.scale_order_id} cancellation had errors: "
                    f"{result.message}"
                )

            return CancelScaleOrderResponse(result=result)

        except ValueError as e:
            logger.warning(f"Scale order not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to cancel scale order: {e}")
            raise RuntimeError(f"Failed to cancel scale order: {str(e)}")
