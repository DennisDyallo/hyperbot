"""
Models for scale order configuration and tracking.

Scale orders place multiple limit orders at different price levels,
allowing traders to build or exit positions gradually.
"""

from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class ScaleOrderConfig(BaseModel):
    """Configuration for creating a scale order."""

    coin: str = Field(..., description="Asset symbol (e.g., 'BTC', 'ETH')")
    is_buy: bool = Field(..., description="True for buy orders, False for sell orders")
    total_usd_amount: float = Field(
        ..., gt=0, description="Total USD amount to deploy across all orders"
    )
    num_orders: int = Field(..., ge=2, le=20, description="Number of orders to place (2-20)")

    # Price range
    start_price: float = Field(..., gt=0, description="Starting price for the ladder")
    end_price: float = Field(..., gt=0, description="Ending price for the ladder")

    # Distribution settings
    distribution_type: Literal["linear", "geometric"] = Field(
        default="linear",
        description="How to distribute sizes: 'linear' (equal) or 'geometric' (weighted)",
    )
    geometric_ratio: float = Field(
        default=1.5,
        gt=1.0,
        le=3.0,
        description="Geometric ratio for size distribution (1.5 = each order 1.5x previous, range: 1.0-3.0)",
    )

    # Order settings
    reduce_only: bool = Field(default=False, description="Only reduce existing position")
    time_in_force: Literal["Gtc", "Ioc", "Alo"] = Field(
        default="Gtc",
        description="Time in force: Gtc (good til cancel), Ioc (immediate or cancel), Alo (add liquidity only)",
    )

    @field_validator("end_price")
    @classmethod
    def validate_price_range(cls, end_price: float, info) -> float:
        """Ensure end_price is different from start_price."""
        start_price = info.data.get("start_price")
        if start_price and end_price == start_price:
            raise ValueError("end_price must be different from start_price")
        return end_price

    @field_validator("end_price")
    @classmethod
    def validate_price_direction(cls, end_price: float, info) -> float:
        """Validate price range makes sense for buy/sell direction."""
        start_price = info.data.get("start_price")
        is_buy = info.data.get("is_buy")

        if start_price and is_buy is not None:
            # For buy orders, typically scale down (higher to lower prices)
            # For sell orders, typically scale up (lower to higher prices)
            # But we'll allow both directions for flexibility
            pass

        return end_price


class ScaleOrderPreview(BaseModel):
    """Preview of a scale order before placement."""

    coin: str
    is_buy: bool
    total_usd_amount: float
    total_coin_size: float = Field(..., description="Total coin quantity across all orders")
    num_orders: int
    orders: list[dict] = Field(..., description="List of individual orders with price and size")
    estimated_avg_price: float = Field(..., description="Estimated average fill price")
    price_range_pct: float = Field(..., description="Price range as percentage")


class OrderPlacement(BaseModel):
    """Result of placing a single order in a scale order."""

    order_id: int | None = Field(None, description="Hyperliquid order ID if successful")
    price: float
    size: float
    status: Literal["success", "failed"] = Field(..., description="Placement status")
    error: str | None = Field(None, description="Error message if failed")


class ScaleOrderResult(BaseModel):
    """Result of placing a scale order."""

    scale_order_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique ID for this scale order group"
    )
    coin: str
    is_buy: bool
    total_usd_amount: float
    total_coin_size: float = Field(..., description="Total coin quantity placed")
    num_orders: int

    placements: list[OrderPlacement] = Field(..., description="Individual order placement results")

    orders_placed: int = Field(..., description="Number of orders successfully placed")
    orders_failed: int = Field(..., description="Number of orders that failed")

    average_price: float | None = Field(None, description="Average price of placed orders")
    total_placed_size: float = Field(..., description="Total size actually placed")

    status: Literal["completed", "partial", "failed"] = Field(
        ...,
        description="Overall status: 'completed' (all placed), 'partial' (some placed), 'failed' (none placed)",
    )

    created_at: datetime = Field(default_factory=datetime.now)


class ScaleOrder(BaseModel):
    """
    Database model for tracking scale order groups.

    This represents a group of related limit orders that were placed
    as part of a scale order strategy.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    coin: str
    is_buy: bool

    # Configuration
    total_usd_amount: float
    total_coin_size: float = Field(..., description="Total coin quantity")
    num_orders: int
    start_price: float
    end_price: float
    distribution_type: str

    # Results
    order_ids: list[int] = Field(default_factory=list, description="List of Hyperliquid order IDs")
    orders_placed: int = Field(default=0)
    orders_filled: int = Field(default=0)
    total_filled_size: float = Field(default=0.0)
    average_fill_price: float | None = None

    # Status tracking
    status: Literal["active", "completed", "cancelled", "failed"] = Field(
        default="active",
        description="Status: 'active' (orders open), 'completed' (all filled), 'cancelled' (cancelled), 'failed' (placement failed)",
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "coin": "BTC",
                "is_buy": True,
                "total_usd_amount": 50000.0,
                "total_coin_size": 1.0,
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
            }
        }


class ScaleOrderCancel(BaseModel):
    """Request to cancel a scale order."""

    scale_order_id: str = Field(..., description="ID of the scale order to cancel")
    cancel_all_orders: bool = Field(
        default=True, description="Whether to cancel all open orders in the group"
    )


class ScaleOrderStatus(BaseModel):
    """Status information for a scale order."""

    scale_order: ScaleOrder
    open_orders: list[dict] = Field(
        default_factory=list, description="List of currently open orders from this scale order"
    )
    filled_orders: list[dict] = Field(
        default_factory=list, description="List of filled orders from this scale order"
    )
    fill_percentage: float = Field(..., description="Percentage of total size filled (0-100)")
