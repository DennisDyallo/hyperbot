"""
Place Scale Order Use Case.

Unified logic for placing scale orders (multiple limit orders).
Handles order placement, tracking, and result reporting.
"""
from pydantic import BaseModel
from src.use_cases.base import BaseUseCase
from src.models.scale_order import ScaleOrderConfig, ScaleOrderResult
from src.services.scale_order_service import scale_order_service
from src.config import logger


class PlaceScaleOrderRequest(BaseModel):
    """Request model for placing scale order."""
    config: ScaleOrderConfig

    class Config:
        json_schema_extra = {
            "example": {
                "config": {
                    "coin": "BTC",
                    "is_buy": True,
                    "total_size": 1.0,
                    "num_orders": 5,
                    "start_price": 50000.0,
                    "end_price": 48000.0,
                    "distribution_type": "linear",
                    "time_in_force": "Gtc"
                }
            }
        }


class PlaceScaleOrderResponse(BaseModel):
    """Response model for scale order placement."""
    result: ScaleOrderResult

    class Config:
        json_schema_extra = {
            "example": {
                "result": {
                    "scale_order_id": "scale_123",
                    "coin": "BTC",
                    "is_buy": True,
                    "total_size": 1.0,
                    "num_orders": 5,
                    "orders_placed": [
                        {
                            "price": 50000.0,
                            "size": 0.2,
                            "order_id": "order_1",
                            "success": True
                        }
                    ],
                    "successful_orders": 5,
                    "failed_orders": 0,
                    "success_rate": 100.0,
                    "total_notional": 49000.0,
                    "estimated_avg_price": 49000.0,
                    "created_at": "2025-11-05T20:00:00Z"
                }
            }
        }


class PlaceScaleOrderUseCase(BaseUseCase[PlaceScaleOrderRequest, PlaceScaleOrderResponse]):
    """
    Use case for placing scale orders with unified logic for API and Bot.

    Features:
    - Places multiple limit orders at calculated price levels
    - Tracks scale order group with unique ID
    - Reports placement success/failure for each order
    - Stores scale order for future status queries

    Example:
        >>> config = ScaleOrderConfig(
        ...     coin="BTC",
        ...     is_buy=True,
        ...     total_size=1.0,
        ...     num_orders=5,
        ...     start_price=50000.0,
        ...     end_price=48000.0
        ... )
        >>> request = PlaceScaleOrderRequest(config=config)
        >>> use_case = PlaceScaleOrderUseCase()
        >>> response = await use_case.execute(request)
        >>> print(f"Placed {response.result.successful_orders}/{response.result.num_orders} orders")
        >>> print(f"Scale order ID: {response.result.scale_order_id}")
    """

    def __init__(self):
        """Initialize use case with scale order service."""
        self.scale_order_service = scale_order_service

    async def execute(self, request: PlaceScaleOrderRequest) -> PlaceScaleOrderResponse:
        """
        Execute scale order placement use case.

        Args:
            request: Placement request with scale order configuration

        Returns:
            Placement response with results and tracking ID

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If placement fails
        """
        try:
            config = request.config

            logger.info(
                f"Placing scale order: {config.coin} "
                f"{'BUY' if config.is_buy else 'SELL'} "
                f"{config.total_size} across {config.num_orders} orders "
                f"(${config.start_price:.2f} - ${config.end_price:.2f})"
            )

            # Place scale order via service
            result = await self.scale_order_service.place_scale_order(config)

            logger.info(
                f"Scale order placed: {result.scale_order_id} - "
                f"{result.successful_orders}/{result.num_orders} orders successful "
                f"({result.success_rate:.1f}%)"
            )

            if result.failed_orders > 0:
                logger.warning(
                    f"Scale order {result.scale_order_id} had {result.failed_orders} failed orders"
                )

            return PlaceScaleOrderResponse(result=result)

        except ValueError as e:
            logger.warning(f"Invalid scale order configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to place scale order: {e}")
            raise RuntimeError(f"Failed to place scale order: {str(e)}")
