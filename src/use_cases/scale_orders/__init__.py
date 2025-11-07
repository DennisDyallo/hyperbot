"""
Scale Order Use Cases.

Business logic for scale order operations including:
- Preview: Calculate price levels and sizes before placement
- Place: Execute multiple limit orders at different prices
- Track: Monitor fill progress and manage active scale orders

These use cases are shared by both API and Bot interfaces.
"""

from src.use_cases.scale_orders.place import (
    PlaceScaleOrderRequest,
    PlaceScaleOrderResponse,
    PlaceScaleOrderUseCase,
)
from src.use_cases.scale_orders.preview import (
    PreviewScaleOrderRequest,
    PreviewScaleOrderResponse,
    PreviewScaleOrderUseCase,
)
from src.use_cases.scale_orders.track import (
    CancelScaleOrderRequest,
    CancelScaleOrderResponse,
    CancelScaleOrderUseCase,
    GetScaleOrderStatusRequest,
    GetScaleOrderStatusResponse,
    GetScaleOrderStatusUseCase,
    ListScaleOrdersRequest,
    ListScaleOrdersResponse,
    ListScaleOrdersUseCase,
)

__all__ = [
    # Preview
    "PreviewScaleOrderUseCase",
    "PreviewScaleOrderRequest",
    "PreviewScaleOrderResponse",
    # Place
    "PlaceScaleOrderUseCase",
    "PlaceScaleOrderRequest",
    "PlaceScaleOrderResponse",
    # Track - List
    "ListScaleOrdersUseCase",
    "ListScaleOrdersRequest",
    "ListScaleOrdersResponse",
    # Track - Status
    "GetScaleOrderStatusUseCase",
    "GetScaleOrderStatusRequest",
    "GetScaleOrderStatusResponse",
    # Track - Cancel
    "CancelScaleOrderUseCase",
    "CancelScaleOrderRequest",
    "CancelScaleOrderResponse",
]
