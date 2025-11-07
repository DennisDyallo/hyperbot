"""
Place Order Use Case.

Unified order placement logic for both API and Bot interfaces.
Supports both USD-based and coin-based order sizes with automatic conversion.
"""

from typing import Any

from pydantic import BaseModel, Field

from src.config import logger
from src.services.market_data_service import market_data_service
from src.services.order_service import order_service
from src.use_cases.base import BaseUseCase
from src.use_cases.common.usd_converter import USDConverter
from src.use_cases.common.validators import OrderValidator, ValidationError


class PlaceOrderRequest(BaseModel):
    """Request model for placing an order."""

    coin: str = Field(..., description="Asset symbol (e.g., BTC, ETH)")
    is_buy: bool = Field(..., description="True for buy, False for sell")

    # Size can be specified in either USD or coin amount
    usd_amount: float | None = Field(None, gt=0, description="Order size in USD")
    coin_size: float | None = Field(None, gt=0, description="Order size in coins")

    # Order parameters
    is_market: bool = Field(True, description="True for market order, False for limit")
    limit_price: float | None = Field(
        None, gt=0, description="Limit price (required for limit orders)"
    )
    slippage: float = Field(0.05, ge=0, le=1, description="Slippage tolerance (default 5%)")
    reduce_only: bool = Field(False, description="Reduce-only flag")
    time_in_force: str = Field("Gtc", description="Time in force (Gtc, Ioc, Alo)")

    class Config:
        json_schema_extra = {
            "example": {
                "coin": "BTC",
                "is_buy": True,
                "usd_amount": 1000.0,
                "is_market": True,
                "slippage": 0.05,
            }
        }


class PlaceOrderResponse(BaseModel):
    """Response model for order placement."""

    status: str = Field(..., description="Order status (success/failed)")
    coin: str = Field(..., description="Asset symbol")
    side: str = Field(..., description="Order side (buy/sell)")
    size: float = Field(..., description="Order size in coins")
    usd_value: float = Field(..., description="Order value in USD")
    price: float | None = Field(None, description="Execution price (market) or limit price")
    order_type: str = Field(..., description="Order type (market/limit)")
    order_id: int | None = Field(None, description="Order ID (for limit orders)")
    message: str = Field(..., description="Success/error message")


class PlaceOrderUseCase(BaseUseCase[PlaceOrderRequest, PlaceOrderResponse]):
    """
    Use case for placing orders with unified logic for API and Bot.

    Features:
    - Accepts either USD amount or coin size
    - Automatic USD to coin conversion
    - Validation of order parameters
    - Consistent error handling
    - Response includes both coin size and USD value

    Example:
        >>> request = PlaceOrderRequest(
        ...     coin="BTC",
        ...     is_buy=True,
        ...     usd_amount=1000.0,
        ...     is_market=True
        ... )
        >>> use_case = PlaceOrderUseCase()
        >>> response = await use_case.execute(request)
    """

    def __init__(self):
        """Initialize use case with required services."""
        self.order_service = order_service
        self.market_data = market_data_service
        self.usd_converter = USDConverter()

    async def execute(self, request: PlaceOrderRequest) -> PlaceOrderResponse:
        """
        Execute order placement use case.

        Args:
            request: Order placement request

        Returns:
            Order placement response

        Raises:
            ValidationError: If request validation fails
            RuntimeError: If order placement fails
        """
        try:
            # Validate coin symbol
            OrderValidator.validate_coin_symbol(request.coin)

            # Determine order size (convert from USD if needed)
            coin_size, current_price = await self._determine_order_size(request)

            # Validate order size
            OrderValidator.validate_size(coin_size, request.coin)

            # Validate limit price if limit order
            if not request.is_market:
                if request.limit_price is None:
                    raise ValidationError("Limit price required for limit orders")

                # Get tick size for price validation
                metadata = market_data_service.get_asset_metadata(request.coin)
                tick_size = 10 ** (-metadata["szDecimals"]) if metadata else None
                OrderValidator.validate_price(request.limit_price, request.coin, tick_size)

            # Validate slippage
            OrderValidator.validate_slippage(request.slippage * 100)  # Convert to percentage

            # Log order intent
            side = "BUY" if request.is_buy else "SELL"
            order_type = "MARKET" if request.is_market else "LIMIT"
            logger.info(
                f"Placing {order_type} {side} order: {request.coin} "
                f"size={coin_size} (${coin_size * current_price:.2f})"
            )

            # Place the order
            if request.is_market:
                result = await self._place_market_order(request, coin_size)
            else:
                result = await self._place_limit_order(request, coin_size)

            # Calculate USD value
            execution_price = result.get("price", current_price)
            usd_value = coin_size * execution_price

            # Build response
            return PlaceOrderResponse(
                status="success",
                coin=request.coin,
                side=side,
                size=coin_size,
                usd_value=usd_value,
                price=execution_price,
                order_type=order_type,
                order_id=result.get("order_id"),
                message=f"{order_type} {side} order placed successfully",
            )

        except ValidationError as e:
            logger.warning(f"Order validation failed: {e}")
            raise RuntimeError(f"Order validation failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            raise RuntimeError(f"Failed to place order: {str(e)}") from e

    async def _determine_order_size(self, request: PlaceOrderRequest) -> tuple[float, float]:
        """
        Determine order size from USD amount or coin size.

        Returns:
            Tuple of (coin_size, current_price)
        """
        # Validate that exactly one of usd_amount or coin_size is provided
        if request.usd_amount and request.coin_size:
            raise ValidationError("Specify either usd_amount or coin_size, not both")

        if not request.usd_amount and not request.coin_size:
            raise ValidationError("Must specify either usd_amount or coin_size")

        # Convert from USD if needed
        if request.usd_amount:
            coin_size, current_price = self.usd_converter.convert_usd_to_coin(
                request.usd_amount, request.coin
            )
            logger.debug(
                f"Converted ${request.usd_amount} to {coin_size} {request.coin} at ${current_price}"
            )
            return coin_size, current_price
        else:
            # Get current price for USD value calculation
            current_price = self.market_data.get_price(request.coin)
            if current_price is None or current_price <= 0:
                raise ValueError(f"Invalid price for {request.coin}: {current_price}")
            return request.coin_size, current_price

    async def _place_market_order(
        self, request: PlaceOrderRequest, coin_size: float
    ) -> dict[str, Any]:
        """Place a market order."""
        result = self.order_service.place_market_order(
            coin=request.coin,
            is_buy=request.is_buy,
            size=coin_size,
            slippage=request.slippage,
            reduce_only=request.reduce_only,
        )

        # Extract execution price from result if available
        # Market orders are filled immediately
        # Response structure: result['result']['response']['data']['statuses'][0]['filled']['avgPx']
        price = None
        try:
            api_result = result.get("result", {})
            response = api_result.get("response", {})
            data = response.get("data", {})
            statuses = data.get("statuses", [])
            if statuses and isinstance(statuses[0], dict):
                filled = statuses[0].get("filled", {})
                avg_px = filled.get("avgPx")
                if avg_px:
                    price = float(avg_px)
        except (KeyError, IndexError, ValueError, TypeError) as e:
            logger.warning(f"Could not extract avgPx from market order result: {e}")

        return {
            "price": price,
            "order_id": None,  # Market orders don't have resting order IDs
        }

    async def _place_limit_order(
        self, request: PlaceOrderRequest, coin_size: float
    ) -> dict[str, Any]:
        """Place a limit order."""
        result = self.order_service.place_limit_order(
            coin=request.coin,
            is_buy=request.is_buy,
            size=coin_size,
            limit_price=request.limit_price,
            reduce_only=request.reduce_only,
            time_in_force=request.time_in_force,
        )

        # Extract order ID from result
        order_id = result.get("order_id")

        return {"price": request.limit_price, "order_id": order_id}
