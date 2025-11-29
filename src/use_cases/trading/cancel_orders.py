"""
Cancel Orders Use Case.

Unified logic for canceling orders (single or bulk) across all interfaces.
"""

from pydantic import BaseModel, Field

from src.config import logger
from src.services.order_service import order_service
from src.use_cases.base import BaseUseCase


class CancelOrderRequest(BaseModel):
    """Request model for canceling a single order."""

    coin: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")
    order_id: int = Field(..., description="Order ID to cancel")

    class Config:
        json_schema_extra = {
            "example": {
                "coin": "BTC",
                "order_id": 12345,
            }
        }


class CancelOrderResponse(BaseModel):
    """Response model for single order cancellation."""

    status: str = Field(..., description="Operation status (success/failed)")
    coin: str = Field(..., description="Asset symbol")
    order_id: int = Field(..., description="Canceled order ID")
    message: str = Field(..., description="Success/error message")


class CancelBulkOrdersRequest(BaseModel):
    """Request model for canceling multiple orders."""

    order_ids: list[tuple[str, int]] = Field(
        default_factory=list,
        description="List of (coin, order_id) tuples to cancel",
    )
    cancel_all: bool = Field(
        False, description="If True, cancel ALL open orders (ignores order_ids)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "order_ids": [("BTC", 12345), ("ETH", 67890)],
                "cancel_all": False,
            }
        }


class BulkCancelResult(BaseModel):
    """Result for a single order in bulk cancellation."""

    coin: str
    order_id: int
    status: str  # "success" or "failed"
    message: str


class CancelBulkOrdersResponse(BaseModel):
    """Response model for bulk order cancellation."""

    status: str = Field(..., description="Overall operation status (success/partial/failed)")
    total_requested: int = Field(..., description="Total orders requested to cancel")
    successful: int = Field(..., description="Number of successfully canceled orders")
    failed: int = Field(..., description="Number of failed cancellations")
    results: list[BulkCancelResult] = Field(..., description="Detailed results for each order")
    message: str = Field(..., description="Overall summary message")


class CancelOrderUseCase(BaseUseCase[CancelOrderRequest, CancelOrderResponse]):
    """
    Use case for canceling a single order.

    Features:
    - Cancel specific order by coin and order ID
    - Consistent error handling
    - Normalized response format

    Example:
        >>> request = CancelOrderRequest(coin="BTC", order_id=12345)
        >>> use_case = CancelOrderUseCase()
        >>> response = await use_case.execute(request)
    """

    def __init__(self):
        """Initialize use case with required services."""
        self.order_service = order_service

    async def execute(self, request: CancelOrderRequest) -> CancelOrderResponse:
        """
        Execute cancel order use case.

        Args:
            request: Cancel order request

        Returns:
            CancelOrderResponse with result

        Raises:
            RuntimeError: If wallet not configured
            Exception: If cancellation fails
        """
        try:
            logger.info(f"Canceling order: {request.coin} #{request.order_id}")

            self.order_service.cancel_order(
                coin=request.coin,
                order_id=request.order_id,
            )

            logger.info(f"Successfully canceled order: {request.coin} #{request.order_id}")

            return CancelOrderResponse(
                status="success",
                coin=request.coin,
                order_id=request.order_id,
                message=f"Order {request.coin} #{request.order_id} canceled successfully",
            )

        except Exception as e:
            logger.error(f"Failed to cancel order {request.coin} #{request.order_id}: {e}")
            return CancelOrderResponse(
                status="failed",
                coin=request.coin,
                order_id=request.order_id,
                message=f"Failed to cancel order: {str(e)}",
            )


class CancelBulkOrdersUseCase(BaseUseCase[CancelBulkOrdersRequest, CancelBulkOrdersResponse]):
    """
    Use case for canceling multiple orders (bulk operation).

    Features:
    - Cancel multiple specific orders
    - Cancel ALL open orders with single flag
    - Partial success handling (some succeed, some fail)
    - Detailed results for each order

    Example (cancel specific orders):
        >>> request = CancelBulkOrdersRequest(
        ...     order_ids=[("BTC", 12345), ("ETH", 67890)]
        ... )
        >>> use_case = CancelBulkOrdersUseCase()
        >>> response = await use_case.execute(request)

    Example (cancel all):
        >>> request = CancelBulkOrdersRequest(
        ...     order_ids=[],  # Ignored when cancel_all=True
        ...     cancel_all=True
        ... )
        >>> response = await use_case.execute(request)
    """

    def __init__(self):
        """Initialize use case with required services."""
        self.order_service = order_service

    async def execute(self, request: CancelBulkOrdersRequest) -> CancelBulkOrdersResponse:
        """
        Execute bulk cancel orders use case.

        Args:
            request: Bulk cancel request

        Returns:
            CancelBulkOrdersResponse with detailed results

        Raises:
            ValueError: If no orders to cancel
        """
        try:
            # Handle "cancel all" mode
            if request.cancel_all:
                return await self._cancel_all_orders()

            # Handle specific orders mode
            if not request.order_ids:
                logger.warning("No orders specified for bulk cancel")
                return CancelBulkOrdersResponse(
                    status="failed",
                    total_requested=0,
                    successful=0,
                    failed=0,
                    results=[],
                    message="No orders specified to cancel",
                )

            return await self._cancel_specific_orders(request.order_ids)

        except Exception as e:
            logger.error(f"Unexpected error in bulk cancel: {e}")
            return CancelBulkOrdersResponse(
                status="failed",
                total_requested=len(request.order_ids) if not request.cancel_all else 0,
                successful=0,
                failed=len(request.order_ids) if not request.cancel_all else 0,
                results=[],
                message=f"Unexpected error: {str(e)}",
            )

    async def _cancel_all_orders(self) -> CancelBulkOrdersResponse:
        """
        Cancel all open orders.

        Returns:
            Response with cancellation results
        """
        try:
            logger.info("Canceling ALL open orders")

            result = self.order_service.cancel_all_orders()
            canceled_count = result.get("canceled_count", 0)

            logger.info(f"Canceled all orders: {canceled_count} orders")

            return CancelBulkOrdersResponse(
                status="success",
                total_requested=canceled_count,
                successful=canceled_count,
                failed=0,
                results=[],  # Could parse individual results if needed
                message=f"Successfully canceled all {canceled_count} orders",
            )

        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            return CancelBulkOrdersResponse(
                status="failed",
                total_requested=0,
                successful=0,
                failed=0,
                results=[],
                message=f"Failed to cancel all orders: {str(e)}",
            )

    async def _cancel_specific_orders(
        self, order_ids: list[tuple[str, int]]
    ) -> CancelBulkOrdersResponse:
        """
        Cancel specific orders by coin and order ID.

        Args:
            order_ids: List of (coin, order_id) tuples

        Returns:
            Response with detailed results for each order
        """
        logger.info(f"Canceling {len(order_ids)} specific orders")

        results = []
        successful = 0
        failed = 0

        for coin, order_id in order_ids:
            try:
                self.order_service.cancel_order(coin=coin, order_id=order_id)
                results.append(
                    BulkCancelResult(
                        coin=coin,
                        order_id=order_id,
                        status="success",
                        message="Canceled successfully",
                    )
                )
                successful += 1
                logger.debug(f"Canceled order: {coin} #{order_id}")

            except Exception as e:
                results.append(
                    BulkCancelResult(
                        coin=coin,
                        order_id=order_id,
                        status="failed",
                        message=str(e),
                    )
                )
                failed += 1
                logger.warning(f"Failed to cancel {coin} #{order_id}: {e}")

        # Determine overall status
        if failed == 0:
            status = "success"
            message = f"All {successful} orders canceled successfully"
        elif successful == 0:
            status = "failed"
            message = f"All {failed} orders failed to cancel"
        else:
            status = "partial"
            message = f"{successful} succeeded, {failed} failed"

        logger.info(f"Bulk cancel complete: {message}")

        return CancelBulkOrdersResponse(
            status=status,
            total_requested=len(order_ids),
            successful=successful,
            failed=failed,
            results=results,
            message=message,
        )
