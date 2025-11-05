"""
Trading use cases package.

This package contains use cases for trading operations like placing orders,
closing positions, and managing trades. These use cases encapsulate business
logic that is shared between API and Bot interfaces.
"""
from src.use_cases.trading.place_order import (
    PlaceOrderUseCase,
    PlaceOrderRequest,
    PlaceOrderResponse,
)
from src.use_cases.trading.close_position import (
    ClosePositionUseCase,
    ClosePositionRequest,
    ClosePositionResponse,
)

__all__ = [
    "PlaceOrderUseCase",
    "PlaceOrderRequest",
    "PlaceOrderResponse",
    "ClosePositionUseCase",
    "ClosePositionRequest",
    "ClosePositionResponse",
]
