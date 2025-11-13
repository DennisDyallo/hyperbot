# Hyperliquid Fills API Research

**Date**: 2025-11-13
**Purpose**: Document actual API structure for order fill notifications

## Summary

Integration tests revealed the exact structure of fill events from Hyperliquid API. This document serves as the source of truth for implementing order fill notifications.

---

## API Method: `user_fills()`

### Method Signature
```python
info.user_fills(user_address: str) -> List[Dict[str, Any]]
```

**Notes**:
- Does NOT support time filtering via parameters
- Returns ALL fills for the user (can be 1000+)
- Must filter manually by timestamp after retrieval
- Ordered newest first

### Fill Event Structure

Based on 1577 actual fills from mainnet:

```python
{
  "coin": str,              # Symbol: "BTC", "ETH", "UNI", etc.
  "px": str,                # Price (decimal string): "7.498"
  "sz": str,                # Size (decimal string): "33.3"
  "side": str,              # "B" (buy) or "S" (sell)
  "time": int,              # Unix timestamp in milliseconds: 1762985424175
  "startPosition": str,     # Position size before fill: "99.9"
  "dir": str,               # Direction: "Open Long", "Close Long", "Open Short", "Close Short"
  "closedPnl": str,         # Realized P&L (decimal string): "0.0", "1.23"
  "hash": str,              # Transaction hash: "0xb0446a4187b84dbf..."
  "oid": int,               # Order ID: 231584579056
  "crossed": bool,          # Whether order crossed spread: true/false
  "fee": str,               # Fee paid (decimal string): "0.035954"
  "tid": int,               # Trade ID: 817974212080988
  "feeToken": str,          # Fee token: "USDC"
  "twapId": None | int,     # TWAP order ID if applicable
  "builderFee": str,        # Builder fee (optional): "0.001"
  "liquidation": bool       # Liquidation fill (optional): true/false
}
```

### All Fields Found (17 total)

| Field | Type | Always Present | Description |
|-------|------|---------------|-------------|
| `coin` | str | ✅ Yes | Trading pair symbol |
| `px` | str | ✅ Yes | Execution price (decimal string) |
| `sz` | str | ✅ Yes | Fill size (decimal string) |
| `side` | str | ✅ Yes | "B" (buy) or "S" (sell) |
| `time` | int | ✅ Yes | Unix timestamp (milliseconds) |
| `startPosition` | str | ✅ Yes | Position size before this fill |
| `dir` | str | ✅ Yes | "Open Long", "Close Long", "Open Short", "Close Short" |
| `closedPnl` | str | ✅ Yes | Realized P&L from this fill |
| `hash` | str | ✅ Yes | Transaction hash |
| `oid` | int | ✅ Yes | Order ID (unique identifier) |
| `crossed` | bool | ✅ Yes | Whether order crossed the spread |
| `fee` | str | ✅ Yes | Fee paid for this fill |
| `tid` | int | ✅ Yes | Trade ID (unique per fill) |
| `feeToken` | str | ✅ Yes | Token used for fee (usually "USDC") |
| `twapId` | None/int | ✅ Yes | TWAP order ID (null if not TWAP) |
| `builderFee` | str | ⚠️ Optional | MEV builder fee (if applicable) |
| `liquidation` | bool | ⚠️ Optional | True if liquidation fill |

### Examples

**Market Order Fill (Immediate)**:
```json
{
  "coin": "UNI",
  "px": "7.498",
  "sz": "33.3",
  "side": "B",
  "time": 1762985424175,
  "startPosition": "99.9",
  "dir": "Open Long",
  "closedPnl": "0.0",
  "hash": "0xb0446a4187b84dbfb1be042f5ce21f020830002722bb6c91540d159446bc27aa",
  "oid": 231584579056,
  "crossed": false,
  "fee": "0.035954",
  "tid": 817974212080988,
  "feeToken": "USDC",
  "twapId": null
}
```

**Limit Order Fill (Crossed Spread)**:
```json
{
  "coin": "ADA",
  "px": "0.41638",
  "sz": "477.0",
  "side": "B",
  "time": 1722127783598,
  "startPosition": "0.0",
  "dir": "Open Long",
  "closedPnl": "0.0",
  "hash": "0xcbd491420c74be4bbfee040e3c5988016200910d45400fcab6fc9f0230618423",
  "oid": 31406260755,
  "crossed": true,
  "fee": "0.069514",
  "tid": 1125863544224934,
  "feeToken": "USDC",
  "twapId": null
}
```

---

## WebSocket API: `userEvents` Subscription

### Subscription Method
```python
info.subscribe(
    subscription={"type": "userEvents", "user": wallet_address},
    callback=event_callback
)
```

**Status**: ⚠️ Requires further testing with live order placement

**Expected Event Types** (from Hyperliquid docs):
- `fill` - Order fill events
- `order` - Order status updates
- `funding` - Funding payments
- `liquidation` - Liquidation events
- `nonUserCancel` - Orders cancelled by system

### WebSocket vs REST API Comparison

| Aspect | WebSocket `userEvents` | REST `user_fills()` |
|--------|----------------------|-------------------|
| **Latency** | <1s real-time | On-demand query |
| **Data** | Same fill structure | Same fill structure |
| **Persistence** | Event-based (miss if offline) | All history available |
| **Use Case** | Real-time notifications | Recovery after downtime |
| **Filtering** | Filtered at source | Client-side filtering |

---

## Implementation Recommendations

### 1. Fill Hash Calculation (Deduplication)

Since fills can arrive via both WebSocket and REST API, we need a consistent hash:

```python
def calculate_fill_hash(fill: dict) -> str:
    """
    Generate unique hash for deduplication.

    Uses immutable fields that uniquely identify a fill.
    """
    components = [
        str(fill.get("oid")),     # Order ID
        str(fill.get("tid")),     # Trade ID
        str(fill.get("time")),    # Timestamp
        fill.get("coin"),         # Coin
        fill.get("px"),           # Price
        fill.get("sz"),           # Size
    ]
    return hashlib.sha256(":".join(components).encode()).hexdigest()[:16]
```

### 2. Timestamp Handling

**Critical**: Hyperliquid uses milliseconds, Python uses seconds

```python
# Convert from Hyperliquid timestamp
fill_time = datetime.fromtimestamp(fill["time"] / 1000, tz=timezone.utc)

# Convert to Hyperliquid timestamp for queries
query_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
```

### 3. Recovery Query Strategy

Since `user_fills()` doesn't support time filtering:

```python
def get_fills_since(timestamp_ms: int) -> List[dict]:
    """Query and filter fills since timestamp."""
    all_fills = info.user_fills(wallet_address)

    # Filter client-side
    return [
        fill for fill in all_fills
        if fill["time"] > timestamp_ms
    ]
```

**Optimization**: Stop iterating once we hit fills older than our timestamp (fills are newest-first).

### 4. Essential Fields for Notifications

**Minimum required fields**:
- `coin` - What was traded
- `side` - Buy or sell
- `sz` - Size filled
- `px` - Execution price
- `time` - When it happened
- `dir` - Open/Close position
- `closedPnl` - P&L if closing
- `fee` - Cost of trade
- `oid` - For tracking
- `tid` - For deduplication

### 5. Side Mapping

```python
SIDE_EMOJI = {
    "B": "📈",  # Buy (green up)
    "S": "📉",  # Sell (red down)
}

SIDE_TEXT = {
    "B": "BUY",
    "S": "SELL",
}
```

### 6. Direction Mapping

```python
DIR_EMOJI = {
    "Open Long": "🟢",
    "Close Long": "🔵",
    "Open Short": "🔴",
    "Close Short": "🟣",
}
```

---

## Testing Observations

### From Integration Tests

1. **Volume**: Account had 1577 fills in history
2. **Performance**: Querying all fills takes ~1-2 seconds
3. **Oldest Fill**: From July 28, 2024 (3+ months of history)
4. **Newest Fill**: From November 12, 2025
5. **24-Hour Activity**: 13 fills in last 24 hours
6. **Time Filtering**: Manual filtering required

### WebSocket Testing

**Status**: Requires live order placement to capture events

**Next Steps**:
1. Place small test order on testnet
2. Capture WebSocket events
3. Compare structure with `user_fills()` data
4. Document any differences

---

## Data Model Requirements

Based on findings, our models need:

### OrderFillEvent
```python
@dataclass
class OrderFillEvent:
    """Represents a single order fill event."""
    coin: str
    side: str  # "B" or "S"
    size: Decimal
    price: Decimal
    timestamp: datetime
    direction: str  # "Open Long", etc.
    closed_pnl: Decimal
    fee: Decimal
    order_id: int
    trade_id: int
    hash: str
    crossed: bool
    fee_token: str = "USDC"
    twap_id: Optional[int] = None
    builder_fee: Optional[Decimal] = None
    liquidation: bool = False
```

### NotificationState
```python
@dataclass
class NotificationState:
    """Persistent state for recovery."""
    last_processed_timestamp: int  # Milliseconds
    recent_fill_hashes: Set[str]   # Last 1000 fills
    last_websocket_heartbeat: Optional[datetime]
    websocket_reconnect_count: int = 0
```

---

## Conclusion

We have complete understanding of the `user_fills()` API structure. The next steps are:

1. ✅ Document findings (this file)
2. ⏭️ Create Pydantic models based on structure
3. ⏭️ Implement OrderMonitorService with recovery logic
4. ⏭️ Test WebSocket events with live orders
5. ⏭️ Implement notification formatting
6. ⏭️ Integrate with Telegram bot

**Key Insight**: Since `user_fills()` returns ALL fills without time filtering, we should:
- Store `last_processed_timestamp` persistently
- On startup, query all fills and filter client-side
- Optimize by stopping once we hit old fills (newest-first ordering)
- Use fill hash for deduplication across WebSocket + REST sources
