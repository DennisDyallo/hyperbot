# Hyperliquid API Reference

## Overview

The Hyperliquid API provides programmatic access to trading, account management, and market data on the Hyperliquid decentralized exchange.

**Base URLs:**
- Mainnet: `https://api.hyperliquid.xyz`
- Testnet: `https://api.hyperliquid-testnet.xyz`

## Authentication

Hyperliquid uses Ethereum-style wallet signatures for authentication.

### Components
- **Wallet Address**: Your Ethereum wallet public address
- **Private Key**: Used to sign requests (never sent to the server)
- **API Wallet** (optional): A separate wallet for API access with limited permissions

### Best Practices
- Use an API wallet for enhanced security
- Never commit private keys to version control
- Store credentials in environment variables
- Use testnet for development and testing

## Core API Classes

### 1. Info API (Read-Only)

The Info class provides read-only access to market data and account information.

```python
from hyperliquid.info import Info
from hyperliquid.utils import constants

# Initialize
info = Info(constants.MAINNET_API_URL, skip_ws=True)

# Get user state
user_state = info.user_state(user_address)
```

#### Key Methods

**`user_state(user_address: str) -> dict`**

Returns complete account state including:
- `assetPositions`: List of open positions
- `marginSummary`: Account value, margin used, available balance
- `crossMarginSummary`: Cross-margin information
- `withdrawable`: Amount available for withdrawal

**Response Structure:**
```json
{
  "assetPositions": [
    {
      "position": {
        "coin": "BTC",
        "szi": "0.5",
        "leverage": {
          "type": "cross",
          "value": 3
        },
        "entryPx": "50000.0",
        "positionValue": "25000.0",
        "unrealizedPnl": "1250.5",
        "returnOnEquity": "0.05"
      }
    }
  ],
  "marginSummary": {
    "accountValue": "100000.0",
    "totalMarginUsed": "25000.0",
    "totalNtlPos": "25000.0",
    "totalRawUsd": "75000.0"
  }
}
```

**`open_orders(user_address: str) -> list`**

Returns all open orders for the user.

**`user_fills(user_address: str) -> list`**

Returns recent trade fills.

**`meta() -> dict`**

Returns exchange metadata including:
- Available trading pairs
- Tick sizes
- Minimum order sizes
- Leverage limits

**`all_mids() -> dict`**

Returns current mid prices for all trading pairs.

**`l2_snapshot(coin: str) -> dict`**

Returns Level 2 order book snapshot for a specific coin.

### 2. Exchange API (Trading)

The Exchange class handles order placement, cancellation, and account modifications.

```python
from hyperliquid.exchange import Exchange

# Initialize
exchange = Exchange(
    wallet_address=your_address,
    base_url=constants.MAINNET_API_URL,
    account_address=your_address  # Or API wallet address
)
```

#### Order Types

**Market Order**
```python
result = exchange.market_open(
    coin="BTC",
    is_buy=True,
    sz=0.1,
    slippage=0.05  # 5% slippage tolerance
)
```

**Limit Order**
```python
result = exchange.order(
    coin="BTC",
    is_buy=True,
    sz=0.1,
    limit_px=50000.0,
    order_type={"limit": {"tif": "Gtc"}}  # Good til cancel
)
```

**Time In Force Options:**
- `Gtc` - Good til cancel
- `Ioc` - Immediate or cancel
- `Alo` - Add liquidity only (maker-only)

**Stop Loss / Take Profit**
```python
result = exchange.order(
    coin="BTC",
    is_buy=False,
    sz=0.1,
    limit_px=45000.0,
    order_type={
        "trigger": {
            "triggerPx": 45000.0,
            "isMarket": True,
            "tpsl": "sl"  # Stop loss
        }
    }
)
```

#### Order Management

**Cancel Order**
```python
result = exchange.cancel(
    coin="BTC",
    oid=12345  # Order ID
)
```

**Cancel All Orders**
```python
result = exchange.cancel_all()
```

**Modify Order**
```python
result = exchange.modify_order(
    oid=12345,
    coin="BTC",
    is_buy=True,
    sz=0.2,  # New size
    limit_px=51000.0  # New price
)
```

#### Position Management

**Close Position**
```python
# Market close
result = exchange.market_close(
    coin="BTC",
    sz=None  # None = close entire position
)
```

**Update Leverage**
```python
result = exchange.update_leverage(
    leverage=5,
    coin="BTC",
    is_cross=True
)
```

**Update Isolated Margin**
```python
result = exchange.update_isolated_margin(
    amount=1000.0,  # USD amount to add/remove
    coin="BTC"
)
```

## WebSocket API

For real-time updates, use the WebSocket connection:

```python
from hyperliquid.info import Info

# Initialize with WebSocket
info = Info(constants.MAINNET_API_URL, skip_ws=False)

# Subscribe to user events
info.subscribe(
    subscription={"type": "userEvents", "user": user_address},
    callback=handle_user_event
)

# Subscribe to order book updates
info.subscribe(
    subscription={"type": "l2Book", "coin": "BTC"},
    callback=handle_orderbook_update
)
```

## Rate Limits

**Info API (Read):**
- 1200 requests per minute per IP
- No authentication required

**Exchange API (Write):**
- 60 requests per minute per account
- Requires authentication

**WebSocket:**
- 60 subscriptions per connection
- Reconnect on disconnect

## Error Handling

Common error responses:

```python
{
    "status": "error",
    "response": {
        "type": "insufficient_margin",
        "message": "Not enough available balance"
    }
}
```

**Error Types:**
- `insufficient_margin` - Not enough balance
- `invalid_price` - Price outside valid range
- `invalid_size` - Size below minimum or above maximum
- `rate_limit_exceeded` - Too many requests
- `order_not_found` - Order doesn't exist
- `position_not_found` - No position to close

## Best Practices

### 1. Error Handling
```python
try:
    result = exchange.market_open(coin="BTC", is_buy=True, sz=0.1)
    if result["status"] == "error":
        logger.error(f"Order failed: {result['response']}")
    else:
        logger.info(f"Order placed: {result}")
except Exception as e:
    logger.exception(f"API call failed: {e}")
```

### 2. Rate Limiting
```python
import time
from functools import wraps

def rate_limit(min_interval=1.0):
    """Decorator to enforce minimum time between calls."""
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator
```

### 3. Position Monitoring
```python
async def monitor_position(coin: str):
    """Monitor position and send alerts."""
    while True:
        user_state = info.user_state(address)
        positions = user_state.get("assetPositions", [])

        for pos in positions:
            if pos["position"]["coin"] == coin:
                pnl = float(pos["position"]["unrealizedPnl"])
                if abs(pnl) > alert_threshold:
                    send_alert(f"Large PnL change: ${pnl:.2f}")

        await asyncio.sleep(60)
```

### 4. Slippage Protection
```python
def calculate_max_price(side: str, mid_price: float, slippage: float):
    """Calculate maximum acceptable price with slippage."""
    if side == "buy":
        return mid_price * (1 + slippage)
    else:
        return mid_price * (1 - slippage)
```

### 5. Order Size Validation
```python
def validate_order_size(coin: str, size: float) -> bool:
    """Validate order size against exchange limits."""
    meta = info.meta()
    for asset in meta["universe"]:
        if asset["name"] == coin:
            min_size = float(asset["szDecimals"])
            return size >= min_size
    return False
```

## Testing

Always test on testnet first:

```python
# Testnet configuration
from hyperliquid.utils import constants

info = Info(constants.TESTNET_API_URL, skip_ws=True)
exchange = Exchange(
    wallet_address=testnet_address,
    base_url=constants.TESTNET_API_URL,
    account_address=testnet_address
)
```

## Resources

- **Official SDK**: https://github.com/hyperliquid-dex/hyperliquid-python-sdk
- **API Documentation**: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
- **Discord Support**: https://discord.gg/hyperliquid
- **Status Page**: https://status.hyperliquid.xyz

## Common Patterns

### Pattern 1: Safe Market Order
```python
async def safe_market_order(coin: str, is_buy: bool, size: float, max_slippage: float = 0.02):
    """Place market order with slippage check."""
    # Get current price
    mids = info.all_mids()
    current_price = float(mids[coin])

    # Place order
    result = exchange.market_open(
        coin=coin,
        is_buy=is_buy,
        sz=size,
        slippage=max_slippage
    )

    # Verify fill price
    if result["status"] == "ok":
        fills = result["response"]["data"]["statuses"][0].get("filled", {})
        avg_price = float(fills.get("avgPx", 0))

        # Check slippage
        actual_slippage = abs(avg_price - current_price) / current_price
        if actual_slippage > max_slippage:
            logger.warning(f"High slippage: {actual_slippage:.2%}")

    return result
```

### Pattern 2: TWAP Order Execution
```python
async def twap_order(coin: str, is_buy: bool, total_size: float, num_orders: int, interval_seconds: int):
    """Execute TWAP (Time-Weighted Average Price) order."""
    order_size = total_size / num_orders

    for i in range(num_orders):
        result = await safe_market_order(coin, is_buy, order_size)
        logger.info(f"TWAP {i+1}/{num_orders}: {result}")

        if i < num_orders - 1:
            await asyncio.sleep(interval_seconds)
```

### Pattern 3: Portfolio Rebalancing
```python
async def rebalance_portfolio(target_weights: dict):
    """Rebalance portfolio to target weights."""
    # Get current portfolio
    user_state = info.user_state(address)
    total_value = float(user_state["marginSummary"]["accountValue"])

    # Calculate required trades
    trades = []
    for coin, target_weight in target_weights.items():
        target_value = total_value * target_weight
        current_value = get_position_value(user_state, coin)
        diff = target_value - current_value

        if abs(diff) > 10:  # Minimum $10 trade
            trades.append({
                "coin": coin,
                "is_buy": diff > 0,
                "usd_value": abs(diff)
            })

    # Execute trades
    for trade in trades:
        mid_price = float(info.all_mids()[trade["coin"]])
        size = trade["usd_value"] / mid_price

        await safe_market_order(
            coin=trade["coin"],
            is_buy=trade["is_buy"],
            size=size
        )
```

---

**Note:** Always refer to the official documentation for the most up-to-date information and additional features.
