"""
Trading use cases package.

This package contains use cases for trading operations like placing orders,
closing positions, and managing trades. These use cases encapsulate business
logic that is shared between API and Bot interfaces.
"""

from src.use_cases.trading.cancel_orders import (
    CancelBulkOrdersRequest,
    CancelBulkOrdersResponse,
    CancelBulkOrdersUseCase,
    CancelOrderRequest,
    CancelOrderResponse,
    CancelOrderUseCase,
)
from src.use_cases.trading.close_position import (
    ClosePositionRequest,
    ClosePositionResponse,
    ClosePositionUseCase,
)
from src.use_cases.trading.list_orders import (
    ListOrdersRequest,
    ListOrdersResponse,
    ListOrdersUseCase,
    OrderInfo,
)
from src.use_cases.trading.place_order import (
    PlaceOrderRequest,
    PlaceOrderResponse,
    PlaceOrderUseCase,
)

__all__ = [
    "PlaceOrderUseCase",
    "PlaceOrderRequest",
    "PlaceOrderResponse",
    "ClosePositionUseCase",
    "ClosePositionRequest",
    "ClosePositionResponse",
    "ListOrdersUseCase",
    "ListOrdersRequest",
    "ListOrdersResponse",
    "OrderInfo",
    "CancelOrderUseCase",
    "CancelOrderRequest",
    "CancelOrderResponse",
    "CancelBulkOrdersUseCase",
    "CancelBulkOrdersRequest",
    "CancelBulkOrdersResponse",
]
