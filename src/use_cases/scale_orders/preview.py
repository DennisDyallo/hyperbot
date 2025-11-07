"""
Preview Scale Order Use Case.

Unified logic for previewing scale orders before placement.
Calculates price levels, sizes, and estimated execution price.
"""

from pydantic import BaseModel

from src.config import logger
from src.models.scale_order import ScaleOrderConfig, ScaleOrderPreview
from src.services.scale_order_service import scale_order_service
from src.use_cases.base import BaseUseCase


class PreviewScaleOrderRequest(BaseModel):
    """Request model for previewing scale order."""

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
                    "time_in_force": "Gtc",
                }
            }
        }


class PreviewScaleOrderResponse(BaseModel):
    """Response model for scale order preview."""

    preview: ScaleOrderPreview

    class Config:
        json_schema_extra = {
            "example": {
                "preview": {
                    "coin": "BTC",
                    "is_buy": True,
                    "total_size": 1.0,
                    "num_orders": 5,
                    "orders": [{"price": 50000.0, "size": 0.2, "notional": 10000.0}],
                    "estimated_avg_price": 49000.0,
                    "price_range_pct": 4.0,
                }
            }
        }


class PreviewScaleOrderUseCase(BaseUseCase[PreviewScaleOrderRequest, PreviewScaleOrderResponse]):
    """
    Use case for previewing scale orders with unified logic for API and Bot.

    Features:
    - Calculates price levels (linear distribution)
    - Calculates sizes (linear or geometric distribution)
    - Estimates average execution price
    - Validates configuration parameters

    Example:
        >>> config = ScaleOrderConfig(
        ...     coin="BTC",
        ...     is_buy=True,
        ...     total_size=1.0,
        ...     num_orders=5,
        ...     start_price=50000.0,
        ...     end_price=48000.0
        ... )
        >>> request = PreviewScaleOrderRequest(config=config)
        >>> use_case = PreviewScaleOrderUseCase()
        >>> response = await use_case.execute(request)
        >>> print(f"Avg price: ${response.preview.estimated_avg_price:.2f}")
    """

    def __init__(self):
        """Initialize use case with scale order service."""
        self.scale_order_service = scale_order_service

    async def execute(self, request: PreviewScaleOrderRequest) -> PreviewScaleOrderResponse:
        """
        Execute scale order preview use case.

        Args:
            request: Preview request with scale order configuration

        Returns:
            Preview response with calculated orders and metrics

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If preview generation fails
        """
        try:
            config = request.config

            logger.info(
                f"Scale order preview: {config.coin} "
                f"{'BUY' if config.is_buy else 'SELL'} "
                f"${config.total_usd_amount:.2f} across {config.num_orders} orders "
                f"(${config.start_price:.2f} - ${config.end_price:.2f})"
            )

            # Generate preview via service
            preview = await self.scale_order_service.preview_scale_order(config)

            logger.info(
                f"Preview generated: {len(preview.orders)} orders, "
                f"avg_price=${preview.estimated_avg_price:.2f}, "
                f"range={preview.price_range_pct:.2f}%"
            )

            return PreviewScaleOrderResponse(preview=preview)

        except ValueError as e:
            logger.warning(f"Invalid scale order configuration: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to generate scale order preview: {e}")
            raise RuntimeError(f"Failed to generate preview: {str(e)}") from e
