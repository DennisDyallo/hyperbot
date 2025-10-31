# Hyperliquid Liquidation Mechanics Research

**Research Date**: 2025-10-31
**Purpose**: Understand liquidation mechanics for Phase 2A Risk Management System

---

## Overview

Hyperliquid uses a **two-stage liquidation process** with partial liquidations to minimize trader losses while maintaining system solvency.

---

## Key Concepts

### 1. Cross Margin vs Isolated Margin

**Cross Margin** (Default):
- All positions share the same margin pool
- Account-wide liquidation price
- One position's profit can offset another's loss
- More capital efficient but higher systemic risk

**Isolated Margin**:
- Each position has dedicated margin
- Position-specific liquidation price
- Losses limited to allocated margin
- Less efficient but contained risk

### 2. Liquidation Price Calculation

Hyperliquid API provides `liquidationPx` field directly for each position:

```json
{
  "position": {
    "coin": "BTC",
    "szi": "0.5",
    "leverage": {
      "type": "cross",
      "value": 5
    },
    "entryPx": "50000.0",
    "positionValue": "25000.0",
    "unrealizedPnl": "1000.0",
    "liquidationPx": "42500.0",
    "marginUsed": "5000.0"
  }
}
```

**For Long Positions**:
- Liquidation occurs when price falls below `liquidationPx`
- Distance to liquidation: `(current_price - liquidation_price) / current_price * 100`

**For Short Positions**:
- Liquidation occurs when price rises above `liquidationPx`
- Distance to liquidation: `(liquidation_price - current_price) / current_price * 100`

### 3. Two-Stage Liquidation Process

**Stage 1: Partial Liquidation**
- Triggered when position reaches maintenance margin threshold
- System closes portion of position to restore health
- Reduces position size by ~25-50%
- Trader maintains control of remaining position

**Stage 2: Full Liquidation**
- Triggered if margin continues to deteriorate
- Entire position closed at market price
- Liquidation fee applied (~0.5-1%)
- Remaining collateral (if any) returned to account

### 4. Mark Price vs Last Price

Hyperliquid uses **mark price** (not last trade price) for liquidation calculations:

- **Mark Price**: Fair value based on index + funding rate
- **Purpose**: Prevents manipulation via flash crashes on single exchange
- **Benefit**: More stable liquidation triggers

---

## API Fields for Risk Calculation

Available in `user_state()` response:

```python
position_data = {
    "coin": str,              # Asset symbol
    "szi": str,               # Signed size (+ long, - short)
    "entryPx": str,           # Average entry price
    "positionValue": str,     # Current position value (USD)
    "unrealizedPnl": str,     # Unrealized profit/loss
    "liquidationPx": str,     # ✅ Liquidation price (provided by API)
    "marginUsed": str,        # Margin allocated to position
    "leverage": {
        "type": str,          # "cross" or "isolated"
        "value": int          # Leverage multiplier (e.g., 5)
    }
}

margin_summary = {
    "accountValue": str,      # Total account value
    "totalMarginUsed": str,   # Sum of all margin used
    "totalNtlPos": str,       # Total notional position value
    "totalRawUsd": str,       # Available balance
}
```

---

## Practical Implications for Hyperbot

### 1. No Manual Calculation Needed
- ✅ API provides `liquidationPx` directly
- ❌ No need to implement liquidation price formulas
- Focus on **distance to liquidation** instead

### 2. Risk Metrics to Track

**Primary Metric**: Liquidation Distance (%)
```python
if position_size > 0:  # Long
    distance_pct = ((current_price - liquidation_price) / current_price) * 100
else:  # Short
    distance_pct = ((liquidation_price - current_price) / current_price) * 100
```

**Secondary Metrics**:
- Margin utilization: `total_margin_used / account_value * 100`
- Position leverage: from API
- Unrealized PnL: from API

### 3. Conservative Thresholds for Crypto

Given crypto's high volatility (BTC can move 10-20% in hours):

| Risk Level | Liquidation Distance | Rationale |
|------------|---------------------|-----------|
| **SAFE** | > 50% | Safe through 2-3 major moves |
| **LOW** | 30-50% | Safe through 1-2 major moves |
| **MODERATE** | 15-30% | Vulnerable to large swing |
| **HIGH** | 8-15% | One bad day could liquidate |
| **CRITICAL** | < 8% | Flash crash risk |

### 4. Leverage Management

**Update Leverage** (before rebalancing):
```python
exchange.update_leverage(
    leverage=5,
    coin="BTC",
    is_cross=True
)
```

**Best Practices**:
- Set leverage BEFORE opening positions
- Use consistent leverage across rebalancing (e.g., 5x for all)
- Lower leverage = higher liquidation distance = safer

---

## References

- **Hyperliquid API Docs**: `docs/hyperliquid/api-reference.md`
- **Hyperliquid Official Docs**: https://hyperliquid.gitbook.io/hyperliquid-docs
- **Python SDK**: https://github.com/hyperliquid-dex/hyperliquid-python-sdk

---

## Key Takeaways

1. ✅ **Use API's `liquidationPx`** - Don't calculate manually
2. ✅ **Liquidation distance is primary risk metric** - Simple and universal
3. ✅ **Conservative thresholds** - Crypto is volatile (50%/30%/15%/8%)
4. ✅ **Cross margin = account-wide risk** - All positions affect each other
5. ✅ **Set leverage before trading** - Use `update_leverage()` in rebalancing
6. ✅ **Mark price prevents manipulation** - More stable than last price
