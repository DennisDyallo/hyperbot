# Phase 7: Leverage-Aware Order Placement & Capital Transparency

**Status**: 📋 Planned (Enhanced with UX Best Practices)
**Priority**: HIGH - Critical UX improvement for safe trading
**Duration**: 4.5-5 days
**Target Completion**: TBD

---

## 🎯 Quick Reference: Key UX Improvements

This plan has been enhanced with professional Telegram trading bot UX principles:

### Core Design Philosophy
1. **Progressive Disclosure**: Quick preview (default) + Full details (optional)
2. **Mobile-First**: All previews fit on small screens without scrolling
3. **Context-Aware**: Recommendations based on order size, not generic
4. **Action-Oriented**: Buttons say "Buy $1,000 BTC" not "Confirm"
5. **Safety Through Transparency**: Show consequences, don't just restrict

### Major UX Enhancements
- ✅ **Two-Tier Previews**: Quick (80% use case) vs. Full (power users)
- ✅ **Smart Leverage Labels**: "Good for this size" vs. generic "Recommended"
- ✅ **Risk-Sorted Positions**: Dangerous positions highlighted first
- ✅ **Clearer Stop Loss Labels**: "SAFE/BALANCED/WIDE" vs. "2% risk"
- ✅ **Loading States**: Every async operation shows progress
- ✅ **30-Second Undo**: Order modification window
- ✅ **Tutorial Mode**: First-time user onboarding
- ✅ **"?" Helpers**: Optional explanations without patronizing
- ✅ **Bulk Actions**: Set all stop losses with single flow

### Implementation Strategy
**Ship in phases**: 7C-Lite (basic flow) → Get feedback → 7C-Full (enhanced features)

---

## 👨‍💻 Developer's Expert Assessment

**Date**: 2025-12-01
**Analysis**: Comprehensive review of existing wizard architecture

### Current Implementation Analysis

After deep-diving into `wizard_market_order.py` (390 lines) and comparing with other wizards in the codebase, here's the architectural reality:

#### ✅ What's Working Well

1. **State Machine Pattern**: ConversationHandler is optimal for Telegram bots
   - Clear state transitions (COIN → SIDE → AMOUNT → CONFIRM)
   - Proper entry points, state handlers, and fallbacks
   - Each handler returns next state or END

2. **Error Handling**: Consistent utility functions
   - `send_success_and_end()`, `send_error_and_end()`, `send_cancel_and_end()`
   - All exit paths return to main menu
   - User data properly cleaned up

3. **Dual Input Support**: Buttons + text input
   - Quick preset buttons for common values
   - "Custom" option for flexibility
   - Proper validation and re-prompting

#### ❌ Problems Identified

1. **Code Duplication** (~73 lines total):
   ```python
   # Confirmation message appears 2x (in amount_selected and amount_text_input)
   side_emoji = "🟢" if is_buy else "🔴"
   text = (
       f"{side_emoji} **Confirm Market Order**\n\n"
       f"**Coin**: {coin}\n"
       # ... 19 lines duplicated
   )
   # Saves: 38 lines

   # Query extraction boilerplate appears 7x
   query = update.callback_query
   assert query is not None
   await query.answer()
   # Saves: 35 lines
   ```

2. **Menu Builder Coupling**:
   - 4 external menu functions in `menus.py` (54 lines)
   - Hard to customize per wizard
   - Duplicate button patterns

3. **No Risk Preview**:
   - Missing liquidation price display
   - No margin requirement calculation
   - No buying power visibility
   - No risk level assessment

### Component Library Reality Check

**Initial Approach (FAILED)**: `OrderFlowOrchestrator`
- ❌ Tried to orchestrate entire flow (steps 1-6)
- ❌ Conflicts with ConversationHandler (already does orchestration)
- ❌ Methods are async and edit messages directly
- ❌ Cannot return `(text, markup)` tuples for flexible use
- ❌ Wrong abstraction level

**Why It Failed**:
```python
# OrderFlowOrchestrator tries to do THIS:
async def step_2_side_selection(self, update, context, coin):
    # Builds text, builds buttons, edits message
    await query.edit_message_text(...)
    # But ConversationHandler already manages the flow!

# What we ACTUALLY need:
text = build_order_preview(coin, side, amount)  # Just returns text
buttons = build_confirm_cancel("market")         # Just returns markup
```

**Correct Approach**: Building blocks, not orchestration

### What Components Should Provide

#### 1. Preview Message Builder ✅ HIGH VALUE
```python
preview_text = build_order_preview(
    coin="BTC",
    side="BUY",
    usd_amount=100.0,
    coin_size=0.05,
    price=2000.0,
    leverage=5,
    margin_required=20.0,
    liquidation_price=1600.0,
    risk_level="MODERATE"
)
```
**Saves**: 38 lines of duplication

#### 2. Button Builder ✅ EXISTS (needs refinement)
```python
buttons = ButtonBuilder()
buttons.add_row(("$10", "amount:10"), ("$25", "amount:25"))
return buttons.build()
```
**Saves**: 60 lines (4 menu functions)

#### 3. State Extractor Helper (NEW)
```python
@extract_callback_state
async def handler(update, context, query, user_data):
    # query and user_data already extracted and validated
```
**Saves**: 35 lines of boilerplate

#### 4. Loading Context Manager (NEW)
```python
async with LoadingMessage(query, f"Fetching {coin} price..."):
    coin_size, price = convert_usd_to_coin(usd_amount, coin)
```
**Benefit**: Cleaner async patterns

### Realistic POC Metrics

**Current Implementation**:
- Lines: 390
- Handlers: 8 async functions
- States: 4
- External dependencies: 4 menu builders
- Duplication: ~73 lines

**With Proper Components** (estimated):
- Lines: ~280-310
- Reduction: **20-28%**
- Handlers: 8 (same - no change needed)
- States: 4 (same - ConversationHandler is optimal)
- External dependencies: 0 (inline ButtonBuilder)
- Duplication: <10 lines

### Key Learnings

1. **ConversationHandler Pattern is Optimal**: Don't try to replace it
2. **Components Should Be Builders**: Not orchestrators
3. **Focus on Duplication**: Preview messages, button patterns
4. **Keep State Management Simple**: user_data is good enough
5. **Async is Unavoidable**: Embrace it with proper patterns

### Recommended Implementation Strategy

#### Phase 1: Extract Helpers (Low Risk)
1. `build_order_preview()` → Returns formatted text with all metrics
2. Replace `menus.py` functions with `ButtonBuilder` patterns
3. Create `@extract_callback_state` decorator
4. Add `LoadingMessage` context manager

#### Phase 2: Enhance Wizard (Moderate Risk)
1. Add leverage selection step (new state)
2. Add buying power calculation
3. Use preview builder for confirmation
4. Add risk metrics display

#### Phase 3: Test & Iterate
- Refactor one handler at a time
- Keep old version as fallback
- A/B test with users

### Time Estimate (Realistic)

**To Build Market Order Wizard from Scratch**:
- With current patterns: 4-6 hours (experienced dev)
- With proper components: 2-3 hours (50% faster)
- Testing + edge cases: +2-3 hours
- **Total**: 6-9 hours for production-ready wizard

**To Refactor Existing Wizard**:
- Extract preview builder: 2 hours
- Refactor to use components: 3-4 hours
- Testing: 2 hours
- **Total**: 7-8 hours

### Critical Insights for Phase 7

1. **Don't Rebuild Wizards**: Just enhance with new steps
2. **Add Leverage Step**: Insert between AMOUNT and CONFIRM
3. **Use Preview Builder**: Show capital impact + risk metrics
4. **Keep Existing Patterns**: They work, just reduce duplication
5. **Test Incrementally**: One wizard at a time

### The Path Forward

```
PHASE 7 Implementation Reality:

NOT: Rewrite all wizards with components
BUT: Add leverage selection + preview enhancement

Steps:
1. Create preview builder with leverage metrics
2. Add LEVERAGE state to market wizard
3. Enhance CONFIRM step to show capital impact
4. Test thoroughly
5. Repeat for limit and scale wizards
```

**Conclusion**: The component library needs redesign to provide **building blocks** (preview builders, button helpers) not **orchestration** (flow management). The ConversationHandler pattern is already optimal - we just need better tools to build the pieces.

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
⚡ Select Leverage for $1,000 BTC

Your order: $1,000
Available: $5,200

1x  → $5,200 max ⚪ Conservative
3x  → $15,600 max ✨ Good for this size
5x  → $26,000 max 🟡 Higher risk
10x → $52,000 max 🔴 Risky
20x → $104,000 max � Extreme risk

💡 For $1,000 orders, 3-5x balances
   opportunity and safety.

[1x] [3x ✨] [5x] [10x] [20x] [Custom]
```

**Step 3: Order Preview (ENHANCED - Two-Tier System)**

**Quick Preview (Default - Mobile Optimized)**
```
📋 Order Preview

💰 BTC BUY: $1,000 @ market
⚡ Leverage: 5x
📊 Margin: $200 / $5,200 available
🎯 Liquidation: $78,800 (-20%)
⚠️ Risk: MODERATE 🟡

[✅ Buy $1,000 BTC] [📊 Full Details] [❌ Cancel]
```

**Full Preview (Optional - When User Clicks "📊 Full Details")**
```
📋 Complete Order Analysis

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
Risk Level: MODERATE 🟡 [?]

Position Size: 0.01015 BTC
Total Exposure: $1,000

✅ You have sufficient margin
✅ Leverage will be set to 5x

[✅ Buy $1,000 BTC] [⚙️ Change Leverage] [❌ Cancel]
```

**"[?]" Helper (When Clicked)**
```
💡 MODERATE Risk means:
• Liquidation 15-25% away
• Normal for 5x leverage
• Consider stop loss protection
• Typical for intermediate traders

[Close]
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

━━━━━━━━━━━━━━━━━
What's next?
[🛡️ Set Stop Loss] [📊 View Position] [🔙 Main Menu]
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

**Step 4: Enhanced Preview (NEW - Two-Tier System)**

**Quick Preview (Default)**
```
📋 Limit Order Preview

💰 BTC BUY: $1,000 @ $96,530
⚡ Leverage: 5x
📊 Margin Reserved: $200 🔒
🎯 If filled, liq: $77,224 (-20%)
⚠️ Risk: MODERATE 🟡

[✅ Place Limit Order] [📊 Full Details] [❌ Cancel]
```

**Full Preview (Optional)**
```
📋 Complete Limit Order Analysis

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

[✅ Place Limit Order] [⚙️ Adjust] [❌ Cancel]
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

**Scale Order Preview (ENHANCED - Simplified with Expansion)**

**Quick Preview (Default)**
```
📊 Scale Order Preview

5 BUY orders: $96k-$100k @ 5x ⚡
Total: $5,000 | Margin: $1,000

━━━━━━━━━━━━━━━━━
If All Filled:
Entry: ~$98,000
Liquidation: $78,400 (-20%)
Risk: MODERATE 🟡

[📋 View All Orders] [✅ Place 5 Orders] [❌ Cancel]
```

**Expanded View (When "📋 View All Orders" Clicked)**
```
📊 Complete Scale Order Analysis

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

💡 Tip: This is a Hyperliquid platform
   limitation, not a bot restriction.

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

**Level 1: Positions List (Enhanced - Risk-Sorted)**
```
📊 Open Positions (3)

Total Value: $12,450
Total PnL: +$523 (4.2%) 🟢
Margin Used: 62%

Sort: [⚠️ Risk] [💰 Size] [📈 PnL] [🔤 Name]

━━━━━━━━━━━━━━━━━
⚠️ NEEDS ATTENTION (1)
━━━━━━━━━━━━━━━━━
🔴 ETH SHORT • -$87 (8.7%)
   Liq: 8% away ⚠️ | No SL ❌
   [🛡️ Set SL] [📊 Details] [❌ Close]

━━━━━━━━━━━━━━━━━
✅ PROTECTED (2)
━━━━━━━━━━━━━━━━━
🟢 BTC LONG • +$175 (17.5%)
   Liq: 22.7% away | SL ✅
   [📊 Details]

🟢 SOL LONG • +$365 (50.3%)
   Liq: 36.5% away | SL ✅
   [📊 Details]

━━━━━━━━━━━━━━━━━
⚠️ Risk Summary:
• 1 position without stop loss
• 1 position with HIGH risk

[🛡️ Set All SL] [📊 Risk Analysis] [🔙 Back]
```

**Alternative: Traditional View (When Sorted by Name/Size/PnL)**
```
📊 Open Positions (3)

Total Value: $12,450
Total PnL: +$523 (4.2%) 🟢
Margin Used: 62%

Sort: [⚠️ Risk] [💰 Size] [📈 PnL] [🔤 Name]

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
Suggested Stop Loss Levels:
━━━━━━━━━━━━━━━━━

🟢 SAFE (protects most gains)
$99,470 • 2% below current
   If hit: Keep +$70 profit
   [Set SL]

🟡 BALANCED (normal volatility buffer)
$96,425 • 5% below current
   If hit: -$254 loss
   [Set SL]

🟠 WIDE (for volatile markets)
$91,350 • 10% below current
   If hit: -$508 loss
   [Set SL]

💀 Liquidation: $78,400 (-22.7%)

💡 Tip: For 5x leverage, 5-10% SL
   is common practice.

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

💡 You can modify this later if needed

[✅ Set Stop Loss @ $95k] [❌ Cancel]
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

### 5. Loading States (NEW - Critical for UX)
```
When calculating preview:
⏳ Calculating buying power...

When fetching price:
⏳ Fetching current BTC price...

When placing order:
⏳ Placing order...

When setting leverage:
⏳ Setting leverage to 5x...
```

### 6. Bulk Stop Loss Confirmation (NEW)
```
🛡️ Set Stop Loss for 3 Positions

You're about to set stop loss for:

• BTC @ $95,000 (5% below current)
  Max loss: -$325

• ETH @ $3,700 (5% below current)
  Max loss: -$487

• SOL @ $140.00 (8% below current)
  Max loss: -$250

Total potential loss: -$1,062

[✅ Set All] [⚙️ Customize Each] [❌ Cancel]
```

### 7. Tutorial Mode / First Time Experience (NEW)
```
🎓 Welcome to Leverage Trading!

This is your first time placing
a leveraged order. Let's learn:

What is Leverage?
Leverage lets you control a larger
position with less capital.

Example:
• Without leverage: $1,000 = $1,000 BTC
• With 5x leverage: $1,000 = $5,000 BTC

⚠️ But remember:
• Profits are multiplied by 5x
• Losses are also multiplied by 5x
• Risk of liquidation exists

[📚 Learn More] [✅ I Understand] [Skip Tutorial]
```

### 8. Order Modification Window (NEW)
```
✅ Limit Order Placed!

Order ID: #12345678
BTC BUY @ $96,530
Size: $1,000

Your order is now active.

⏪ Changed your mind?
   [Cancel Order] (30 sec remaining)

After 30 seconds, use /orders to
manage this order.

[📊 View Orders] [🔙 Main Menu]
```

### 9. Leverage Lock Warning - First Position (NEW)
```
⚠️ Important: Leverage Lock

Once you open this 5x position,
you CANNOT change leverage until
you close the position completely.

Future BTC orders will automatically
use 5x leverage.

This is how Hyperliquid works,
not a bot limitation.

☑️ I understand leverage is locked
   after opening position

[✅ Continue] [📚 Learn More] [❌ Cancel]
```

### 10. Cross Margin Warning (NEW - If Applicable)
```
⚠️ Cross Margin Mode Active

ALL your account balance backs
this position.

Impact:
• Shared margin across all positions
• One liquidation can affect others
• Better capital efficiency
• Higher systemic risk

Alternative: Use isolated margin
to limit risk per position.

[📚 Learn More] [✅ I Understand, Continue] [❌ Cancel]
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
- [ ] Create `PreviewOrderUseCase` (supports both quick & full preview modes)
- [ ] Add leverage parameter to all order models
- [ ] Implement auto-leverage setting in `OrderService`
- [ ] Add buying power calculations to `AccountService`
- [ ] **NEW**: Create `ManageStopLossUseCase` (set/remove/get)
- [ ] **NEW**: Enhance `PositionService` to calculate liquidation for all positions
- [ ] **NEW**: Add stop loss detection in position queries
- [ ] **NEW**: Add risk sorting logic for positions
- [ ] Unit tests (target: 90% coverage)

### Phase 7B: API Integration (0.5 days)
- [ ] Add `/api/account/buying-power` endpoint
- [ ] Add `/api/orders/preview` endpoint (with `detail_level` param: "quick"/"full")
- [ ] Update all order endpoints to accept leverage
- [ ] **NEW**: Add `/api/positions/{coin}/stop-loss` endpoints (GET/POST/DELETE)
- [ ] **NEW**: Enhance `/api/positions` response with liquidation & SL data
- [ ] **NEW**: Add sort parameter to `/api/positions` (risk/size/pnl/name)
- [ ] Update OpenAPI/Swagger docs
- [ ] Integration tests

### Phase 7C-Lite: Simple Order Flow FIRST (1 day) ⭐ PRIORITY
**Goal**: Ship basic leverage-aware ordering quickly, get user feedback

- [ ] Add context-aware leverage selection to market order wizard
- [ ] Add leverage selection to limit order wizard
- [ ] Implement QUICK preview for all order types (mobile-optimized)
- [ ] Add action-oriented confirmation buttons
- [ ] Implement loading states for all async operations
- [ ] Add leverage lock warning for first-time position opening
- [ ] Basic error messages with helpful guidance
- [ ] Manual testing on testnet

**Ship to beta users, collect feedback before Phase 7C-Full**

### Phase 7D: Position Enhancements (1 day)
- [ ] **NEW**: Enhance `/positions` command with liquidation prices
- [ ] **NEW**: Add stop loss display to position list
- [ ] **NEW**: Add risk distance indicators (% to liquidation)
- [ ] **NEW**: Implement risk-based sorting with grouping (Needs Attention / Protected)
- [ ] **NEW**: Add sort controls (Risk/Size/PnL/Name)
- [ ] **NEW**: Create detailed position view with full metrics
- [ ] **NEW**: Implement stop loss wizard with improved labeling (SAFE/BALANCED/WIDE)
- [ ] **NEW**: Add recommended SL levels calculator
- [ ] **NEW**: Create risk summary view
- [ ] **NEW**: Add "Set All SL" bulk action with confirmation
- [ ] Update position formatters

### Phase 7C-Full: Enhanced Order Flows (0.5 days)
**Goal**: Add power-user features based on Phase 7C-Lite feedback

- [ ] Add "Full Details" expansion to all previews
- [ ] Implement "?" helper tooltips for risk levels
- [ ] Add leverage selection to scale order wizard
- [ ] Add enhanced scale order preview with expansion
- [ ] Add `/buyingpower` command
- [ ] Add `/riskcalc` command (optional)
- [ ] Update settings menu for leverage preferences
- [ ] Add tutorial mode for first-time users
- [ ] Add 30-second order modification window

### Phase 7E: Polish & Safety (0.5 days)
- [ ] Add confirmation dialogs for high leverage (>10x)
- [ ] Add margin usage warnings (>80%)
- [ ] Implement "existing position" leverage conflict handling
- [ ] **NEW**: Add warnings for positions without stop loss
- [ ] **NEW**: Add liquidation proximity alerts (< 10% away)
- [ ] **NEW**: Add cross margin warning (if applicable)
- [ ] Add bulk stop loss confirmation
- [ ] Improve all error messages with actionable guidance
- [ ] Add loading state polish (progress indicators)
- [ ] End-to-end testing on testnet

### Phase 7F: Documentation & Launch (0.5 days)
- [ ] Update user documentation
- [ ] Add leverage examples to README
- [ ] **NEW**: Add stop loss best practices guide
- [ ] **NEW**: Document liquidation calculation methods
- [ ] **NEW**: Create UX decision log (why we chose two-tier previews, etc.)
- [ ] Update API documentation
- [ ] Create trading safety guide
- [ ] Set up metrics tracking (error rates, preview abandonment, etc.)
- [ ] Create user survey for feedback collection
- [ ] Launch announcement with tutorial

---

**Implementation Priority Rationale**:

1. **7A-7B (Backend/API)**: Foundation must be solid
2. **7C-Lite (Simple Flow)**: Ship fast, validate UX with real users
3. **7D (Positions)**: High-value safety feature
4. **7C-Full (Enhanced)**: Add depth based on feedback
5. **7E-7F (Polish/Launch)**: Final touches and documentation

**Key Change**: Split Phase 7C into 7C-Lite and 7C-Full to enable faster iteration and user feedback

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

## UX Design Principles Applied

### 1. Progressive Disclosure
**Problem**: Information overload on mobile screens
**Solution**: Two-tier preview system
- Quick preview (80% use case): Essential info only
- Full details (20% use case): Comprehensive analysis
- Users choose their depth of information

### 2. Mobile-First Design
**Considerations**:
- Telegram primarily used on mobile devices
- Limited screen real estate
- Quick decision-making context
- Thumb-friendly button placement

**Implementation**:
- Quick previews fit in one screen
- Most important info at the top
- Action buttons use clear, specific language
- Loading states prevent perceived lag

### 3. Context-Aware Intelligence
**Examples**:
- Leverage recommendations based on ORDER SIZE, not just generic
- Risk sorting shows dangerous positions first
- Warnings appear only when relevant
- Bulk actions when multiple items need attention

### 4. Scannability
**Techniques**:
- Color coding (🟢🟡🔴) for instant risk assessment
- Grouping (Protected vs. Needs Attention)
- Visual hierarchy with emojis and separators
- Consistent formatting patterns

### 5. Action-Oriented Language
**Instead of**: "Confirm" → **Use**: "Buy $1,000 BTC"
**Instead of**: "Set SL" → **Use**: "Set Stop Loss @ $95k"
**Instead of**: "Continue" → **Use**: "I Understand, Continue"

**Why**: Specific actions reduce cognitive load and prevent errors

### 6. Educational Without Patronizing
**Balance**:
- Tips and helpers available but not forced
- "?" buttons for optional learning
- Tutorial mode for first-timers
- Expert users can skip explanations

### 7. Safety Through Transparency
**Not**: "Don't use high leverage"
**Instead**: Show exact consequences (liquidation price, distance, potential loss)

**Philosophy**: Informed traders make better decisions than restricted ones

### 8. Fail-Safe Defaults
- Default leverage: Conservative (3x)
- Default sort: Risk (most dangerous first)
- Default view: Quick preview (less overwhelming)
- Confirmations required for high-risk actions

### 9. Consistent Mental Models
**Order Flow Pattern** (all order types):
1. Select coin & direction
2. Enter size
3. Choose leverage (same UI every time)
4. See preview (same format every time)
5. Confirm (action-specific button)

**Why**: Muscle memory reduces errors

### 10. Forgiveness
- 30-second undo window for orders
- Edit capabilities for stop losses
- Clear "Back" options at every step
- No dead ends in the UI

---

## UX Testing Checklist

### Usability Tests
- [ ] New user can place first order in <2 minutes
- [ ] Experienced user can place order in <30 seconds
- [ ] Users understand leverage impact before confirmation
- [ ] Users can identify highest-risk position in <5 seconds
- [ ] Users can set stop loss without confusion
- [ ] No "I don't know what to do" moments

### Mobile Testing
- [ ] All previews readable on iPhone SE (smallest screen)
- [ ] Buttons thumb-reachable on 6.7" phones
- [ ] No horizontal scrolling required
- [ ] Text size readable without zooming
- [ ] Loading states visible on slow connections

### Error Prevention
- [ ] Cannot place order with insufficient margin
- [ ] Cannot set invalid stop loss (too close/beyond liquidation)
- [ ] High leverage requires explicit confirmation
- [ ] Warnings appear before dangerous actions
- [ ] Validation messages are helpful, not just "Error"

### Performance
- [ ] Quick preview appears in <1 second
- [ ] Full preview loads in <2 seconds
- [ ] Leverage selection feels instant
- [ ] No "hanging" states without feedback
- [ ] Graceful degradation on network issues

### Accessibility
- [ ] Clear visual hierarchy without color dependence
- [ ] Emojis supplement text, don't replace it
- [ ] All critical info text-based (not emoji-only)
- [ ] Consistent terminology throughout

---

## Metrics to Track Post-Launch

### Success Metrics
- **Order Error Rate**: Target <1% (orders placed with wrong leverage/size)
- **Preview Abandonment**: Target <10% (users who see preview but cancel)
- **Stop Loss Coverage**: Target >80% of positions have SL within 24h
- **Time to Place Order**: Target <60 seconds for market orders
- **User Confidence Score**: Survey rating >4.5/5

### Risk Metrics
- **Unexpected Liquidations**: Target 0 (all liquidations had proper warning)
- **Support Tickets**: "I didn't know..." complaints → 0
- **Incorrect Leverage Usage**: Target <5% of orders

### Engagement Metrics
- **Full Preview Usage**: Measure % who expand details
- **Risk Calculator Usage**: Track adoption
- **Tutorial Completion**: % of new users who complete
- **Settings Customization**: % who change default leverage

### Feature Adoption
- **Leverage Selection**: % using inline selection vs. /leverage command
- **Stop Loss Usage**: Before/after comparison
- **Quick Actions**: % using buttons vs. typing commands
- **Buying Power Checks**: /buyingpower command usage

---

**Last Updated**: 2025-12-01
**Author**: Hyperbot Development Team + UX Review
**Status**: 📋 Enhanced with UX Best Practices
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
