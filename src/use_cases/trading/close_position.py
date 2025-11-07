"""
Close Position Use Case.

Unified position closing logic for both API and Bot interfaces.
Supports both partial and full position closes with validation.
"""

from pydantic import BaseModel, Field, field_validator

from src.config import logger
from src.services.market_data_service import market_data_service
from src.services.position_service import position_service
from src.use_cases.base import BaseUseCase
from src.use_cases.common.usd_converter import USDConverter
from src.use_cases.common.validators import OrderValidator, ValidationError


class ClosePositionRequest(BaseModel):
    """Request model for closing a position."""

    coin: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")

    # Size options (None = close full position)
    size: float | None = Field(None, gt=0, description="Specific size to close in coins")
    percentage: float | None = Field(
        None, gt=0, le=100, description="Percentage of position to close (1-100)"
    )

    slippage: float = Field(0.05, ge=0, le=1, description="Slippage tolerance (default 5%)")

    @field_validator("coin")
    @classmethod
    def validate_coin_upper(cls, v: str) -> str:
        """Ensure coin symbol is uppercase."""
        return v.upper()

    class Config:
        json_schema_extra = {"example": {"coin": "BTC", "percentage": 50.0, "slippage": 0.05}}


class ClosePositionResponse(BaseModel):
    """Response model for position closing."""

    status: str = Field(..., description="Operation status (success/failed)")
    coin: str = Field(..., description="Asset symbol")
    size_closed: float = Field(..., description="Size closed in coins")
    usd_value: float = Field(..., description="USD value of closed position")
    remaining_size: float = Field(..., description="Remaining position size (0 if fully closed)")
    close_type: str = Field(..., description="Close type (full/partial)")
    message: str = Field(..., description="Success/error message")


class ClosePositionUseCase(BaseUseCase[ClosePositionRequest, ClosePositionResponse]):
    """
    Use case for closing positions with unified logic for API and Bot.

    Features:
    - Full or partial position closes
    - Percentage-based or absolute size closes
    - Validation of position existence and close parameters
    - Consistent error handling
    - Response includes both coin size and USD value

    Example:
        >>> # Close 50% of position
        >>> request = ClosePositionRequest(
        ...     coin="BTC",
        ...     percentage=50.0
        ... )
        >>> use_case = ClosePositionUseCase()
        >>> response = await use_case.execute(request)

        >>> # Close full position
        >>> request = ClosePositionRequest(coin="BTC")
        >>> response = await use_case.execute(request)
    """

    def __init__(self):
        """Initialize use case with required services."""
        self.position_service = position_service
        self.market_data = market_data_service
        self.usd_converter = USDConverter()

    async def execute(self, request: ClosePositionRequest) -> ClosePositionResponse:
        """
        Execute position closing use case.

        Args:
            request: Position close request

        Returns:
            Position close response

        Raises:
            ValidationError: If request validation fails
            ValueError: If position doesn't exist
            RuntimeError: If position close fails
        """
        try:
            # Validate coin symbol
            OrderValidator.validate_coin_symbol(request.coin)

            # Get current position
            position = self.position_service.get_position(request.coin)
            if not position:
                raise ValueError(f"No open position found for {request.coin}")

            position_details = position["position"]
            current_size = abs(float(position_details["size"]))
            position_value = float(position_details["position_value"])

            # Determine close size
            close_size, close_type = await self._determine_close_size(request, current_size)

            # Validate close size
            if close_size > current_size:
                raise ValidationError(
                    f"Close size {close_size} exceeds position size {current_size}"
                )

            OrderValidator.validate_size(close_size, request.coin)

            # Log close intent
            logger.info(
                f"Closing {close_type} position: {request.coin} "
                f"size={close_size}/{current_size} "
                f"(${close_size * position_value / current_size:.2f})"
            )

            # Close the position
            await self._close_position(request, close_size)

            # Calculate values
            current_price = self.market_data.get_price(request.coin)
            if current_price is None or current_price <= 0:
                # Fallback to position value calculation
                current_price = position_value / current_size

            usd_value = close_size * current_price
            remaining_size = current_size - close_size

            # Build response
            return ClosePositionResponse(
                status="success",
                coin=request.coin,
                size_closed=close_size,
                usd_value=usd_value,
                remaining_size=remaining_size,
                close_type=close_type,
                message=f"{close_type.capitalize()} position closed successfully",
            )

        except ValidationError as e:
            logger.warning(f"Position close validation failed: {e}")
            raise
        except ValueError as e:
            logger.warning(f"Position not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Position close failed: {e}")
            raise RuntimeError(f"Failed to close position: {str(e)}") from e

    async def _determine_close_size(
        self, request: ClosePositionRequest, current_size: float
    ) -> tuple[float, str]:
        """
        Determine close size from request parameters.

        Returns:
            Tuple of (close_size, close_type)
        """
        # Validate that only one close method is specified
        specified_params = sum([request.size is not None, request.percentage is not None])

        if specified_params > 1:
            raise ValidationError("Specify only one of: size, percentage (or none for full close)")

        # Full close (no parameters specified)
        if specified_params == 0:
            return current_size, "full"

        # Percentage-based close
        if request.percentage is not None:
            if request.percentage <= 0 or request.percentage > 100:
                raise ValidationError("Percentage must be between 0 and 100")

            close_size = current_size * (request.percentage / 100)
            close_type = "full" if request.percentage == 100 else "partial"

            logger.debug(
                f"Calculated close size from {request.percentage}%: {close_size} of {current_size}"
            )
            return close_size, close_type

        # Absolute size close
        if request.size is not None:
            close_type = "full" if request.size >= current_size else "partial"
            return request.size, close_type

        # Should never reach here
        raise ValidationError("Invalid close parameters")

    async def _close_position(self, request: ClosePositionRequest, close_size: float) -> dict:
        """Close the position via position service."""
        result = self.position_service.close_position(
            coin=request.coin, size=close_size, slippage=request.slippage
        )

        return result
