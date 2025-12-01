# Phase 7: Leverage-Aware Order Placement & Capital Transparency

**Status**: 📋 Planned
**Priority**: HIGH - Critical UX improvement for safe trading
**Duration**: 3-4 days
**Target Completion**: TBD

---

## Problem Statement

**Current Pain Points**:
1. ❌ Users must manually set leverage **before** placing orders (separate step)
2. ❌ No visibility into **buying power** at different leverage levels
3. ❌ No pre-order preview of **margin required** and **liquidation price**
4. ❌ Risk of placing orders with wrong leverage (forget to set it)
5. ❌ No capital utilization feedback ("Can I afford this order?")

**Real Trading Scenario**:
```
Trader wants to buy $1000 worth of BTC at 5x leverage
Current Flow (BAD):
  1. Set leverage separately: /leverage BTC 5
  2. Place order: /trade -> market -> BTC -> buy -> $1000
  3. Hope leverage was set correctly ❌
  4. No idea about liquidation price until after ❌

Desired Flow (GOOD):
  1. /trade -> market -> BTC -> buy
  2. Select leverage: [1x] [3x] [5x] [10x] ← Interactive selection
  3. See preview BEFORE confirming:
     💰 Order: $1000 BTC @ market
     ⚡ Leverage: 5x
     📊 Margin Required: $200
     💸 Buying Power Available: $4,800 (at 5x)
     🎯 Est. Liquidation: $67,000 (35% drop)
     ⚠️ Risk: MODERATE
  4. Confirm with full transparency ✅
```

---

## Goals

### Primary Goals
1. **Inline Leverage Selection**: Choose leverage during order placement (not separate step)
2. **Capital Transparency**: Show available buying power at each leverage level
3. **Risk Preview**: Display margin, liquidation price, and risk assessment before confirmation
4. **Prevent Errors**: Validate orders against available capital in real-time
5. **Consistent UX**: Same flow for market, limit, and scale orders
6. **Enhanced Position Display**: Show liquidation levels for ALL positions (isolated & cross)
7. **Stop Loss Management**: Display and manage stop loss orders in position view

### Additional Safety Features (NEW)
1. **Liquidation Price Display**: Show liquidation price for every position (not just isolated)
2. **Stop Loss Visibility**: Display active stop loss orders associated with positions
3. **Risk Distance Indicators**: Show % distance to liquidation for quick risk assessment
4. **Stop Loss Recommendations**: Suggest stop loss levels based on position risk

### Success Metrics
- ✅ Zero orders placed with incorrect leverage
- ✅ 100% of orders show capital/risk preview before confirmation
- ✅ <5 seconds to select leverage and see capital impact
- ✅ User confidence: "I know exactly what I'm getting into"
- ✅ Liquidation prices visible for ALL positions (100% coverage)
- ✅ Stop loss orders clearly associated with positions
- ✅ Quick risk assessment via distance-to-liquidation indicators

---

## Architecture Changes

### Backend Changes

#### 1. Enhanced Order Request Models
```python
# src/use_cases/trading/place_order.py
class PlaceOrderRequest(BaseModel):
    coin: str
    is_buy: bool
    usd_amount: float | None = None
    coin_size: float | None = None

    # NEW: Leverage parameters
    leverage: int | None = Field(
        None,
        ge=1,
        le=50,
        description="Leverage to use (auto-set if no position exists)"
    )
    auto_set_leverage: bool = Field(
        True,
        description="Automatically set leverage if needed (default True)"
    )

    is_market: bool = True
    limit_price: float | None = None
    # ... existing fields
```

#### 2. Enhanced Position Response Models (NEW)
```python
# src/use_cases/portfolio/position_summary.py
class PositionDetail(BaseModel):
    """Enhanced position details with liquidation and stop loss info."""
    # Existing fields
    coin: str
    side: str  # "LONG" / "SHORT"
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    leverage: int

    # NEW: Risk metrics
    liquidation_price: float
    liquidation_distance_pct: float  # % from current to liquidation
    margin_used: float
    margin_type: str  # "cross" / "isolated"
    risk_level: str  # "LOW", "MODERATE", "HIGH", "CRITICAL"

    # NEW: Stop loss info
    stop_loss_price: float | None = None
    stop_loss_order_id: int | None = None
    stop_loss_distance_pct: float | None = None  # % from current to SL
    has_stop_loss: bool = False
```

#### 3. New Use Case: Manage Stop Loss
```python
# src/use_cases/trading/manage_stop_loss.py
class SetStopLossRequest(BaseModel):
    """Request to set stop loss for a position."""
    coin: str
    stop_loss_price: float

class SetStopLossResponse(BaseModel):
    """Response after setting stop loss."""
    status: str  # "success" / "failed"
    message: str
    order_id: int | None = None
    stop_loss_price: float | None = None
    potential_loss_usd: float | None = None
    potential_loss_pct: float | None = None

class RemoveStopLossRequest(BaseModel):
    """Request to remove stop loss."""
    coin: str
    order_id: int

class GetStopLossRequest(BaseModel):
    """Request to get stop loss for position."""
    coin: str

class StopLossInfo(BaseModel):
    """Stop loss information for a position."""
    has_stop_loss: bool
    stop_loss_price: float | None = None
    order_id: int | None = None
    distance_pct: float | None = None
    potential_loss: float | None = None
```

#### 2. New Use Case: Calculate Buying Power
```python
# src/use_cases/portfolio/buying_power.py
class CalculateBuyingPowerRequest(BaseModel):
    """Request to calculate buying power at different leverage levels."""
    coin: str
    leverage_levels: list[int] = Field(
        default=[1, 3, 5, 10, 20],
        description="Leverage levels to calculate"
    )

class BuyingPowerInfo(BaseModel):
    """Buying power information for a specific leverage level."""
    leverage: int
    available_margin: float  # USD available for margin
    buying_power: float  # margin * leverage
    current_usage_pct: float  # % of margin already used
    can_trade: bool

class CalculateBuyingPowerResponse(BaseModel):
    """Response with buying power at different leverage levels."""
    coin: str
    account_value: float  # Total account value
    margin_available: float  # Free margin (not used)

    # Buying power at each leverage level
    buying_power_levels: list[BuyingPowerInfo]

    # Current position info (if exists)
    current_leverage: int | None = None
    current_position_value: float | None = None
```

#### 3. Enhanced Order Preview
```python
# src/use_cases/trading/preview_order.py
class PreviewOrderRequest(BaseModel):
    """Request to preview an order before placement."""
    coin: str
    is_buy: bool
    size_usd: float
    leverage: int
    entry_price: float | None = None  # None = market price

class PreviewOrderResponse(BaseModel):
    """Complete order preview with risk assessment."""
    # Order details
    coin: str
    side: str  # "BUY" / "SELL"
    size_usd: float
    size_coin: float
    entry_price: float

    # Leverage & Margin
    leverage: int
    margin_required: float
    margin_available: float
    margin_sufficient: bool

    # Risk metrics
    estimated_liquidation_price: float
    liquidation_distance_pct: float
    risk_level: str  # "LOW", "MODERATE", "HIGH", "EXTREME"

    # Capital impact
    buying_power_before: float
    buying_power_after: float
    buying_power_used_pct: float

    # Warnings
    warnings: list[str] = []
    can_proceed: bool
```

#### 4. Auto-Leverage Setting in Order Service
```python
# src/services/order_service.py
class OrderService:
    async def place_order_with_leverage(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        leverage: int | None = None,
        auto_set: bool = True,
        **order_params
    ) -> dict[str, Any]:
        """
        Place order with automatic leverage management.

        Workflow:
        1. Check if position exists for coin
        2. If no position and leverage specified:
           - Set leverage first
           - Then place order
        3. If position exists:
           - Use existing leverage (ignore leverage param)
        4. If no leverage specified:
           - Use system default (settings.DEFAULT_LEVERAGE)
        """
        # Implementation here
```

---

## UX Design: Telegram Bot Flows

### Flow 1: Market Order with Leverage Selection

**Step 1: Initiate Order**
```
/trade -> Market Order -> BTC -> BUY

💰 Enter amount in USD:
(or use quick amounts)

[$100] [$500] [$1000] [Custom]
```

**Step 2: Leverage Selection (NEW!)**
```
⚡ Select Leverage

Your buying power at each level:

1x  → $5,200 available
3x  → $15,600 available ✨ Recommended
5x  → $26,000 available
10x → $52,000 available ⚠️ High Risk
20x → $104,000 available 🔥 EXTREME

Current selection: $1000

[1x] [3x] [5x] [10x] [20x] [Custom]
```

**Step 3: Order Preview (ENHANCED)**
```
📋 Order Preview

Coin: BTC
Side: BUY 🟢
Amount: $1,000
Leverage: 5x ⚡

━━━━━━━━━━━━━━━━━
💰 CAPITAL IMPACT
━━━━━━━━━━━━━━━━━
Margin Required: $200.00
Margin Available: $5,200.00
Buying Power Used: 3.8%

━━━━━━━━━━━━━━━━━
⚠️ RISK ASSESSMENT
━━━━━━━━━━━━━━━━━
Entry Price: ~$98,500 (market)
Est. Liquidation: $78,800
Safety Distance: 20% drop
Risk Level: MODERATE 🟡

Position Size: 0.01015 BTC
Total Exposure: $1,000

✅ You have sufficient margin
✅ Leverage will be set to 5x

[✅ Confirm] [⚙️ Change Leverage] [❌ Cancel]
```

**Step 4: Execution & Confirmation**
```
✅ Order Executed!

⚡ Leverage set to 5x for BTC
📈 Market BUY executed
   Size: 0.01015 BTC
   Avg Fill: $98,523
   Value: $1,000.00

💰 New Position:
   Margin Used: $200
   Liquidation: $78,800 (-20%)

🎯 Track with /positions

[🔙 Back to Menu]
```

---

### Flow 2: Limit Order with Leverage

**Step 1-2**: Same as market order

**Step 3: Price Entry**
```
📊 Set Limit Price

Current BTC: $98,500

Enter your limit price:

[📉 -1%: $97,515]
[📉 -2%: $96,530]
[📉 -5%: $93,575]
[Custom Price]
```

**Step 4: Enhanced Preview (NEW)**
```
📋 Limit Order Preview

Coin: BTC
Side: BUY 🟢 Limit
Amount: $1,000
Price: $96,530 (2% below market)
Leverage: 5x ⚡

━━━━━━━━━━━━━━━━━
💰 CAPITAL IMPACT
━━━━━━━━━━━━━━━━━
Margin Required: $200.00
Margin Reserved: $200.00 🔒
  (locked until filled/cancelled)

Remaining Buying Power: $5,000
  (at 5x leverage)

━━━━━━━━━━━━━━━━━
⚠️ RISK ASSESSMENT
━━━━━━━━━━━━━━━━━
If Filled @ $96,530:
  Position Size: 0.01036 BTC
  Est. Liquidation: $77,224
  Safety Distance: 20% from entry
  Risk Level: MODERATE 🟡

⚠️ Note: Liquidation calculated from
   FILL price, not current price

[✅ Confirm] [⚙️ Adjust] [❌ Cancel]
```

---

### Flow 3: Scale Order with Leverage

**Scale Order Wizard - Leverage Step (NEW)**
```
⚡ Leverage & Capital

Total Order: $5,000 across 5 orders
Price Range: $96k - $100k

Select leverage:

1x  → Need $5,000 margin ❌ Insufficient
3x  → Need $1,667 margin ✅ Available
5x  → Need $1,000 margin ✅ Available
10x → Need $500 margin ✅ Available ⚠️

Your available margin: $5,200

Recommended: 3x-5x for scale orders
(Lower liquidation risk across range)

[3x ✨] [5x] [10x] [Back]
```

**Scale Order Preview (ENHANCED)**
```
📊 Scale Order Preview

5 BTC BUY orders: $96k - $100k
Total: $5,000 | Leverage: 5x ⚡

━━━━━━━━━━━━━━━━━
💰 CAPITAL BREAKDOWN
━━━━━━━━━━━━━━━━━
Total Margin Required: $1,000
  - Reserved now: $1,000 🔒
  - Per order: $200

Remaining Buying Power: $4,200
  (at 5x leverage)

━━━━━━━━━━━━━━━━━
📊 ORDER LADDER
━━━━━━━━━━━━━━━━━
1. $100,000 → $1,000 (0.01 BTC)
2. $99,000  → $1,000 (0.0101 BTC)
3. $98,000  → $1,000 (0.0102 BTC)
4. $97,000  → $1,000 (0.0103 BTC)
5. $96,000  → $1,000 (0.0104 BTC)

━━━━━━━━━━━━━━━━━
⚠️ RISK RANGES
━━━━━━━━━━━━━━━━━
If all filled:
  Avg Entry: ~$98,000
  Position: 0.0510 BTC ($5,000)
  Liquidation: $78,400 (20% drop)
  Risk: MODERATE 🟡

If only top 2 filled:
  Avg Entry: ~$99,500
  Liquidation: $79,600 (20% drop)

⚡ Leverage will be set to 5x for BTC

[✅ Place 5 Orders] [⚙️ Adjust] [❌ Cancel]
```

---

### Flow 4: Leverage Change Warning (Existing Position)

**Scenario**: User tries to place order with different leverage than existing position

```
⚠️ Leverage Cannot Be Changed

You have an open BTC position with 3x leverage.

New orders will use the same leverage (3x).

To use 5x leverage:
1. Close current position
2. Set new leverage
3. Open new position

Current Position:
  Size: 0.05 BTC ($4,900)
  Leverage: 3x
  Liquidation: $65,600

Continue with 3x leverage?

[✅ Yes, Continue] [📊 View Position] [❌ Cancel]
```

---

## Enhanced Position Display (NEW)

### Current Problem
**Existing `/positions` command shows:**
- ✅ Coin, side, size, entry price
- ✅ Current price, PnL, leverage
- ❌ **NO liquidation price** (critical missing!)
- ❌ **NO stop loss orders** associated with position
- ❌ **NO risk distance** indicators

**Why This Is Dangerous:**
Traders can't quickly assess:
- "How close am I to liquidation?"
- "Do I have stop loss protection?"
- "Which positions are most at risk?"

### Enhanced Position View

**Level 1: Positions List (Enhanced)**
```
📊 Open Positions (3)

Total Value: $12,450
Total PnL: +$523 (4.2%) 🟢
Margin Used: 62%

━━━━━━━━━━━━━━━━━
1. 🟢 BTC LONG
   ├─ Size: 0.05 BTC
   ├─ Entry: $98,000
   ├─ Current: $101,500 (+3.6%)
   ├─ PnL: +$175 (+17.5%) 🟢
   ├─ Leverage: 5x ⚡
   ├─ 🎯 Liquidation: $78,400 (-22.7% away)
   ├─ 🛡️ Stop Loss: $95,000 (-6.4% away) ✅
   └─ Risk: LOW 🟢

   [📊 Details] [🛡️ Edit SL] [❌ Close]

━━━━━━━━━━━━━━━━━
2. 🔴 ETH SHORT
   ├─ Size: -2.5 ETH
   ├─ Entry: $3,850
   ├─ Current: $3,920 (-1.8%)
   ├─ PnL: -$87 (-8.7%) 🔴
   ├─ Leverage: 10x ⚡⚡
   ├─ 🎯 Liquidation: $4,235 (+8.0% away) ⚠️
   ├─ 🛡️ Stop Loss: None ❌
   └─ Risk: HIGH 🟡

   [📊 Details] [🛡️ Set SL] [❌ Close]

━━━━━━━━━━━━━━━━━
3. 🟢 SOL LONG
   ├─ Size: 50 SOL
   ├─ Entry: $145.00
   ├─ Current: $152.30 (+5.0%)
   ├─ PnL: +$365 (+50.3%) 🟢
   ├─ Leverage: 3x ⚡
   ├─ 🎯 Liquidation: $96.67 (-36.5% away)
   ├─ 🛡️ Stop Loss: $142.00 (-6.8% away) ✅
   └─ Risk: LOW 🟢

   [📊 Details] [🛡️ Edit SL] [❌ Close]

━━━━━━━━━━━━━━━━━
⚠️ Risk Summary:
• 1 position without stop loss
• 1 position with HIGH risk

[🛡️ Set All SL] [📊 Risk Analysis] [🔙 Back]
```

**Key Enhancements:**
1. **🎯 Liquidation Price**: Shows for EVERY position (cross & isolated)
2. **Distance to Liquidation**: Percentage showing safety buffer
3. **🛡️ Stop Loss Display**: Shows active SL or "None" warning
4. **Risk Indicators**: Color-coded (🟢 LOW, 🟡 HIGH, 🔴 CRITICAL)
5. **Visual Risk Distance**: Uses % to show how close to danger
6. **Quick Actions**: Set/Edit stop loss directly from position list

### Level 2: Individual Position Details

**Detailed Position View (when "📊 Details" clicked)**
```
📊 BTC LONG Position Details

━━━━━━━━━━━━━━━━━
💰 POSITION INFO
━━━━━━━━━━━━━━━━━
Coin: BTC
Side: LONG 🟢
Size: 0.05 BTC
Entry Price: $98,000.00
Current Price: $101,500.00
Position Value: $5,075.00

━━━━━━━━━━━━━━━━━
📈 PERFORMANCE
━━━━━━━━━━━━━━━━━
Unrealized PnL: +$175.00
ROI: +17.5% 🟢
Price Change: +3.6%

━━━━━━━━━━━━━━━━━
⚡ LEVERAGE & MARGIN
━━━━━━━━━━━━━━━━━
Leverage: 5x
Margin Used: $1,015.00
Margin Type: Cross

💡 Note: Cannot change leverage
   while position is open

━━━━━━━━━━━━━━━━━
🎯 RISK METRICS
━━━━━━━━━━━━━━━━━
Liquidation Price: $78,400.00
Distance: -22.7% (from current)
Safety Buffer: $23,100 price drop

Risk Level: LOW 🟢
✅ Healthy liquidation distance

━━━━━━━━━━━━━━━━━
🛡️ STOP LOSS
━━━━━━━━━━━━━━━━━
Active SL: $95,000.00 ✅
Trigger: -6.4% from current
Potential Loss: -$325 (at SL)
Max Loss %: -32.0% (on margin)

Order ID: #12345678
Status: Active 🟢

━━━━━━━━━━━━━━━━━
💡 SCENARIOS
━━━━━━━━━━━━━━━━━
If BTC reaches:
• $105,000 (+3.4%): +$350 PnL
• $110,000 (+8.4%): +$600 PnL
• $95,000 (-6.4%): -$325 (SL hit)
• $78,400 (-22.7%): 💀 Liquidated

[🛡️ Edit Stop Loss]
[📊 Risk Calculator]
[❌ Close Position]
[🔙 Back to Positions]
```

### Level 3: Stop Loss Management

**Set/Edit Stop Loss Flow**
```
🛡️ Set Stop Loss for BTC

Current Position:
Entry: $98,000
Current: $101,500
Size: 0.05 BTC (5x leverage)

━━━━━━━━━━━━━━━━━
Recommended Stop Loss Levels:
━━━━━━━━━━━━━━━━━

Tight (2% risk):
$99,470 (-2.0% from current)
Loss if hit: -$102 (-10% ROI)
[Set SL]

Conservative (5% risk):
$96,425 (-5.0% from current)
Loss if hit: -$254 (-25% ROI)
[Set SL]

Moderate (10% risk):
$91,350 (-10.0% from current)
Loss if hit: -$508 (-50% ROI)
[Set SL]

Wide (15% risk):
$86,275 (-15.0% from current)
Loss if hit: -$762 (-75% ROI)
[Set SL]

━━━━━━━━━━━━━━━━━
⚠️ Warning Zone:
Liquidation: $78,400 (-22.7%)

💡 Recommended: 5-10% for 5x leverage

[Custom Price] [Remove SL] [Cancel]
```

**Custom Stop Loss Entry**
```
🛡️ Custom Stop Loss

Enter stop loss price for BTC:

Current: $101,500
Entry: $98,000
Liquidation: $78,400

Valid range:
• Min: $78,500 (above liquidation)
• Max: $101,400 (below current)

Enter price: $_______

[Confirm] [Cancel]
```

**Stop Loss Confirmation**
```
⚠️ Confirm Stop Loss

Position: BTC LONG
Stop Loss: $95,000

Impact:
• Trigger: -6.4% from current
• Potential Loss: -$325
• ROI at SL: -32.0%
• Distance to liquidation: 16.3%

This will place a limit SELL order
at $95,000 to close your position.

✅ Protects from larger losses
⚠️ May trigger on temporary dips

[✅ Confirm] [❌ Cancel]
```

### Stop Loss Success Message
```
✅ Stop Loss Set!

BTC LONG protected:
🛡️ Stop Loss: $95,000
📉 Trigger: -6.4% from current
💰 Max Loss: -$325 (-32% ROI)

Order ID: #12345678
Status: Active

💡 Your position will auto-close
   if BTC drops to $95,000

[📊 View Position] [🔙 Main Menu]
```

### Risk Summary View (NEW)
```
⚠️ Portfolio Risk Summary

Account Value: $12,450
Positions: 3 open

━━━━━━━━━━━━━━━━━
🎯 LIQUIDATION RISKS
━━━━━━━━━━━━━━━━━

Closest to Liquidation:
1. ETH: 8.0% away 🟡 HIGH
2. BTC: 22.7% away 🟢 LOW
3. SOL: 36.5% away 🟢 LOW

━━━━━━━━━━━━━━━━━
🛡️ STOP LOSS COVERAGE
━━━━━━━━━━━━━━━━━

Protected: 2/3 positions (67%)
Unprotected: 1 position

Missing SL:
• ETH SHORT (-$4,350 exposure) ⚠️

━━━━━━━━━━━━━━━━━
⚡ LEVERAGE BREAKDOWN
━━━━━━━━━━━━━━━━━

3x: 1 position ($7,250)
5x: 1 position ($5,075)
10x: 1 position ($4,350) ⚠️

Average Leverage: 5.4x

━━━━━━━━━━━━━━━━━
💡 RECOMMENDATIONS
━━━━━━━━━━━━━━━━━

⚠️ Set stop loss for ETH
⚠️ Consider reducing ETH leverage
✅ BTC and SOL well protected

[🛡️ Set Missing SL] [📊 Details] [🔙 Back]
```

---

## Additional UX Enhancements

### 1. Quick Leverage Preset Buttons
```
Settings -> Trading Preferences

Default Leverage: [3x]
Quick Presets: [1x] [3x] [5x] [10x]

⚡ Market Orders:
  □ Always ask for leverage
  ☑ Use default leverage (3x)
  □ Use position leverage if exists

📊 Limit Orders:
  ☑ Always ask for leverage
  □ Use default leverage (3x)

🎯 Scale Orders:
  ☑ Always ask for leverage
  □ Use default leverage (3x)
```

### 2. /buyingpower Command (NEW)
```
/buyingpower

💰 Your Buying Power

Account Value: $5,200
Free Margin: $5,200 (100%)

━━━━━━━━━━━━━━━━━
Available at Each Leverage:
━━━━━━━━━━━━━━━━━
1x  → $5,200
3x  → $15,600 ✨
5x  → $26,000
10x → $52,000 ⚠️
20x → $104,000 🔥

━━━━━━━━━━━━━━━━━
Current Positions:
━━━━━━━━━━━━━━━━━
(No open positions)

Margin Usage: 0%
Available for trading: 100%

[🔄 Refresh] [📊 Positions]
```

### 3. Risk Calculator (NEW)
```
/riskcalc

🎯 Risk Calculator

Calculate potential outcomes:

Enter trade details:
Coin: [BTC]
Direction: [Long] [Short]
Entry: [$98,500] (market)
Size: [$1,000]
Leverage: [5x]

━━━━━━━━━━━━━━━━━
Results:
━━━━━━━━━━━━━━━━━
Position: 0.01015 BTC
Margin: $200
Liquidation: $78,800 (-20%)

Profit/Loss Scenarios:
+5%  ($103,425): +$253 (+126% ROI)
+10% ($108,350): +$508 (+254% ROI)
-5%  ($93,575):  -$253 (-126% ROI)
-10% ($88,650):  -$508 (-254% ROI)
-20% ($78,800):  💀 LIQUIDATED

[📊 Detailed] [💾 Save] [🔙 Back]
```

### 4. Margin Alerts (Proactive Warnings)
```
⚠️ High Margin Usage Alert

Your margin usage: 87%

Account Value: $5,200
Used Margin: $4,524
Available: $676

Positions at risk if market moves:
• BTC: Liq @ $78,800 (-20%)
• ETH: Liq @ $1,850 (-18%)

Consider:
• Reduce position sizes
• Lower leverage
• Add more margin

[📊 View Positions] [💰 Deposit] [🔕 Snooze]
```

---

## API Changes

### New Endpoints

```python
# GET /api/account/buying-power
GET /api/account/buying-power?coin=BTC&leverage_levels=1,3,5,10
Response: {
  "coin": "BTC",
  "account_value": 5200.00,
  "margin_available": 5200.00,
  "buying_power_levels": [
    {"leverage": 1, "buying_power": 5200, "can_trade": true},
    {"leverage": 3, "buying_power": 15600, "can_trade": true},
    {"leverage": 5, "buying_power": 26000, "can_trade": true},
    {"leverage": 10, "buying_power": 52000, "can_trade": true}
  ]
}

# POST /api/orders/preview
POST /api/orders/preview
Body: {
  "coin": "BTC",
  "is_buy": true,
  "size_usd": 1000,
  "leverage": 5,
  "is_market": true
}
Response: {
  "coin": "BTC",
  "side": "BUY",
  "size_usd": 1000,
  "leverage": 5,
  "margin_required": 200,
  "margin_available": 5200,
  "estimated_liquidation": 78800,
  "risk_level": "MODERATE",
  "can_proceed": true,
  "warnings": []
}

# Enhanced order endpoints (all support leverage param)
POST /api/orders/market
Body: {
  "coin": "BTC",
  "is_buy": true,
  "size": 0.01,
  "leverage": 5,  // NEW
  "auto_set_leverage": true  // NEW
}

POST /api/orders/limit
Body: {
  "coin": "BTC",
  "is_buy": true,
  "size": 0.01,
  "limit_price": 96500,
  "leverage": 5  // NEW
}

POST /api/scale-orders/place
Body: {
  "coin": "BTC",
  "is_buy": true,
  "total_usd_amount": 5000,
  "num_orders": 5,
  "start_price": 100000,
  "end_price": 96000,
  "leverage": 5  // NEW
}
```

---

## Implementation Plan

### Phase 7A: Backend Foundation (1.5 days)
- [ ] Create `CalculateBuyingPowerUseCase`
- [ ] Create `PreviewOrderUseCase`
- [ ] Add leverage parameter to all order models
- [ ] Implement auto-leverage setting in `OrderService`
- [ ] Add buying power calculations to `AccountService`
- [ ] **NEW**: Create `ManageStopLossUseCase` (set/remove/get)
- [ ] **NEW**: Enhance `PositionService` to calculate liquidation for all positions
- [ ] **NEW**: Add stop loss detection in position queries
- [ ] Unit tests (target: 90% coverage)

### Phase 7B: API Integration (0.5 days)
- [ ] Add `/api/account/buying-power` endpoint
- [ ] Add `/api/orders/preview` endpoint
- [ ] Update all order endpoints to accept leverage
- [ ] **NEW**: Add `/api/positions/{coin}/stop-loss` endpoints (GET/POST/DELETE)
- [ ] **NEW**: Enhance `/api/positions` response with liquidation & SL data
- [ ] Update OpenAPI/Swagger docs
- [ ] Integration tests

### Phase 7C: Telegram Bot UX - Orders (1 day)
- [ ] Add leverage selection step to market order wizard
- [ ] Add leverage selection to limit order wizard
- [ ] Add leverage selection to scale order wizard
- [ ] Enhance all order previews with capital/risk metrics
- [ ] Add `/buyingpower` command
- [ ] Add `/riskcalc` command (optional)
- [ ] Update settings menu for leverage preferences

### Phase 7D: Telegram Bot UX - Positions (1 day)
- [ ] **NEW**: Enhance `/positions` command with liquidation prices
- [ ] **NEW**: Add stop loss display to position list
- [ ] **NEW**: Add risk distance indicators (% to liquidation)
- [ ] **NEW**: Create detailed position view with full metrics
- [ ] **NEW**: Implement stop loss wizard (set/edit/remove)
- [ ] **NEW**: Add recommended SL levels calculator
- [ ] **NEW**: Create `/risksum` or integrate into /positions for risk summary
- [ ] **NEW**: Add "Set All SL" bulk action
- [ ] Update position formatters

### Phase 7E: Polish & Safety (0.5 days)
- [ ] Add confirmation dialogs for high leverage (>10x)
- [ ] Add margin usage warnings (>80%)
- [ ] Implement "existing position" leverage conflict handling
- [ ] **NEW**: Add warnings for positions without stop loss
- [ ] **NEW**: Add liquidation proximity alerts (< 10% away)
- [ ] Add helpful error messages
- [ ] End-to-end testing on testnet

### Phase 7F: Documentation (0.5 days)
- [ ] Update user documentation
- [ ] Add leverage examples to README
- [ ] **NEW**: Add stop loss best practices guide
- [ ] **NEW**: Document liquidation calculation methods
- [ ] Update API documentation
- [ ] Create trading safety guide

---

## Success Criteria

### Functional Requirements
- ✅ All order types support leverage parameter
- ✅ Buying power calculated for all leverage levels
- ✅ Order preview shows complete risk assessment
- ✅ Auto-leverage setting works correctly
- ✅ Existing position leverage conflicts handled gracefully
- ✅ **NEW**: Liquidation price displayed for ALL positions (100% coverage)
- ✅ **NEW**: Stop loss orders correctly associated with positions
- ✅ **NEW**: Stop loss set/edit/remove functionality working
- ✅ **NEW**: Risk distance calculations accurate

### UX Requirements
- ✅ <3 taps to select leverage during order flow
- ✅ Capital impact visible before every order
- ✅ Clear risk visualization (liquidation price, distance)
- ✅ No confusing error messages
- ✅ Consistent UX across all order types
- ✅ **NEW**: Liquidation visible in position list (no need to drill down)
- ✅ **NEW**: Stop loss status immediately visible
- ✅ **NEW**: Quick access to set/edit SL from position view
- ✅ **NEW**: Color-coded risk indicators for quick scanning

### Safety Requirements
- ✅ Cannot place order with insufficient margin
- ✅ High leverage (>10x) requires extra confirmation
- ✅ Liquidation price always displayed
- ✅ Warnings for high margin usage (>80%)
- ✅ Clear indication when leverage cannot be changed
- ✅ **NEW**: Warnings for positions without stop loss
- ✅ **NEW**: Alerts when liquidation distance < 10%
- ✅ **NEW**: Stop loss price validation (must be above liquidation for longs)
- ✅ **NEW**: Cannot set SL too close to current price (min 1% distance)

### Testing Requirements
- ✅ 90%+ test coverage on new code
- ✅ All edge cases covered (insufficient margin, existing positions, etc.)
- ✅ Integration tests on testnet
- ✅ Manual testing of complete user flows
- ✅ **NEW**: Stop loss order placement tests
- ✅ **NEW**: Liquidation calculation accuracy tests
- ✅ **NEW**: Cross/isolated margin handling tests

---

## Risks & Mitigations

### Risk 1: Complexity in Order Flow
**Impact**: Users confused by too many steps
**Mitigation**:
- Default leverage from settings (skip step if desired)
- Remember last used leverage per coin
- Quick preset buttons (1x, 3x, 5x, 10x)

### Risk 2: Calculation Errors
**Impact**: Wrong liquidation price shown, users get liquidated
**Mitigation**:
- Comprehensive unit tests
- Cross-validate with Hyperliquid API
- Conservative estimates (round down buying power, round up liquidation risk)
- Testnet validation before production

### Risk 3: Performance Impact
**Impact**: Slow order placement due to extra calculations
**Mitigation**:
- Cache account value for 10 seconds
- Async calculation of previews
- Show preview while calculating (progressive loading)

### Risk 4: User Ignores Warnings
**Impact**: Users still place risky trades despite warnings
**Mitigation**:
- Require explicit confirmation for leverage >10x
- Show liquidation scenarios in simple terms
- Add "education mode" that explains risks

---

## Future Enhancements (Phase 8+)

1. **Smart Leverage Suggestions**
   - ML model suggests optimal leverage based on volatility
   - "Other traders using 3-5x for BTC right now"

2. **Position Size Calculator**
   - "Risk 2% of account on this trade" → auto-calculate size

3. **Leverage Presets per Coin**
   - BTC: Default 3x (less volatile)
   - Altcoins: Default 2x (more volatile)

4. **Margin Usage Charts**
   - Visual timeline of margin usage over time
   - Alerts when approaching dangerous levels

5. **Backtesting**
   - "What if I used 5x instead of 3x last month?"

---

## References

- [Hyperliquid Leverage Docs](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/leverage)
- [BitMEX Risk Management Guide](https://www.bitmex.com/app/riskManagement)
- [Binance Margin Trading](https://www.binance.com/en/support/faq/margin-trading)
- Current implementation: `src/services/leverage_service.py`

---

**Last Updated**: 2025-12-01
**Author**: Hyperbot Development Team
**Status**: 📋 Ready for Implementation
**Duration Estimate**: 4.5-5 days (extended to include position enhancements)

---

## Summary of New Features

### Order Placement Enhancements
1. ✅ Inline leverage selection during order flow
2. ✅ Real-time buying power visibility at each leverage level
3. ✅ Complete order preview with capital impact & risk metrics
4. ✅ Auto-leverage setting (no separate step required)
5. ✅ Consistent UX across market/limit/scale orders

### Position Management Enhancements (NEW)
1. ✅ Liquidation price displayed for ALL positions
2. ✅ Distance-to-liquidation percentage indicators
3. ✅ Stop loss order integration and visibility
4. ✅ Quick stop loss set/edit/remove actions
5. ✅ Recommended stop loss levels based on leverage
6. ✅ Risk summary view across all positions
7. ✅ Visual risk indicators (color-coded)
8. ✅ Warnings for unprotected positions

### Safety Improvements
1. ✅ Prevent orders with insufficient capital
2. ✅ Liquidation proximity warnings
3. ✅ Stop loss coverage tracking
4. ✅ High leverage confirmations
5. ✅ Risk-based position highlighting

**Note**: Leverage cannot be changed on existing positions (Hyperliquid limitation - by design, no action needed)
