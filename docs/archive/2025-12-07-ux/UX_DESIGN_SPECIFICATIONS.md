# UX Design Specifications: Telegram Trading Bot

**Document Type**: Design Handoff
**From**: UX Design Team
**To**: Development Team
**Date**: 2025-12-01
**Version**: 1.0

---

## 📐 Document Purpose

This document provides **pixel-perfect** specifications for implementing Telegram bot interactions. It bridges the gap between UX design and code implementation.

**What developers will find here**:
- ✅ Exact text formatting (bold, italic, spacing)
- ✅ Emoji usage and placement
- ✅ Button layouts and labels
- ✅ Information hierarchy
- ✅ Responsive behavior
- ✅ Animation/transition notes
- ✅ Edge case handling

---

## 🎨 Design System Foundation

### Typography Scale

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HEADING 1 (Main titles)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format: **TITLE TEXT**
Usage: Section headers, main titles
Example: **💰 CAPITAL IMPACT**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Heading 2 (Subsections)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format: **Text**
Usage: Subsection titles
Example: **Order Preview**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Body Text (Regular)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format: Plain text
Usage: Labels, descriptions
Example: Margin Required: $200.00

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Emphasis (Important values)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format: **Value** or _Text_
Usage: Highlight key numbers
Example: PnL: **+$123.45 (+5.2%)**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Code/Technical (Inline)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format: `text`
Usage: Order IDs, addresses
Example: Order ID: `#12345678`
```

### Spacing Rules

```
┌─────────────────────────────────┐
│ Message Title                   │  ← No spacing above
│                                 │  ← 1 blank line
│ Content section                 │
│ Line 1                          │  ← No spacing between lines
│ Line 2                          │
│                                 │  ← 1 blank line before separator
│ ━━━━━━━━━━━━━━━━━               │  ← Separator
│ **SECTION HEADER**              │
│ ━━━━━━━━━━━━━━━━━               │  ← Separator
│ Field: Value                    │  ← No spacing between fields
│ Field: Value                    │
│                                 │  ← 1 blank line between sections
│ ━━━━━━━━━━━━━━━━━               │
│ **NEXT SECTION**                │
│ ━━━━━━━━━━━━━━━━━               │
│ Content                         │
└─────────────────────────────────┘
```

**Rules**:
- Use `\n` for single line break
- Use `\n\n` for blank line (section separator)
- Separator = `━━━━━━━━━━━━━━━━━` (17 characters)
- Always blank line before buttons

### Color System (via Emojis)

Since Telegram doesn't support text colors, we use emojis as visual indicators:

```
🟢 GREEN - Positive, Safe, Long positions
   - PnL positive
   - Risk LOW
   - Long positions
   - Success states

🔴 RED - Negative, Danger, Short positions
   - PnL negative
   - Risk CRITICAL
   - Short positions
   - Error states

🟡 YELLOW - Warning, Moderate risk
   - Risk MODERATE
   - Caution states
   - Important notices

🟠 ORANGE - High risk, Urgent
   - Risk HIGH
   - Needs attention

⚪ WHITE/GRAY - Neutral
   - Zero PnL
   - Informational
   - Conservative options

✨ SPARKLE - Recommended
   - Suggested options
   - Highlighted choices

⚡ BOLT - Leverage indicator
   - Shows leverage level
   - Power/multiplier concept

💀 SKULL - Extreme danger
   - Liquidation
   - Extreme risk
   - Critical warnings
```

---

## 📱 Component Specifications

### SPEC-001: Quick Preview

**Purpose**: Mobile-optimized order preview (default view)
**Max Height**: 10 lines (fits on small screens)
**Pattern**: Always same structure

```
┌─────────────────────────────────────┐
│ 📋 **Order Preview**                │  Line 1: Title
│                                     │  Line 2: Blank
│ 💰 BTC BUY 🟢: $1,000 @ market     │  Line 3: Order summary
│ ⚡ Leverage: 5x                     │  Line 4: Leverage
│ 📊 Margin: $200 / $5,200 available │  Line 5: Capital
│ 🎯 Liquidation: $78,800 (-20%)     │  Line 6: Risk
│ ⚠️ Risk: MODERATE 🟡               │  Line 7: Risk level
│                                     │  Line 8: Blank
│ [✅ Buy $1,000 BTC] ─────────────  │  Button 1: Action
│ [📊 Full Details]  ────────────────│  Button 2: Expand
│ [❌ Cancel] ───────────────────────│  Button 3: Cancel
└─────────────────────────────────────┘
```

**Implementation**:
```python
# Exact format string
message = f"""📋 **Order Preview**

💰 {coin} {side} {side_emoji}: {format_currency(amount_usd)} @ market
⚡ Leverage: {leverage}x
📊 Margin: {format_currency(margin_req)} / {format_currency(margin_avail)} available
🎯 Liquidation: {format_currency(liq_price)} ({format_percentage(liq_dist, show_sign=False)} away)
⚠️ Risk: {risk_level} {risk_emoji}"""

# Button structure (3 buttons, full width each)
buttons = [
    [InlineKeyboardButton(f"✅ {side.title()} {format_currency(amount_usd)} {coin}", callback_data=confirm_cb)],
    [InlineKeyboardButton("📊 Full Details", callback_data=details_cb)],
    [InlineKeyboardButton("❌ Cancel", callback_data=cancel_cb)]
]
```

**Variations**:
- For limit orders: Replace "@ market" with "@ $96,530 (2% below)"
- For reduce-only: Add line: "🔒 Reduce Only: Yes"

**Mobile Testing**:
- ✅ Fits on iPhone SE (4.7") without scrolling
- ✅ All buttons thumb-reachable
- ✅ Text readable at default size

---

### SPEC-002: Full Preview

**Purpose**: Comprehensive order analysis (optional view)
**Max Height**: Unlimited (user requested details)
**Pattern**: Structured with cards

```
┌─────────────────────────────────────────────┐
│ 📋 **Complete Order Analysis**              │
│                                             │
│ Coin: BTC                                   │
│ Side: BUY 🟢                                │
│ Amount: $1,000                              │
│ Leverage: 5x ⚡                             │
│                                             │
│ ━━━━━━━━━━━━━━━━━                           │
│ **💰 CAPITAL IMPACT**                       │
│ ━━━━━━━━━━━━━━━━━                           │
│ Margin Required: $200.00                    │
│ Margin Available: $5,200.00                 │
│ Buying Power Used: 3.8%                     │
│                                             │
│ ━━━━━━━━━━━━━━━━━                           │
│ **⚠️ RISK ASSESSMENT**                      │
│ ━━━━━━━━━━━━━━━━━                           │
│ Entry Price: ~$98,500 (market)              │
│ Est. Liquidation: $78,800                   │
│ Safety Distance: 20.0% drop                 │
│ Risk Level: MODERATE 🟡 [?]                 │
│                                             │
│ Position Size: 0.01015 BTC                  │
│ Total Exposure: $1,000                      │
│                                             │
│ ✅ You have sufficient margin                │
│ ✅ Leverage will be set to 5x               │
│                                             │
│ [✅ Buy $1,000 BTC] ───────────────────     │
│ [⚙️ Change Leverage] ──────────────────     │
│ [❌ Cancel] ───────────────────────────     │
└─────────────────────────────────────────────┘
```

**Implementation**:
```python
# Build with InfoCard components
from src.bot.components.cards import InfoCard, build_capital_impact_card, build_risk_assessment_card

# Header
header = f"""📋 **Complete Order Analysis**

Coin: {coin}
Side: {side} {side_emoji}
Amount: {format_currency(amount_usd)}
Leverage: {leverage}x ⚡
"""

# Cards
capital_card = build_capital_impact_card(margin_req, margin_avail, bp_used_pct)
risk_card = build_risk_assessment_card(entry_price, liq_price, liq_dist, leverage)

# Footer
footer = f"""
Position Size: {format_coin_size(size_coin, coin)}
Total Exposure: {format_currency(amount_usd)}

✅ You have sufficient margin
✅ Leverage will be set to {leverage}x"""

# Combine
message = "\n\n".join([header, capital_card.render(), risk_card.render(), footer])
```

**Interactive Elements**:
- `[?]` button next to "Risk Level" opens explanation modal
- All expandable sections use consistent `[?]` indicator

---

### SPEC-003: Leverage Selector

**Purpose**: Context-aware leverage selection
**Pattern**: Show buying power at each level with recommendations

```
┌─────────────────────────────────────────────┐
│ ⚡ **Select Leverage for $1,000 BTC**       │
│                                             │
│ Your order: $1,000                          │
│ Available: $5,200                           │
│                                             │
│ 1x  → $5,200 max ⚪ Conservative            │
│ 3x  → $15,600 max ✨ Good for this size     │
│ 5x  → $26,000 max 🟡 Higher risk            │
│ 10x → $52,000 max 🔴 Risky                  │
│ 20x → $104,000 max 💀 Extreme risk          │
│                                             │
│ 💡 For $1,000 orders, 3-5x balances         │
│    opportunity and safety.                  │
│                                             │
│ [1x] [3x ✨] [5x] [10x] ──────────────────  │
│ [Custom Leverage] ─────────────────────     │
│ [🔙 Back] [❌ Cancel] ──────────────────     │
└─────────────────────────────────────────────┘
```

**Implementation**:
```python
# Calculate recommendations
def get_leverage_recommendation(amount_usd: float, account_value: float) -> int:
    """
    Context-aware leverage recommendation.

    Rules:
    - Order < 20% of account → 3-5x
    - Order 20-50% of account → 1-3x
    - Order > 50% of account → 1x only
    """
    ratio = amount_usd / account_value

    if ratio < 0.2:
        return 3  # or 5x
    elif ratio < 0.5:
        return 2  # or 3x
    else:
        return 1

# Build message
recommended_lev = get_leverage_recommendation(amount_usd, account_value)

message = f"""⚡ **Select Leverage for {format_currency(amount_usd)} {coin}**

Your order: {format_currency(amount_usd)}
Available: {format_currency(account_value)}

1x  → {format_currency(account_value)} max ⚪ Conservative
3x  → {format_currency(account_value * 3)} max {"✨ Good for this size" if recommended_lev == 3 else ""}
5x  → {format_currency(account_value * 5)} max 🟡 Higher risk
10x → {format_currency(account_value * 10)} max 🔴 Risky
20x → {format_currency(account_value * 20)} max 💀 Extreme risk

💡 For {format_currency(amount_usd)} orders, {recommended_lev}-{recommended_lev+2}x balances
   opportunity and safety."""

# Buttons: Row of 4 + Custom + Back/Cancel
buttons = [
    [
        InlineKeyboardButton("1x", callback_data="lev:1"),
        InlineKeyboardButton("3x ✨", callback_data="lev:3") if recommended_lev == 3 else InlineKeyboardButton("3x", callback_data="lev:3"),
        InlineKeyboardButton("5x", callback_data="lev:5"),
        InlineKeyboardButton("10x", callback_data="lev:10")
    ],
    [InlineKeyboardButton("Custom Leverage", callback_data="lev:custom")],
    [
        InlineKeyboardButton("🔙 Back", callback_data="back"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel")
    ]
]
```

**Design Notes**:
- Recommended option gets ✨ emoji
- Labels explain WHY (not just numbers)
- Always show buying power (helps user decide)
- Educational tip at bottom (non-intrusive)

---

### SPEC-004: Position List (Risk-Sorted)

**Purpose**: Show all positions with risk prioritization
**Pattern**: Group by urgency, show key metrics inline

```
┌─────────────────────────────────────────────┐
│ 📊 **Open Positions** (3)                   │
│                                             │
│ Total Value: $12,450                        │
│ Total PnL: 🟢 +$523 (+4.2%)                 │
│ Margin Used: 62%                            │
│                                             │
│ Sort: [⚠️ Risk] [💰 Size] [📈 PnL] [🔤 Name] │
│                                             │
│ ━━━━━━━━━━━━━━━━━                           │
│ ⚠️ **NEEDS ATTENTION** (1)                  │
│ ━━━━━━━━━━━━━━━━━                           │
│ 🔴 **ETH SHORT** • 🔴 -$87 (8.7%)          │
│    Liq: 8% away ⚠️ | No SL ❌               │
│    [📊 Details] [🛡️ Set SL] [❌ Close]      │
│                                             │
│ ━━━━━━━━━━━━━━━━━                           │
│ ✅ **PROTECTED** (2)                        │
│ ━━━━━━━━━━━━━━━━━                           │
│ 🟢 **BTC LONG** • 🟢 +$175 (17.5%)         │
│    Liq: 22.7% away 🟢 | SL ✅              │
│    [📊 Details]                             │
│                                             │
│ 🟢 **SOL LONG** • 🟢 +$365 (50.3%)         │
│    Liq: 36.5% away 🟢 | SL ✅              │
│    [📊 Details]                             │
│                                             │
│ ━━━━━━━━━━━━━━━━━                           │
│ ⚠️ **Risk Summary:**                        │
│ • 1 position without stop loss              │
│ • 1 position with HIGH risk                 │
│                                             │
│ [🛡️ Set All SL] [📊 Risk Analysis] [🔙]    │
└─────────────────────────────────────────────┘
```

**Implementation**:
```python
# Sort positions by risk
positions.sort(key=lambda p: p['liquidation_distance_pct'])

# Group
high_risk = [p for p in positions if p['liquidation_distance_pct'] < 15 or not p['has_stop_loss']]
protected = [p for p in positions if p not in high_risk]

# Build header
header = f"""📊 **Open Positions** ({len(positions)})

Total Value: {format_currency(total_value)}
Total PnL: {pnl_emoji} {pnl_str}
Margin Used: {margin_used_pct:.0f}%

Sort: [⚠️ Risk] [💰 Size] [📈 PnL] [🔤 Name]
"""

# Build high risk section
high_risk_section = []
if high_risk:
    high_risk_section.append("━━━━━━━━━━━━━━━━━")
    high_risk_section.append(f"⚠️ **NEEDS ATTENTION** ({len(high_risk)})")
    high_risk_section.append("━━━━━━━━━━━━━━━━━")

    for pos in high_risk:
        high_risk_section.append(format_position_item(pos, show_actions=True))

# Build protected section
protected_section = []
if protected:
    protected_section.append("━━━━━━━━━━━━━━━━━")
    protected_section.append(f"✅ **PROTECTED** ({len(protected)})")
    protected_section.append("━━━━━━━━━━━━━━━━━")

    for pos in protected:
        protected_section.append(format_position_item(pos, show_actions=False))

# Build footer
footer = []
if high_risk:
    no_sl_count = sum(1 for p in positions if not p['has_stop_loss'])
    high_risk_count = sum(1 for p in positions if p['liquidation_distance_pct'] < 15)

    footer.append("━━━━━━━━━━━━━━━━━")
    footer.append("⚠️ **Risk Summary:**")
    if no_sl_count > 0:
        footer.append(f"• {no_sl_count} position(s) without stop loss")
    if high_risk_count > 0:
        footer.append(f"• {high_risk_count} position(s) with HIGH risk")

# Combine
message = "\n".join([header] + high_risk_section + [""] + protected_section + [""] + footer)
```

**Design Decisions**:
- **Risk-sorted by default** because safety is priority #1
- **Grouped into 2 tiers** to reduce cognitive load
- **Quick actions only for risky positions** to focus attention
- **Inline metrics** (Liq %, SL status) for scannability
- **Risk summary footer** provides actionable overview

---

### SPEC-005: Loading States

**Purpose**: Show progress during async operations
**Pattern**: Consistent spinner emoji + clear action

```
┌─────────────────────────────────────┐
│ ⏳ Calculating preview...           │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ⏳ Fetching current BTC price...    │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ⏳ Placing order...                 │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ⏳ Setting leverage to 5x...        │
└─────────────────────────────────────┘
```

**Implementation**:
```python
# Standard loading messages (use constants)
LOADING_MESSAGES = {
    "preview": "⏳ Calculating preview...",
    "price": "⏳ Fetching current {coin} price...",
    "order": "⏳ Placing order...",
    "leverage": "⏳ Setting leverage to {leverage}x...",
    "position": "⏳ Fetching {coin} position...",
    "account": "⏳ Loading account data...",
    "close": "⏳ Closing {coin} position...",
}

# Usage
async def show_loading(update: Update, action: str, **kwargs):
    """Show loading state."""
    message = LOADING_MESSAGES[action].format(**kwargs)

    if update.callback_query:
        await update.callback_query.edit_message_text(message)
    else:
        await update.message.reply_text(message)
```

**Design Notes**:
- Always use ⏳ emoji (hourglass)
- Always use "..." suffix
- Be specific about what's loading
- Replace immediately when done (don't leave hanging)
- Maximum duration: 5 seconds (show error after)

---

### SPEC-006: Success Messages with Next Actions

**Purpose**: Confirm completion and guide next steps
**Pattern**: Success message + suggestions + buttons

```
┌─────────────────────────────────────────────┐
│ ✅ **Order Executed!**                      │
│                                             │
│ ⚡ Leverage set to 5x for BTC               │
│ 📈 Market BUY executed                      │
│    Size: 0.01015 BTC                        │
│    Avg Fill: $98,523                        │
│    Value: $1,000.00                         │
│                                             │
│ 💰 New Position:                            │
│    Margin Used: $200                        │
│    Liquidation: $78,800 (-20%)              │
│                                             │
│ ━━━━━━━━━━━━━━━━━                           │
│ **What's next?**                            │
│                                             │
│ [🛡️ Set Stop Loss] ────────────────────     │
│ [📊 View Position] ─────────────────────     │
│ [🔙 Main Menu] ─────────────────────────     │
└─────────────────────────────────────────────┘
```

**Implementation**:
```python
# Success message structure
def build_order_success_message(
    coin: str,
    side: str,
    size_coin: float,
    avg_fill: float,
    value_usd: float,
    leverage: int,
    margin_used: float,
    liquidation_price: float,
    liquidation_distance_pct: float
) -> str:
    """Build standardized success message."""

    return f"""✅ **Order Executed!**

⚡ Leverage set to {leverage}x for {coin}
📈 Market {side} executed
   Size: {format_coin_size(size_coin, coin)}
   Avg Fill: {format_currency(avg_fill)}
   Value: {format_currency(value_usd)}

💰 New Position:
   Margin Used: {format_currency(margin_used)}
   Liquidation: {format_currency(liquidation_price)} ({format_percentage(liquidation_distance_pct, show_sign=False)} away)

━━━━━━━━━━━━━━━━━
**What's next?**"""

# Buttons: Context-aware suggestions
buttons = [
    [InlineKeyboardButton("🛡️ Set Stop Loss", callback_data=f"set_sl:{coin}")],
    [InlineKeyboardButton("📊 View Position", callback_data=f"view_pos:{coin}")],
    [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
]
```

**Design Notes**:
- Always start with ✅ emoji
- Show key execution details (fill price, size)
- Show immediate risk (liquidation)
- Suggest 2-3 logical next actions
- Always include "Main Menu" escape

---

### SPEC-007: Error Messages

**Purpose**: Explain errors and provide solutions
**Pattern**: Error + Explanation + Options

```
┌─────────────────────────────────────────────┐
│ ❌ **Insufficient Margin**                  │
│                                             │
│ You need $500 but only have $200.          │
│                                             │
│ **Options:**                                │
│ • Reduce order size                         │
│ • Lower leverage (currently 10x)            │
│ • Deposit more funds                        │
│                                             │
│ [📉 Reduce Order Size] ─────────────────     │
│ [⚡ Lower Leverage] ─────────────────────     │
│ [❌ Cancel] ────────────────────────────     │
└─────────────────────────────────────────────┘
```

**Implementation**:
```python
# Error message templates
ERROR_TEMPLATES = {
    "insufficient_margin": {
        "title": "❌ **Insufficient Margin**",
        "message": "You need {required} but only have {available}.",
        "options": [
            "• Reduce order size",
            "• Lower leverage (currently {leverage}x)",
            "• Deposit more funds"
        ],
        "buttons": [
            ("📉 Reduce Order Size", "reduce_size"),
            ("⚡ Lower Leverage", "change_leverage"),
            ("❌ Cancel", "cancel")
        ]
    },
    "position_not_found": {
        "title": "❌ **Position Not Found**",
        "message": "No open {coin} position exists.",
        "options": [
            "• Place a new order",
            "• View all positions"
        ],
        "buttons": [
            ("📈 Place Order", f"order:{coin}"),
            ("📊 View Positions", "menu_positions"),
            ("❌ Cancel", "cancel")
        ]
    },
    # ... more error types
}

def build_error_message(error_type: str, **kwargs) -> tuple[str, list]:
    """Build standardized error message with buttons."""
    template = ERROR_TEMPLATES[error_type]

    message = f"""{template['title']}

{template['message'].format(**kwargs)}

**Options:**
{chr(10).join(opt.format(**kwargs) for opt in template['options'])}"""

    buttons = [
        [InlineKeyboardButton(label, callback_data=cb.format(**kwargs) if isinstance(cb, str) else cb)]
        for label, cb in template['buttons']
    ]

    return message, buttons
```

**Design Notes**:
- Always use ❌ emoji for errors
- Be specific about what went wrong
- Provide actionable solutions
- Never dead-end (always give options)
- Use friendly tone (not accusatory)

---

## 📏 Button Layout Specifications

### Single Action (Full Width)

```
┌─────────────────────────────────────┐
│ [✅ Buy $1,000 BTC] ───────────────  │  ← 100% width
└─────────────────────────────────────┘
```

### Two Actions (Side by Side)

```
┌─────────────────────────────────────┐
│ [✅ Confirm] [❌ Cancel] ──────────  │  ← 50% / 50%
└─────────────────────────────────────┘
```

### Three Actions (Stacked)

```
┌─────────────────────────────────────┐
│ [✅ Primary Action] ──────────────── │  ← 100% width
│ [📊 Secondary Action] ────────────── │  ← 100% width
│ [❌ Cancel] ───────────────────────  │  ← 100% width
└─────────────────────────────────────┘
```

### Four Actions (2x2 Grid)

```
┌─────────────────────────────────────┐
│ [1x] [3x ✨] [5x] [10x] ──────────  │  ← 25% each
│ [Custom Leverage] ─────────────────  │  ← 100% width
│ [🔙 Back] [❌ Cancel] ─────────────  │  ← 50% / 50%
└─────────────────────────────────────┘
```

**Rules**:
- Max 4 buttons per row
- Primary action always first
- Destructive actions (Close, Cancel) always last
- Navigation (Back) always bottom-left
- Never more than 5 rows of buttons

---

## 🎬 Animation & Transitions

### Message Updates

```python
# WRONG: Jarring replacement
await query.edit_message_text("Step 2")

# RIGHT: Show loading transition
await query.edit_message_text("⏳ Loading...")
await asyncio.sleep(0.1)  # Brief pause
result = await fetch_data()
await query.edit_message_text(result)
```

### Multi-Step Wizards

```
Step 1/5: Select Coin    ← Always show progress
Step 2/5: Buy or Sell
Step 3/5: Enter Amount
Step 4/5: Select Leverage
Step 5/5: Preview & Confirm
```

**Implementation**:
```python
def build_step_header(current: int, total: int, title: str) -> str:
    """Build consistent step header."""
    return f"Step {current}/{total}: {title}"

# Usage
message = f"""📊 **Scale Order Wizard**

{build_step_header(3, 5, "Enter Amount")}

..."""
```

---

## 🧪 Edge Cases & Error States

### Empty States

```
┌─────────────────────────────────────┐
│ 📭 **No Open Positions**            │
│                                     │
│ You don't have any open positions.  │
│                                     │
│ Ready to start trading?             │
│                                     │
│ [📈 Place Order] ──────────────────  │
│ [🔙 Main Menu] ────────────────────  │
└─────────────────────────────────────┘
```

### Network Errors

```
┌─────────────────────────────────────┐
│ ⚠️ **Connection Issue**             │
│                                     │
│ Unable to reach Hyperliquid API.    │
│                                     │
│ This is usually temporary. Try again│
│ in a moment.                        │
│                                     │
│ [🔄 Retry] ────────────────────────  │
│ [🔙 Main Menu] ────────────────────  │
└─────────────────────────────────────┘
```

### Rate Limiting

```
┌─────────────────────────────────────┐
│ ⏸️ **Please Wait**                  │
│                                     │
│ Too many requests. Please wait 5s.  │
│                                     │
│ [⏳ Waiting...] ───────────────────  │  ← Disabled button
└─────────────────────────────────────┘
```

---

## ✅ Design Review Checklist

Before submitting implementation for review:

### Content
- [ ] All text uses proper formatting (bold, italic, code)
- [ ] Emojis used consistently (per design system)
- [ ] Currency values use `format_currency()`
- [ ] Percentages use `format_percentage()`
- [ ] Spacing follows rules (blank lines, separators)

### Buttons
- [ ] Action-oriented labels (not generic "Confirm")
- [ ] Primary action is first and obvious
- [ ] Cancel/Back always present
- [ ] Max 4 buttons per row
- [ ] Emoji used appropriately

### Mobile
- [ ] Quick preview fits on small screen (<10 lines)
- [ ] Text readable without zooming
- [ ] Buttons thumb-reachable
- [ ] No horizontal scrolling

### UX Flow
- [ ] Loading state shown for async operations
- [ ] Success includes "What's next?"
- [ ] Errors include solutions
- [ ] No dead-ends (always have exit)
- [ ] Progress indicated in multi-step flows

### Consistency
- [ ] Matches existing patterns in codebase
- [ ] Uses component library (not custom formatting)
- [ ] Risk colors correct (🟢🟡🟠🔴)
- [ ] Follows separator pattern

---

## 📞 Designer-Developer Communication

### When to Ask UX Team

1. **New component needed** that's not in library
2. **Edge case** not covered in specs
3. **Accessibility concern** for specific user group
4. **Technical limitation** prevents exact spec
5. **Localization** question (emoji interpretation varies)

### How to Report Issues

```
Issue: Leverage selector doesn't fit on iPhone SE
Screen: Leverage selection step
Expected: 10 lines max
Actual: 12 lines (requires scroll)
Proposed fix: Remove educational tip or show only 3 leverage options
```

### Feedback Format

```
✅ WORKING WELL:
- Quick previews load fast
- Risk colors are clear
- Button labels are specific

⚠️ NEEDS ADJUSTMENT:
- Full preview too long on mobile (15 lines)
- Error messages don't suggest solutions
- Loading states missing on position view

🎯 SUGGESTED IMPROVEMENTS:
- Add collapsible sections for full preview
- Use error templates from SPEC-007
- Add LoadingMessage.show() calls
```

---

**Last Updated**: 2025-12-01
**Design Version**: 1.0
**Maintained By**: Hyperbot UX Team
**Implementation Status**: Ready for Development

---

## Appendix: Complete Message Examples

### A1: Market Order - Complete Flow

```
# Step 1: Coin Selection
💰 **Market Order**

Step 1/5: Select coin to trade

Choose from popular coins or enter custom symbol:

[BTC] [ETH] [SOL] [AVAX]
[Custom Symbol]
[🔙 Main Menu]

# Step 2: Buy/Sell
💰 **BTC Market Order**

Step 2/5: Buy or Sell?

[🟢 Buy] [🔴 Sell]
[🔙 Back] [❌ Cancel]

# Step 3: Amount
💰 **BTC BUY**

Step 3/5: Enter amount in USD

Choose a preset or enter custom:

[$100] [$500] [$1,000]
[Custom Amount]
[🔙 Back] [❌ Cancel]

# Step 4: Leverage
⚡ **Select Leverage for $1,000 BTC**

Your order: $1,000
Available: $5,200

1x  → $5,200 max ⚪ Conservative
3x  → $15,600 max ✨ Good for this size
5x  → $26,000 max 🟡 Higher risk
10x → $52,000 max 🔴 Risky
20x → $104,000 max 💀 Extreme risk

💡 For $1,000 orders, 3-5x balances
   opportunity and safety.

[1x] [3x ✨] [5x] [10x]
[Custom Leverage]
[🔙 Back] [❌ Cancel]

# Step 5: Preview (Quick)
📋 **Order Preview**

💰 BTC BUY 🟢: $1,000 @ market
⚡ Leverage: 5x
📊 Margin: $200 / $5,200 available
🎯 Liquidation: $78,800 (-20%)
⚠️ Risk: MODERATE 🟡

[✅ Buy $1,000 BTC]
[📊 Full Details]
[❌ Cancel]

# Step 6: Execution
⏳ Placing order...

# Step 7: Success
✅ **Order Executed!**

⚡ Leverage set to 5x for BTC
📈 Market BUY executed
   Size: 0.01015 BTC
   Avg Fill: $98,523
   Value: $1,000.00

💰 New Position:
   Margin Used: $200
   Liquidation: $78,800 (-20%)

━━━━━━━━━━━━━━━━━
**What's next?**

[🛡️ Set Stop Loss]
[📊 View Position]
[🔙 Main Menu]
```

This completes the design handoff specification! 🎨
