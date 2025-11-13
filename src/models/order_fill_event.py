"""
Order fill event models for notification system.

Based on actual Hyperliquid API structure documented in:
docs/research/hyperliquid_fills_api.md
"""

from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class OrderFillEvent(BaseModel):
    """
    Represents a single order fill event from Hyperliquid.

    This model matches the exact structure returned by:
    - info.user_fills(user_address)
    - WebSocket userEvents subscription (fill events)

    All decimal values (price, size, fees, P&L) are stored as strings
    in the API and converted to Decimal for precision.
    """

    # Core identification
    order_id: int = Field(..., alias="oid", description="Order ID (unique)")
    trade_id: int = Field(..., alias="tid", description="Trade ID (unique per fill)")
    hash: str = Field(..., description="Transaction hash on L1")

    # Trading details
    coin: str = Field(..., description="Trading pair symbol (e.g., 'BTC', 'ETH')")
    side: str = Field(..., description="'B' for buy, 'S' for sell")
    size: Decimal = Field(..., alias="sz", description="Fill size")
    price: Decimal = Field(..., alias="px", description="Execution price")

    # Position information
    direction: str = Field(
        ...,
        alias="dir",
        description="Position direction: 'Open Long', 'Close Long', 'Open Short', 'Close Short'",
    )
    start_position: Decimal = Field(
        ..., alias="startPosition", description="Position size before this fill"
    )
    closed_pnl: Decimal = Field(..., alias="closedPnl", description="Realized P&L from this fill")

    # Execution details
    timestamp_ms: int = Field(..., alias="time", description="Unix timestamp in milliseconds")
    crossed: bool = Field(..., description="Whether order crossed the spread")
    fee: Decimal = Field(..., description="Fee paid for this fill")
    fee_token: str = Field(..., alias="feeToken", description="Token used for fee (usually USDC)")

    # Optional fields
    twap_id: int | None = Field(
        None, alias="twapId", description="TWAP order ID if this is part of TWAP"
    )
    builder_fee: Decimal | None = Field(
        None, alias="builderFee", description="MEV builder fee if applicable"
    )
    liquidation: bool = Field(False, description="Whether this is a liquidation fill")

    class Config:
        """Pydantic model configuration."""

        populate_by_name = True  # Allow both alias and field name
        json_encoders = {
            Decimal: str,  # Encode Decimal as string (matches API)
        }

    @field_validator(
        "size", "price", "start_position", "closed_pnl", "fee", "builder_fee", mode="before"
    )
    @classmethod
    def parse_decimal_string(cls, v: str | Decimal | None) -> Decimal | None:
        """Convert string to Decimal."""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))

    @property
    def timestamp(self) -> datetime:
        """Convert millisecond timestamp to datetime (UTC)."""
        return datetime.fromtimestamp(self.timestamp_ms / 1000, tz=UTC)

    @property
    def side_text(self) -> str:
        """Human-readable side text."""
        return "BUY" if self.side == "B" else "SELL"

    @property
    def side_emoji(self) -> str:
        """Emoji indicator for side."""
        return "📈" if self.side == "B" else "📉"

    @property
    def direction_emoji(self) -> str:
        """Emoji indicator for direction."""
        emoji_map = {
            "Open Long": "🟢",
            "Close Long": "🔵",
            "Open Short": "🔴",
            "Close Short": "🟣",
        }
        return emoji_map.get(self.direction, "⚪")

    @property
    def total_value(self) -> Decimal:
        """Total value of fill (size * price)."""
        return self.size * self.price

    @property
    def is_opening(self) -> bool:
        """Whether this fill opens a position."""
        return "Open" in self.direction

    @property
    def is_closing(self) -> bool:
        """Whether this fill closes a position."""
        return "Close" in self.direction

    @property
    def is_long(self) -> bool:
        """Whether this is a long position."""
        return "Long" in self.direction

    @property
    def is_short(self) -> bool:
        """Whether this is a short position."""
        return "Short" in self.direction

    def calculate_hash(self) -> str:
        """
        Calculate unique hash for this fill (for deduplication).

        Uses immutable fields that uniquely identify a fill:
        - order_id
        - trade_id
        - timestamp
        - coin
        - price
        - size

        Returns:
            str: 16-character hex hash
        """
        import hashlib

        components = [
            str(self.order_id),
            str(self.trade_id),
            str(self.timestamp_ms),
            self.coin,
            str(self.price),
            str(self.size),
        ]
        hash_input = ":".join(components).encode()
        return hashlib.sha256(hash_input).hexdigest()[:16]

    def to_notification_text(self, include_emoji: bool = True) -> str:
        """
        Format fill as notification text.

        Args:
            include_emoji: Whether to include emoji indicators

        Returns:
            str: Formatted notification text
        """
        # Determine order type
        if self.crossed:
            order_type = "Market Order" if "Open" in self.direction else "Close Order"
        else:
            order_type = "Limit Order"

        # Build notification
        lines = []

        if include_emoji:
            lines.append(f"🎯 **{order_type} Filled!**")
        else:
            lines.append(f"**{order_type} Filled!**")

        lines.append("")
        lines.append(f"**Coin**: {self.coin}")

        if include_emoji:
            lines.append(f"**Side**: {self.side_text} {self.side_emoji}")
            lines.append(f"**Direction**: {self.direction} {self.direction_emoji}")
        else:
            lines.append(f"**Side**: {self.side_text}")
            lines.append(f"**Direction**: {self.direction}")

        lines.append(f"**Size**: {self.size} {self.coin}")
        lines.append(f"**Price**: ${self.price:,.4f}")
        lines.append(f"**Total Value**: ${self.total_value:,.2f}")
        lines.append(f"**Fee**: ${self.fee}")

        if self.is_closing and self.closed_pnl != 0:
            pnl_emoji = "💰" if self.closed_pnl > 0 else "📉"
            lines.append(f"**Closed P&L**: ${self.closed_pnl} {pnl_emoji if include_emoji else ''}")

        lines.append(f"**Time**: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC")

        if self.liquidation:
            lines.append("")
            lines.append("⚠️ **LIQUIDATION FILL**")

        return "\n".join(lines)


class FillNotificationRequest(BaseModel):
    """Request to send a fill notification."""

    fill: OrderFillEvent
    user_ids: list[int] = Field(..., description="Telegram user IDs to notify")
    is_recovery: bool = Field(
        False, description="Whether this is a recovery notification (from bot restart)"
    )


class FillNotificationResponse(BaseModel):
    """Response after sending fill notification."""

    fill_hash: str
    notified_users: int
    success: bool
    error: str | None = None
