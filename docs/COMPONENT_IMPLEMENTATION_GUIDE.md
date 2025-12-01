# Component Implementation Guide for Developers

**Quick Start**: How to build Telegram bot interactions using the UX Component Library
**Audience**: Backend developers implementing bot handlers
**Prerequisites**: Read [TELEGRAM_UX_COMPONENT_LIBRARY.md](./TELEGRAM_UX_COMPONENT_LIBRARY.md)

---

## 🎯 Component Usage Patterns

### Pattern 1: Simple Information Display

**Use Case**: Show account info, position details, etc.

```python
from src.bot.components.cards import InfoCard
from src.bot.components.formatters import format_currency, format_percentage

async def show_account_info(update: Update):
    """Display account information using InfoCard."""

    # Fetch data
    account_value = 5200.00
    margin_used = 3200.00
    margin_free = 2000.00

    # Build card
    card = InfoCard("Account Summary", "💰")
    card.add_field("Total Value", format_currency(account_value))
    card.add_field("Margin Used", format_currency(margin_used))
    card.add_field("Margin Free", format_currency(margin_free))
    card.add_field("Usage", format_percentage(margin_used / account_value * 100))

    # Render and send
    message = card.render()
    await update.message.reply_text(message, parse_mode="Markdown")
```

**Output**:
```
━━━━━━━━━━━━━━━━━
💰 Account Summary
━━━━━━━━━━━━━━━━━
Total Value: $5,200.00
Margin Used: $3,200.00
Margin Free: $2,000.00
Usage: 61.5%
```

---

### Pattern 2: Action with Confirmation

**Use Case**: Place order, close position, cancel orders

```python
from src.bot.components.buttons import ButtonBuilder, build_confirm_action_buttons
from src.bot.components.loading import LoadingMessage

async def confirm_close_position(update: Update, coin: str):
    """Show confirmation before closing position."""

    # Show loading
    await LoadingMessage.show(update, "position")

    # Fetch position
    position = get_position(coin)  # your service call

    # Build confirmation message
    message = f"""
🎯 **Close Position Confirmation**

Coin: {coin}
Side: {"LONG 🟢" if position['size'] > 0 else "SHORT 🔴"}
Size: {format_coin_size(abs(position['size']), coin)}
Current PnL: {format_pnl(position['pnl'], position['pnl_pct'])[0]}

⚠️ This will place a market order to close.
"""

    # Build buttons
    buttons = build_confirm_action_buttons(
        f"Close {format_coin_size(abs(position['size']), coin)} Position",
        f"execute_close:{coin}",
        cancel_callback="menu_positions"
    )

    # Send
    query = update.callback_query
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=buttons)
```

---

### Pattern 3: Two-Tier Preview

**Use Case**: Order preview with optional details

```python
from src.bot.components.preview import PreviewBuilder, PreviewData
from src.bot.components.buttons import build_confirm_action_buttons

async def show_order_preview(
    update: Update,
    coin: str,
    side: str,
    amount_usd: float,
    leverage: int,
    show_full: bool = False
):
    """Show order preview (quick or full)."""

    # Calculate preview data
    preview_data = await calculate_preview(coin, side, amount_usd, leverage)

    # Build message
    if show_full:
        message = PreviewBuilder.build_full_preview(preview_data)
        details_callback = None  # Already showing full
    else:
        message = PreviewBuilder.build_quick_preview(preview_data)
        details_callback = f"preview_full:{coin}:{amount_usd}:{leverage}"

    # Build buttons
    buttons = build_confirm_action_buttons(
        f"{side.title()} {format_currency(amount_usd)} {coin}",
        f"confirm_order:{coin}:{amount_usd}:{leverage}",
        details_callback=details_callback
    )

    # Send
    query = update.callback_query
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=buttons)


async def calculate_preview(coin, side, amount_usd, leverage) -> PreviewData:
    """Calculate preview data from services."""

    # Get current price
    price = market_data_service.get_current_price(coin)

    # Calculate margin
    margin_required = amount_usd / leverage

    # Get account
    account = account_service.get_account_value()
    margin_available = account['margin_free']

    # Calculate liquidation
    liquidation_price = calculate_liquidation_price(price, leverage, side)
    liquidation_distance = abs((price - liquidation_price) / price * 100)

    return PreviewData(
        coin=coin,
        side=side,
        amount_usd=amount_usd,
        leverage=leverage,
        entry_price=price,
        margin_required=margin_required,
        margin_available=margin_available,
        buying_power_used_pct=(margin_required / margin_available * 100),
        liquidation_price=liquidation_price,
        liquidation_distance_pct=liquidation_distance,
        size_coin=amount_usd / price
    )
```

---

### Pattern 4: Sorted/Grouped Lists

**Use Case**: Positions, orders, any list needing organization

```python
from src.bot.components.lists import SortableList, SortOption, build_position_list
from src.bot.components.buttons import ButtonBuilder

async def show_positions(update: Update, sort_by: SortOption = SortOption.RISK):
    """Show positions with sorting."""

    # Fetch positions
    positions = position_service.list_positions()

    # Add calculated fields
    for pos in positions:
        pos['liquidation_distance_pct'] = calculate_liq_distance(pos)
        pos['has_stop_loss'] = has_stop_loss_order(pos['coin'])
        pos['pnl_pct'] = pos['unrealized_pnl'] / pos['margin_used'] * 100

    # Build list
    message = build_position_list(positions, sort_by=sort_by)

    # Build sort buttons
    sort_buttons = ButtonBuilder()\
        .add_row(
            ("⚠️ Risk", f"sort_pos:risk", ""),
            ("💰 Size", f"sort_pos:size", ""),
            ("📈 PnL", f"sort_pos:pnl", "")
        )\
        .add_secondary("Main Menu", "menu_main", "🔙")\
        .build()

    # Send
    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=sort_buttons)
```

---

### Pattern 5: Multi-Step Wizard (Using Orchestrator)

**Use Case**: Complex flows like order placement

```python
from src.bot.components.flows.order_flow import OrderFlowOrchestrator
from telegram.ext import ConversationHandler

# State constants
COIN, SIDE, AMOUNT, LEVERAGE, PREVIEW = range(5)

# Initialize orchestrator
order_flow = OrderFlowOrchestrator()

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start order wizard."""
    await order_flow.step_1_coin_selection(update, context)
    return COIN

async def coin_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle coin selection."""
    query = update.callback_query
    coin = query.data.split(":")[1]

    await order_flow.step_2_side_selection(update, context, coin)
    return SIDE

async def side_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle side selection."""
    query = update.callback_query
    side = query.data.split(":")[1]

    await order_flow.step_3_amount_entry(update, context, side)
    return AMOUNT

# ... continue pattern for each step

# Build ConversationHandler
order_wizard = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_order, pattern="^menu_order$")],
    states={
        COIN: [CallbackQueryHandler(coin_selected, pattern="^coin:")],
        SIDE: [CallbackQueryHandler(side_selected, pattern="^side:")],
        AMOUNT: [CallbackQueryHandler(amount_selected, pattern="^amount:")],
        LEVERAGE: [CallbackQueryHandler(leverage_selected, pattern="^leverage:")],
        PREVIEW: [
            CallbackQueryHandler(execute_order, pattern="^confirm_order:"),
            CallbackQueryHandler(show_full_preview, pattern="^preview_full")
        ],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")],
)
```

---

### Pattern 6: Success Message with Next Actions

**Use Case**: After any completed action

```python
from src.bot.components.buttons import ButtonBuilder

async def order_executed_success(update: Update, coin: str, amount: float):
    """Show success with next action suggestions."""

    message = f"""
✅ **Order Executed!**

⚡ Leverage set to 5x for {coin}
📈 Market BUY executed
   Value: {format_currency(amount)}

💰 New Position created
   Liquidation: ~20% away

━━━━━━━━━━━━━━━━━
**What's next?**
"""

    buttons = ButtonBuilder()\
        .add_action("Set Stop Loss", f"set_sl:{coin}", "🛡️")\
        .add_secondary("View Position", f"view_pos:{coin}", "📊")\
        .add_secondary("Place Another Order", "menu_trade", "🔄")\
        .add_secondary("Main Menu", "menu_main", "🔙")\
        .build()

    query = update.callback_query
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=buttons)
```

---

### Pattern 7: Error Handling

**Use Case**: Show helpful error messages

```python
from src.bot.components.buttons import ButtonBuilder

async def handle_order_error(update: Update, error: Exception, context: dict):
    """Show error with helpful guidance."""

    # Determine error type and provide specific help
    if isinstance(error, InsufficientMarginError):
        message = f"""
❌ **Insufficient Margin**

You need {format_currency(context['required'])} but only have {format_currency(context['available'])}.

**Options:**
• Reduce order size
• Lower leverage (currently {context['leverage']}x)
• Deposit more funds
"""
        buttons = ButtonBuilder()\
            .add_action("Reduce Order Size", f"adjust_order:{context['coin']}", "📉")\
            .add_secondary("Lower Leverage", f"change_lev:{context['coin']}", "⚡")\
            .add_secondary("Cancel", "menu_main", "❌")\
            .build()

    else:
        # Generic error
        message = f"""
❌ **Error**

{str(error)}

Please try again or contact support if the issue persists.
"""
        buttons = ButtonBuilder()\
            .add_action("Try Again", "retry_order", "🔄")\
            .add_secondary("Main Menu", "menu_main", "🔙")\
            .build()

    query = update.callback_query
    await query.edit_message_text(message, parse_mode="Markdown", reply_markup=buttons)
```

---

## 🧪 Testing Your Components

### Unit Test Example

```python
# tests/bot/handlers/test_my_handler.py

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.bot.handlers.my_handler import show_order_preview
from src.bot.components.preview import PreviewData

@pytest.mark.asyncio
async def test_show_order_preview_quick():
    """Test quick preview display."""

    # Mock update
    update = Mock()
    update.callback_query = Mock()
    update.callback_query.edit_message_text = AsyncMock()

    # Call handler
    await show_order_preview(update, "BTC", "BUY", 1000, 5, show_full=False)

    # Assert
    call_args = update.callback_query.edit_message_text.call_args
    message = call_args[0][0]

    # Verify quick preview format
    assert "📋 **Order Preview**" in message
    assert "BTC BUY" in message
    assert "$1,000" in message
    assert "5x" in message

    # Verify buttons include "Full Details"
    keyboard = call_args[1]['reply_markup']
    assert any("Full Details" in str(row) for row in keyboard.inline_keyboard)


@pytest.mark.asyncio
async def test_show_order_preview_full():
    """Test full preview display."""

    update = Mock()
    update.callback_query = Mock()
    update.callback_query.edit_message_text = AsyncMock()

    await show_order_preview(update, "BTC", "BUY", 1000, 5, show_full=True)

    call_args = update.callback_query.edit_message_text.call_args
    message = call_args[0][0]

    # Verify full preview includes all cards
    assert "CAPITAL IMPACT" in message
    assert "RISK ASSESSMENT" in message
    assert "Margin Required" in message
    assert "Liquidation" in message
```

### Integration Test Example

```python
# tests/bot/flows/test_order_flow.py

import pytest
from src.bot.components.flows.order_flow import OrderFlowOrchestrator

@pytest.mark.asyncio
async def test_complete_order_flow():
    """Test complete order flow from start to finish."""

    orchestrator = OrderFlowOrchestrator()

    # Mock update and context
    update = create_mock_update()
    context = create_mock_context()

    # Step 1: Coin selection
    await orchestrator.step_2_side_selection(update, context, "BTC")
    assert orchestrator.state.coin == "BTC"

    # Step 2: Side selection
    await orchestrator.step_3_amount_entry(update, context, "BUY")
    assert orchestrator.state.side == "BUY"

    # Step 3: Amount entry
    await orchestrator.step_4_leverage_selection(update, context, 1000.0)
    assert orchestrator.state.amount_usd == 1000.0

    # Step 4: Leverage selection
    await orchestrator.step_5_preview(update, context, 5)
    assert orchestrator.state.leverage == 5

    # Verify preview was shown
    assert update.callback_query.edit_message_text.called
    message = update.callback_query.edit_message_text.call_args[0][0]
    assert "Order Preview" in message
```

---

## 📋 Cheat Sheet: When to Use Each Component

| Need | Component | File |
|------|-----------|------|
| Format money | `format_currency()` | `formatters.py` |
| Format PnL | `format_pnl()` | `formatters.py` |
| Show risk level | `get_risk_indicator()` | `risk.py` |
| Build buttons | `ButtonBuilder()` | `buttons.py` |
| Show loading | `LoadingMessage.show()` | `loading.py` |
| Display info | `InfoCard()` | `cards.py` |
| Order preview | `PreviewBuilder` | `preview.py` |
| Sort/group list | `SortableList()` | `lists.py` |
| Complete order flow | `OrderFlowOrchestrator()` | `flows/order_flow.py` |
| Position display | `PositionDisplay` | `flows/position_display.py` |

---

## 🎨 Design Tokens (Constants)

Create a constants file for consistency:

```python
# src/bot/components/constants.py

# Emojis
EMOJI_RISK_LOW = "🟢"
EMOJI_RISK_MODERATE = "🟡"
EMOJI_RISK_HIGH = "🟠"
EMOJI_RISK_CRITICAL = "🔴"

EMOJI_LONG = "🟢"
EMOJI_SHORT = "🔴"

EMOJI_PNL_POSITIVE = "🟢"
EMOJI_PNL_NEGATIVE = "🔴"
EMOJI_PNL_ZERO = "⚪"

# Separator
SEPARATOR = "━━━━━━━━━━━━━━━━━"

# Risk thresholds (percentage distance to liquidation)
RISK_THRESHOLD_LOW = 25.0
RISK_THRESHOLD_MODERATE = 15.0
RISK_THRESHOLD_HIGH = 10.0

# Default decimals
DECIMALS_CURRENCY = 2
DECIMALS_PERCENTAGE = 1
DECIMALS_COIN_LARGE = 2  # >= 1000
DECIMALS_COIN_MEDIUM = 4  # >= 1
DECIMALS_COIN_SMALL = 6  # < 1

# Button labels
LABEL_CONFIRM = "✅"
LABEL_CANCEL = "❌"
LABEL_BACK = "🔙"
LABEL_DETAILS = "📊"

# Loading messages
LOADING_PREVIEW = "⏳ Calculating preview..."
LOADING_PRICE = "⏳ Fetching current price..."
LOADING_ORDER = "⏳ Placing order..."
LOADING_POSITION = "⏳ Fetching position..."
```

Usage:
```python
from src.bot.components.constants import EMOJI_RISK_LOW, SEPARATOR

message = f"""
{SEPARATOR}
Risk: LOW {EMOJI_RISK_LOW}
{SEPARATOR}
"""
```

---

## 🔧 Common Customizations

### Custom Info Card

```python
# Add your own card types

def build_stop_loss_card(
    has_sl: bool,
    sl_price: float = None,
    potential_loss: float = None
) -> InfoCard:
    """Custom stop loss card."""
    card = InfoCard("STOP LOSS PROTECTION", "🛡️")

    if has_sl:
        card.add_field("Active SL", format_currency(sl_price), "✅")
        card.add_field("Max Loss", format_currency(potential_loss), "⚠️")
    else:
        card.add_field("Status", "No protection set ❌")
        card.add_field("Recommendation", "Set stop loss to limit risk", "💡")

    return card
```

### Custom Button Presets

```python
# src/bot/components/buttons.py (add to file)

def build_leverage_selector_buttons(
    current_leverage: int,
    available_leverages: list[int]
) -> InlineKeyboardMarkup:
    """Build leverage selector with current highlighted."""
    builder = ButtonBuilder()

    # Build rows of leverage options
    row_buttons = []
    for lev in available_leverages:
        emoji = "✨" if lev == current_leverage else ""
        row_buttons.append((f"{lev}x", f"lev:{lev}", emoji))

        # Max 4 per row
        if len(row_buttons) == 4:
            builder.add_row(*row_buttons)
            row_buttons = []

    # Add remaining
    if row_buttons:
        builder.add_row(*row_buttons)

    builder.add_secondary("Custom", "lev:custom")\
           .add_back_cancel()

    return builder.build()
```

---

## 💡 Best Practices

### DO ✅

1. **Always use components** instead of building messages manually
2. **Show loading states** for async operations
3. **Use action-oriented button labels** ("Buy $1,000 BTC" not "Confirm")
4. **Provide "What's next?" suggestions** after actions
5. **Group related information** with InfoCards
6. **Test mobile view** (messages should fit on small screens)
7. **Handle errors gracefully** with helpful guidance
8. **Use constants** for emojis and thresholds

### DON'T ❌

1. **Don't hardcode formatting** - use formatters
2. **Don't skip loading states** - users get anxious
3. **Don't use generic labels** - be specific
4. **Don't overwhelm** - use two-tier previews
5. **Don't forget error handling** - assume things will fail
6. **Don't ignore UX patterns** - consistency matters
7. **Don't skip tests** - components should be reliable
8. **Don't duplicate logic** - DRY principle

---

## 🚀 Quick Migration Guide

### Before (Old Code)

```python
async def show_position(update: Update, coin: str):
    """Old way - manual formatting."""
    pos = get_position(coin)

    message = f"""
Position: {coin}
Size: {pos['size']:.4f}
PnL: ${pos['pnl']:.2f}
Liquidation: ${pos['liq']:.2f}
"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Close", callback_data=f"close:{coin}")],
        [InlineKeyboardButton("Back", callback_data="menu_main")]
    ])

    await update.message.reply_text(message, reply_markup=keyboard)
```

### After (New Components)

```python
from src.bot.components.flows.position_display import PositionDisplay
from src.bot.components.buttons import ButtonBuilder

async def show_position(update: Update, coin: str):
    """New way - using components."""
    pos = get_position(coin)

    # Use PositionDisplay component
    message = PositionDisplay.build_detail_view(pos)

    # Use ButtonBuilder
    buttons = ButtonBuilder()\
        .add_action("Close Position", f"close:{coin}", "❌")\
        .add_secondary("Set Stop Loss", f"set_sl:{coin}", "🛡️")\
        .add_back_cancel()\
        .build()

    await update.message.reply_text(message, parse_mode="Markdown", reply_markup=buttons)
```

**Benefits**:
- ✅ Consistent formatting across all handlers
- ✅ Automatic risk indicators
- ✅ Maintainable (update component, updates everywhere)
- ✅ Testable (components have unit tests)
- ✅ Mobile-optimized

---

## 📞 Getting Help

### Component Not Working?

1. Check the component's docstring for examples
2. Look at tests: `tests/bot/components/test_*.py`
3. See usage in existing handlers
4. Ask in team chat with code sample

### Need a New Component?

1. Check if you can compose existing components
2. If truly new, follow [Component Library](./TELEGRAM_UX_COMPONENT_LIBRARY.md) structure
3. Add tests
4. Update this guide with usage example
5. Submit PR with documentation

### Performance Issues?

1. Profile with `cProfile`
2. Check if you're calling services multiple times
3. Cache expensive calculations
4. Use async/await properly

---

**Last Updated**: 2025-12-01
**Maintained By**: Hyperbot Development Team
**Questions?**: See [TELEGRAM_UX_COMPONENT_LIBRARY.md](./TELEGRAM_UX_COMPONENT_LIBRARY.md)
