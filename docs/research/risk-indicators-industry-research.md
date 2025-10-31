# Risk Indicators - Industry Research

**Research Date**: 2025-10-31
**Purpose**: Study risk indicator best practices from major exchanges for Phase 2A Risk Management System

---

## Executive Summary

Analyzed risk management UX from 4 major exchanges: **Binance**, **Bybit**, **dYdX**, and **GMX**.

**Universal Patterns Identified**:
1. **Liquidation distance as primary metric** (all 4 exchanges)
2. **5-tier color-coded risk levels** (Green → Yellow → Orange → Red → Dark Red)
3. **Real-time visual indicators** throughout interface
4. **Conservative alert thresholds** (20%, 10%, 5% common)
5. **Liquidation price shown prominently** on position cards
6. **Warnings before high-risk actions** (modal confirmations)

---

## 1. Binance (World's Largest Exchange)

### Risk Metrics

**Primary Metric**: Margin Ratio
```
Margin Ratio = Maintenance Margin / Margin Balance * 100%
```

**Risk Levels**:
- **Safe**: uniMMR > 105% (Green)
- **Warning**: uniMMR 100-105% (Yellow)
- **Alert**: uniMMR 95-100% (Orange)
- **Critical**: uniMMR < 95% (Red)
- **Liquidation**: uniMMR = 100% (triggered)

### UX Design Patterns

**Position Card**:
```
┌──────────────────────────────────────┐
│ BTC/USDT Perpetual         [🟢 Safe] │
│ Entry: $50,000  |  Mark: $52,000     │
│ Size: 0.5 BTC   |  Leverage: 5x      │
│ PnL: +$1,000 (+4.0%)                 │
│ Liq Price: $42,500                   │
│ Margin Ratio: 125%      [████░░░░]   │
└──────────────────────────────────────┘
```

**Alert System**:
- Email/SMS when Margin Ratio < 120%
- Push notification when < 110%
- Pop-up warning when < 105%

**Key Features**:
- Auto-deleverage (ADL) indicator
- Isolated margin calculator before opening position
- Simulated PnL with price scenarios

### Lessons for Hyperbot

✅ **Use progress bars** for visual risk representation
✅ **Multiple alert channels** (email, push, UI)
✅ **Pre-trade simulation** to preview liquidation price

---

## 2. Bybit (Derivatives Leader)

### Risk Metrics

**Primary Metric**: Maintenance Margin Rate (MMR)
```
MMR = Maintenance Margin / Position Margin * 100%
```

**Risk Levels**:
- **Safe**: MMR < 50% (Green)
- **Caution**: MMR 50-80% (Yellow)
- **Warning**: MMR 80-90% (Orange)
- **Urgent**: MMR 90-100% (Red, flashing)
- **Liquidation**: MMR = 100%

### UX Design Patterns

**Dashboard Widget**:
```
┌─────────────────────────────────┐
│ Account Health: 🟢 Good         │
│ ████████████████░░░░  78%       │
│                                 │
│ Total Margin:     $10,000       │
│ Used Margin:      $4,500 (45%)  │
│ Available:        $5,500        │
│                                 │
│ Open Positions: 3               │
│ ├─ BTC:  🟢 Safe (Liq: $42,500) │
│ ├─ ETH:  🟡 Caution (Liq: $...)  │
│ └─ SOL:  🟠 Warning (Liq: $...)  │
└─────────────────────────────────┘
```

**Alert Thresholds**:
- **20% from liquidation**: Yellow warning
- **10% from liquidation**: Orange urgent alert
- **5% from liquidation**: Red critical + notification

**Risk Controls**:
- Position limit enforcement based on account size
- Leverage slider with real-time liquidation price preview
- "Reduce Only" mode to prevent increasing risk

### Lessons for Hyperbot

✅ **Color badges per position** in summary view
✅ **Account-wide health score** (useful for cross margin)
✅ **Real-time liquidation price updates** as slider moves

---

## 3. dYdX (Decentralized Perpetuals)

### Risk Metrics

**Primary Metric**: Collateralization Ratio
```
Collateralization = Total Collateral / Initial Margin Requirement * 100%
```

**Risk Levels**:
- **Healthy**: > 150% (Green)
- **Moderate**: 120-150% (Yellow)
- **At Risk**: 105-120% (Orange)
- **Critical**: 100-105% (Red)
- **Liquidation**: < 100%

### UX Design Patterns

**Real-time Risk Indicator** (top-right of app):
```
┌─────────────────────────┐
│ Portfolio Health: 🟢    │
│ ███████████░░░░  145%   │
└─────────────────────────┘
```

**Position Table** (risk-sorted):
```
┏━━━━━━┳━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┳━━━━━━┓
┃ Coin ┃ Size   ┃ Entry ┃ Liq Price  ┃ Risk ┃
┡━━━━━━╇━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━╇━━━━━━┩
│ BTC  │ 0.5    │ 50000 │ 42500      │ 🟢   │
│ ETH  │ 2.0    │ 3000  │ 2700       │ 🟡   │
│ SOL  │ 100    │ 150   │ 145        │ 🔴   │ ← Highlighted
└──────┴────────┴───────┴────────────┴──────┘
```

**Pre-Trade Risk Preview**:
- Shows liquidation price BEFORE submitting order
- Simulates portfolio health after trade
- Warns if action would create HIGH risk position

### Lessons for Hyperbot

✅ **Persistent risk indicator** in top navigation
✅ **Sort by risk** in position table
✅ **Highlight critical positions** (red background)

---

## 4. GMX (Decentralized Spot/Perps)

### Risk Metrics

**Primary Metric**: Position Health
```
Health = (Collateral - Losses) / Liquidation Threshold * 100%
```

**Risk Levels**:
- **Safe**: > 200% (Green)
- **Warning**: 120-200% (Yellow)
- **Danger**: 100-120% (Red)
- **Liquidation**: < 100%

### UX Design Patterns

**Position Entry Modal**:
```
┌──────────────────────────────────────┐
│ Long BTC with 10x Leverage           │
├──────────────────────────────────────┤
│ Pay:           $1,000 USDC           │
│ Leverage:      10x                   │
│ Size:          $10,000               │
│                                      │
│ Entry Price:   ~$50,000              │
│ Liq. Price:    $45,000  (10% down)   │
│                                      │
│ ⚠️  Warning: High leverage position   │
│                                      │
│ [Cancel]              [Open Position]│
└──────────────────────────────────────┘
```

**Position Card with Risk**:
```
┌──────────────────────────────────────┐
│ BTC Long 10x              🟡 Warning │
│                                      │
│ Size:       $10,000                  │
│ Collateral: $1,000                   │
│ Entry:      $50,000                  │
│ Mark:       $51,000                  │
│ Liq Price:  $45,000 (12% down)       │
│                                      │
│ PnL: +$200 (+20%)        [Close]     │
└──────────────────────────────────────┘
```

**Key Features**:
- Liquidation price shown during order entry
- Risk level badge on position card
- Countdown timer for high-risk positions (optional)

### Lessons for Hyperbot

✅ **Show liq price DURING order creation** (preview)
✅ **Risk warnings in modals** before confirming
✅ **Simple visual**: just entry + liq price (clear)

---

## Cross-Exchange Patterns

### Color Coding Standard

| Color | Risk Level | All Exchanges Use |
|-------|-----------|------------------|
| 🟢 Green | Safe | > 30-50% from liq |
| 🟡 Yellow | Low Risk | 20-30% from liq |
| 🟠 Orange | Moderate | 10-20% from liq |
| 🔴 Red | High Risk | 5-10% from liq |
| 🔴 Dark Red/Flashing | Critical | < 5% from liq |

**Note**: For Hyperbot (crypto focus), we're using **more conservative** thresholds:
- 🟢 SAFE: > 50%
- 🟡 LOW: 30-50%
- 🟠 MODERATE: 15-30%
- 🔴 HIGH: 8-15%
- 🔴 CRITICAL: < 8%

### Alert Threshold Patterns

| Distance to Liq | Action |
|----------------|--------|
| 20% | First warning (yellow) |
| 10% | Urgent alert (orange) |
| 5% | Critical alert (red) + notification |
| 2% | Force close suggestion |

### UI Component Patterns

**1. Risk Badge**:
```html
<span class="risk-badge risk-safe">🟢 SAFE</span>
<span class="risk-badge risk-low">🟡 LOW</span>
<span class="risk-badge risk-moderate">🟠 MODERATE</span>
<span class="risk-badge risk-high">🔴 HIGH</span>
<span class="risk-badge risk-critical">🔴 CRITICAL</span>
```

**2. Progress Bar**:
```html
<div class="health-bar">
  <div class="health-fill risk-safe" style="width: 85%"></div>
  <span class="health-label">85% Health</span>
</div>
```

**3. Position Card Layout**:
```
[Coin] [Side] [Leverage]      [Risk Badge]
Entry: $XXX    Current: $XXX
Size: X.XXX    Value: $XXX
PnL: $XXX (±X.X%)
Liq Price: $XXX (±X.X%)       [Close Button]
```

---

## Recommendations for Hyperbot Phase 2A

### 1. Risk Calculation
- ✅ Use liquidation distance as primary metric (simple, universal)
- ✅ Derive health_score from risk_level (no complex composite)
- ✅ Conservative thresholds: 50%/30%/15%/8%/0%

### 2. Visual Design
- ✅ Color-coded badges: Green/Yellow/Orange/Red/Dark Red
- ✅ Progress bar for health score (0-100)
- ✅ Liquidation price prominent on position cards
- ✅ Leverage shown next to coin symbol

### 3. User Warnings
- ✅ Modal confirmation before HIGH/CRITICAL risk trades
- ✅ Disable rebalance button if would create CRITICAL risk
- ✅ Show risk impact in rebalance preview

### 4. Real-time Updates
- ✅ HTMX auto-refresh every 10s (current positions table)
- ✅ Update risk badges on each refresh
- ✅ Highlight positions that changed risk level

### 5. Rebalance-Specific
- ✅ Preview showing BEFORE/AFTER risk levels
- ✅ Block execution if any position would be CRITICAL
- ✅ Set leverage before opening positions
- ✅ Calculate estimated liquidation price for new positions

---

## Implementation Priority

**Phase 2A.1** (Risk Calculator):
1. Calculate liquidation distance (%)
2. Determine risk level (SAFE/LOW/MODERATE/HIGH/CRITICAL)
3. Derive health_score from risk_level (90-100/70-89/50-69/25-49/0-24)
4. Generate warnings list

**Phase 2A.4** (UI):
1. Add risk badge component (color-coded)
2. Show liquidation price on position cards
3. Add health score progress bar
4. Rebalance preview with risk impact
5. Warning modals for HIGH/CRITICAL

---

## References

- **Binance Futures**: https://www.binance.com/en/futures/
- **Bybit Derivatives**: https://www.bybit.com/
- **dYdX Perpetuals**: https://dydx.exchange/
- **GMX**: https://gmx.io/

---

## Key Takeaways

1. ✅ **Liquidation distance is universal** - All exchanges use it
2. ✅ **5-tier color system is standard** - Users expect it
3. ✅ **Show liq price prominently** - On cards, in modals, everywhere
4. ✅ **Conservative thresholds for crypto** - 50% buffer is reasonable
5. ✅ **Warnings before risky actions** - Prevent user mistakes
6. ✅ **Real-time visual feedback** - Progress bars, colors, badges
7. ✅ **Simplicity wins** - Don't overcomplicate with too many metrics
