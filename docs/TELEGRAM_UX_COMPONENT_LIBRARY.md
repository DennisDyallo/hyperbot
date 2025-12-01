# Telegram Trading Bot UX Component Library

**Version**: 1.0
**Last Updated**: 2025-12-01
**Status**: 📐 Design System - Ready for Implementation
**Purpose**: Reusable, maintainable UX patterns for consistent Telegram bot interactions

---

## 🎯 Design System Overview

This document defines **atomic components** and **composition patterns** for building consistent, high-quality Telegram bot interactions. Each component is:

- ✅ **Reusable**: Can be used across multiple flows
- ✅ **Maintainable**: Single source of truth for updates
- ✅ **Accessible**: Clear visual hierarchy and scannability
- ✅ **Mobile-First**: Optimized for small screens
- ✅ **Testable**: Predictable output for automated testing

---

## 📦 Component Architecture

```
┌─────────────────────────────────────┐
│   ATOMIC COMPONENTS (Level 1)       │
│   - Text Formatters                 │
│   - Buttons                         │
│   - Emojis                          │
│   - Loading States                  │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   MOLECULAR COMPONENTS (Level 2)    │
│   - Info Cards                      │
│   - Previews                        │
│   - Lists                           │
│   - Forms                           │
└─────────────────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│   ORGANISM COMPONENTS (Level 3)     │
│   - Order Flow                      │
│   - Position View                   │
│   - Risk Summary                    │
└─────────────────────────────────────┘
```

---

## 🧱 Level 1: Atomic Components

### 1.1 Text Formatters

#### `format_currency(amount: float, symbol: str = "$") -> str`
**Purpose**: Consistent currency formatting

```python
# src/bot/components/formatters.py

def format_currency(amount: float, symbol: str = "$", decimals: int = 2) -> str:
    """
    Format currency with consistent decimal places and separators.

    Examples:
        format_currency(1234.56) → "$1,234.56"
        format_currency(1234.567, decimals=3) → "$1,234.567"
        format_currency(-500) → "-$500.00"
    """
    sign = "-" if amount < 0 else ""
    abs_amount = abs(amount)
    formatted = f"{abs_amount:,.{decimals}f}"
    return f"{sign}{symbol}{formatted}"


def format_percentage(value: float, decimals: int = 1, show_sign: bool = True) -> str:
    """
    Format percentage with consistent display.

    Examples:
        format_percentage(5.67) → "+5.7%"
        format_percentage(-3.2) → "-3.2%"
        format_percentage(0.5, show_sign=False) → "0.5%"
    """
    sign = "+" if value > 0 and show_sign else ""
    return f"{sign}{value:.{decimals}f}%"


def format_coin_size(amount: float, coin: str, decimals: int = None) -> str:
    """
    Format coin amounts with appropriate decimal places.

    Examples:
        format_coin_size(0.01234, "BTC") → "0.01234 BTC"
        format_coin_size(123.456, "SOL", decimals=2) → "123.46 SOL"
    """
    if decimals is None:
        # Auto-determine decimals based on magnitude
        if amount >= 1000:
            decimals = 2
        elif amount >= 1:
            decimals = 4
        else:
            decimals = 6

    return f"{amount:.{decimals}f} {coin}"
```

#### `format_pnl(pnl: float, pnl_pct: float) -> tuple[str, str]`
**Purpose**: Consistent PnL display with emoji

```python
def format_pnl(pnl: float, pnl_pct: float) -> tuple[str, str]:
    """
    Format PnL with emoji and consistent styling.

    Returns:
        tuple: (formatted_string, emoji)

    Examples:
        format_pnl(123.45, 5.2) → ("+$123.45 (+5.2%)", "🟢")
        format_pnl(-50.00, -2.5) → ("-$50.00 (-2.5%)", "🔴")
        format_pnl(0, 0) → ("$0.00 (0.0%)", "⚪")
    """
    if pnl > 0:
        emoji = "🟢"
        formatted = f"+{format_currency(pnl)} (+{format_percentage(pnl_pct, show_sign=False)})"
    elif pnl < 0:
        emoji = "🔴"
        formatted = f"{format_currency(pnl)} ({format_percentage(pnl_pct, show_sign=False)})"
    else:
        emoji = "⚪"
        formatted = f"{format_currency(0)} (0.0%)"

    return formatted, emoji
```

---

### 1.2 Risk Level Indicators

#### `RiskLevel` Enum and Formatter

```python
# src/bot/components/risk.py

from enum import Enum
from typing import NamedTuple

class RiskLevel(str, Enum):
    """Risk level categorization."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskIndicator(NamedTuple):
    """Risk indicator with display properties."""
    level: RiskLevel
    emoji: str
    color: str  # For future HTML/web views
    description: str

def get_risk_indicator(liquidation_distance_pct: float) -> RiskIndicator:
    """
    Determine risk level from liquidation distance.

    Args:
        liquidation_distance_pct: Percentage distance to liquidation (positive = safe)

    Returns:
        RiskIndicator with level, emoji, color, description

    Examples:
        get_risk_indicator(30.0) → LOW (🟢)
        get_risk_indicator(18.0) → MODERATE (🟡)
        get_risk_indicator(8.0) → HIGH (🟠)
        get_risk_indicator(3.0) → CRITICAL (🔴)
    """
    if liquidation_distance_pct >= 25:
        return RiskIndicator(
            level=RiskLevel.LOW,
            emoji="🟢",
            color="green",
            description="Healthy distance to liquidation"
        )
    elif liquidation_distance_pct >= 15:
        return RiskIndicator(
            level=RiskLevel.MODERATE,
            emoji="🟡",
            color="yellow",
            description="Normal risk for leveraged position"
        )
    elif liquidation_distance_pct >= 10:
        return RiskIndicator(
            level=RiskLevel.HIGH,
            emoji="🟠",
            color="orange",
            description="Close to liquidation - consider action"
        )
    else:
        return RiskIndicator(
            level=RiskLevel.CRITICAL,
            emoji="🔴",
            color="red",
            description="DANGER - Very close to liquidation"
        )
```

---

### 1.3 Buttons (InlineKeyboard Builders)

#### `ButtonBuilder` Class

```python
# src/bot/components/buttons.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional

class ButtonBuilder:
    """Fluent builder for consistent inline keyboard buttons."""

    def __init__(self):
        self.rows: List[List[InlineKeyboardButton]] = []

    def add_action(
        self,
        label: str,
        callback_data: str,
        emoji: str = ""
    ) -> 'ButtonBuilder':
        """
        Add primary action button (full width).

        Examples:
            .add_action("Buy $1,000 BTC", "confirm_buy:BTC:1000", "✅")
        """
        full_label = f"{emoji} {label}".strip()
        self.rows.append([
            InlineKeyboardButton(full_label, callback_data=callback_data)
        ])
        return self

    def add_secondary(
        self,
        label: str,
        callback_data: str,
        emoji: str = ""
    ) -> 'ButtonBuilder':
        """Add secondary action button (full width)."""
        full_label = f"{emoji} {label}".strip()
        self.rows.append([
            InlineKeyboardButton(full_label, callback_data=callback_data)
        ])
        return self

    def add_row(self, *buttons: tuple[str, str, str]) -> 'ButtonBuilder':
        """
        Add row of buttons (2-3 per row max).

        Args:
            *buttons: tuples of (label, callback_data, emoji)

        Examples:
            .add_row(
                ("1x", "lev:1", "⚪"),
                ("3x", "lev:3", "✨"),
                ("5x", "lev:5", "🟡")
            )
        """
        row = []
        for label, callback_data, emoji in buttons:
            full_label = f"{emoji} {label}".strip()
            row.append(InlineKeyboardButton(full_label, callback_data=callback_data))
        self.rows.append(row)
        return self

    def add_back_cancel(
        self,
        back_data: str = "menu_main",
        cancel_data: Optional[str] = None
    ) -> 'ButtonBuilder':
        """Add standard back/cancel row."""
        if cancel_data:
            self.rows.append([
                InlineKeyboardButton("🔙 Back", callback_data=back_data),
                InlineKeyboardButton("❌ Cancel", callback_data=cancel_data)
            ])
        else:
            self.rows.append([
                InlineKeyboardButton("🔙 Back to Menu", callback_data=back_data)
            ])
        return self

    def build(self) -> InlineKeyboardMarkup:
        """Build the final keyboard."""
        return InlineKeyboardMarkup(self.rows)


# Preset button sets
def build_confirm_action_buttons(
    action_label: str,
    confirm_callback: str,
    cancel_callback: str = "menu_main",
    details_callback: Optional[str] = None
) -> InlineKeyboardMarkup:
    """
    Standard confirmation buttons with optional details.

    Examples:
        build_confirm_action_buttons(
            "Buy $1,000 BTC",
            "confirm_buy:BTC:1000",
            details_callback="details_buy:BTC:1000"
        )
    """
    builder = ButtonBuilder()
    builder.add_action(action_label, confirm_callback, "✅")

    if details_callback:
        builder.add_secondary("Full Details", details_callback, "📊")

    builder.add_secondary("Cancel", cancel_callback, "❌")

    return builder.build()
```

---

### 1.4 Loading States

#### `LoadingMessage` Component

```python
# src/bot/components/loading.py

from typing import Optional
from telegram import Update

class LoadingMessage:
    """Manage loading state messages with consistent formatting."""

    MESSAGES = {
        "preview": "⏳ Calculating preview...",
        "price": "⏳ Fetching current price...",
        "order": "⏳ Placing order...",
        "leverage": "⏳ Setting leverage...",
        "position": "⏳ Fetching position...",
        "account": "⏳ Loading account data...",
        "risk": "⏳ Analyzing risk...",
        "close": "⏳ Closing position...",
        "cancel": "⏳ Canceling order...",
    }

    @staticmethod
    async def show(
        update: Update,
        action: str,
        custom_message: Optional[str] = None
    ):
        """
        Show loading message.

        Args:
            update: Telegram update
            action: Predefined action key or custom
            custom_message: Override with custom message

        Examples:
            await LoadingMessage.show(update, "preview")
            await LoadingMessage.show(update, "custom", "⏳ Processing...")
        """
        message = custom_message or LoadingMessage.MESSAGES.get(action, f"⏳ {action}...")

        if update.callback_query:
            await update.callback_query.edit_message_text(message)
        elif update.message:
            return await update.message.reply_text(message)
```

---

## 🔬 Level 2: Molecular Components

### 2.1 Info Cards

#### `InfoCard` Component

```python
# src/bot/components/cards.py

from typing import Optional, List
from dataclasses import dataclass

@dataclass
class InfoField:
    """Single field in an info card."""
    label: str
    value: str
    emoji: str = ""

class InfoCard:
    """Build formatted info cards with consistent styling."""

    def __init__(self, title: str, title_emoji: str = ""):
        self.title = f"{title_emoji} {title}".strip() if title_emoji else title
        self.fields: List[InfoField] = []

    def add_field(
        self,
        label: str,
        value: str,
        emoji: str = ""
    ) -> 'InfoCard':
        """Add a field to the card."""
        self.fields.append(InfoField(label, value, emoji))
        return self

    def render(self, include_separator: bool = True) -> str:
        """
        Render the card as formatted text.

        Example output:
        ━━━━━━━━━━━━━━━━━
        💰 CAPITAL IMPACT
        ━━━━━━━━━━━━━━━━━
        Margin Required: $200.00
        Margin Available: $5,200.00
        Buying Power Used: 3.8%
        """
        lines = []

        if include_separator:
            lines.append("━━━━━━━━━━━━━━━━━")

        lines.append(f"**{self.title}**")

        if include_separator:
            lines.append("━━━━━━━━━━━━━━━━━")

        for field in self.fields:
            emoji_prefix = f"{field.emoji} " if field.emoji else ""
            lines.append(f"{emoji_prefix}{field.label}: {field.value}")

        return "\n".join(lines)
```

#### Preset Info Cards

```python
def build_capital_impact_card(
    margin_required: float,
    margin_available: float,
    buying_power_used_pct: float
) -> InfoCard:
    """Standard capital impact card."""
    card = InfoCard("CAPITAL IMPACT", "💰")
    card.add_field("Margin Required", format_currency(margin_required))
    card.add_field("Margin Available", format_currency(margin_available))
    card.add_field("Buying Power Used", f"{buying_power_used_pct:.1f}%")
    return card


def build_risk_assessment_card(
    entry_price: float,
    liquidation_price: float,
    liquidation_distance_pct: float,
    leverage: int
) -> InfoCard:
    """Standard risk assessment card."""
    risk = get_risk_indicator(liquidation_distance_pct)

    card = InfoCard("RISK ASSESSMENT", "⚠️")
    card.add_field("Entry Price", format_currency(entry_price))
    card.add_field("Est. Liquidation", format_currency(liquidation_price))
    card.add_field("Safety Distance", f"{liquidation_distance_pct:.1f}% drop")
    card.add_field("Risk Level", f"{risk.level} {risk.emoji}")

    return card
```

---

### 2.2 Preview Components (Two-Tier Pattern)

#### `PreviewBuilder` Class

```python
# src/bot/components/preview.py

from typing import Optional, List
from dataclasses import dataclass

@dataclass
class PreviewData:
    """Data for order preview."""
    coin: str
    side: str  # "BUY" / "SELL"
    amount_usd: float
    leverage: int
    entry_price: float

    # Capital
    margin_required: float
    margin_available: float
    buying_power_used_pct: float

    # Risk
    liquidation_price: float
    liquidation_distance_pct: float

    # Optional
    size_coin: Optional[float] = None
    warnings: List[str] = None

class PreviewBuilder:
    """Build two-tier previews (quick + full)."""

    @staticmethod
    def build_quick_preview(data: PreviewData) -> str:
        """
        Build mobile-optimized quick preview.

        Shows only essential info on one screen.
        """
        side_emoji = "🟢" if data.side == "BUY" else "🔴"
        risk = get_risk_indicator(data.liquidation_distance_pct)

        lines = [
            "📋 **Order Preview**\n",
            f"💰 {data.coin} {data.side} {side_emoji}: {format_currency(data.amount_usd)} @ market",
            f"⚡ Leverage: {data.leverage}x",
            f"📊 Margin: {format_currency(data.margin_required)} / {format_currency(data.margin_available)} available",
            f"🎯 Liquidation: {format_currency(data.liquidation_price)} ({format_percentage(data.liquidation_distance_pct, show_sign=False)} away)",
            f"⚠️ Risk: {risk.level} {risk.emoji}",
        ]

        return "\n".join(lines)

    @staticmethod
    def build_full_preview(data: PreviewData) -> str:
        """
        Build comprehensive preview with all details.

        Includes all cards and scenarios.
        """
        side_emoji = "🟢" if data.side == "BUY" else "🔴"

        # Header
        header = [
            "📋 **Complete Order Analysis**\n",
            f"Coin: {data.coin}",
            f"Side: {data.side} {side_emoji}",
            f"Amount: {format_currency(data.amount_usd)}",
            f"Leverage: {data.leverage}x ⚡\n",
        ]

        # Capital Impact Card
        capital_card = build_capital_impact_card(
            data.margin_required,
            data.margin_available,
            data.buying_power_used_pct
        )

        # Risk Assessment Card
        risk_card = build_risk_assessment_card(
            data.entry_price,
            data.liquidation_price,
            data.liquidation_distance_pct,
            data.leverage
        )

        # Additional Info
        additional = []
        if data.size_coin:
            additional.append(f"Position Size: {format_coin_size(data.size_coin, data.coin)}")
        additional.append(f"Total Exposure: {format_currency(data.amount_usd)}")

        # Warnings
        warnings = []
        if data.warnings:
            warnings.append("\n⚠️ **Warnings**:")
            for warning in data.warnings:
                warnings.append(f"• {warning}")

        # Combine all sections
        parts = [
            "\n".join(header),
            capital_card.render(),
            risk_card.render(),
            "\n".join(additional)
        ]

        if warnings:
            parts.append("\n".join(warnings))

        return "\n\n".join(parts)
```

---

### 2.3 List Components (Risk-Sorted)

#### `SortableList` Component

```python
# src/bot/components/lists.py

from typing import List, Callable, TypeVar, Generic
from enum import Enum

T = TypeVar('T')

class SortOption(str, Enum):
    """Available sort options."""
    RISK = "risk"
    SIZE = "size"
    PNL = "pnl"
    NAME = "name"

class SortableList(Generic[T]):
    """Build sortable lists with grouping."""

    def __init__(
        self,
        items: List[T],
        default_sort: SortOption = SortOption.RISK
    ):
        self.items = items
        self.current_sort = default_sort
        self.sort_functions: dict[SortOption, Callable] = {}

    def register_sort(
        self,
        option: SortOption,
        key_func: Callable[[T], any]
    ) -> 'SortableList':
        """Register a sort function."""
        self.sort_functions[option] = key_func
        return self

    def sort_by(self, option: SortOption) -> List[T]:
        """Sort items by option."""
        if option not in self.sort_functions:
            return self.items

        key_func = self.sort_functions[option]
        return sorted(self.items, key=key_func)

    def group_by_priority(
        self,
        priority_func: Callable[[T], bool],
        high_label: str = "⚠️ NEEDS ATTENTION",
        low_label: str = "✅ SAFE"
    ) -> tuple[List[T], List[T], str, str]:
        """
        Group items into high/low priority.

        Returns:
            (high_priority_items, low_priority_items, high_label, low_label)
        """
        high = [item for item in self.items if priority_func(item)]
        low = [item for item in self.items if not priority_func(item)]

        return high, low, high_label, low_label


# Example: Position list builder
def build_position_list(
    positions: List[dict],
    sort_by: SortOption = SortOption.RISK
) -> str:
    """
    Build formatted position list with sorting.

    Returns formatted string with sort controls.
    """
    # Create sortable list
    sortable = SortableList(positions, default_sort=sort_by)

    # Register sort functions
    sortable.register_sort(
        SortOption.RISK,
        lambda p: p['liquidation_distance_pct']  # Ascending (closest first)
    )
    sortable.register_sort(
        SortOption.SIZE,
        lambda p: -abs(p['position_value'])  # Descending
    )
    sortable.register_sort(
        SortOption.PNL,
        lambda p: -p['unrealized_pnl']  # Descending
    )
    sortable.register_sort(
        SortOption.NAME,
        lambda p: p['coin']  # Alphabetical
    )

    # Sort
    sorted_positions = sortable.sort_by(sort_by)

    # Group if risk-sorted
    if sort_by == SortOption.RISK:
        high, low, high_label, low_label = sortable.group_by_priority(
            lambda p: p['liquidation_distance_pct'] < 15  # <15% = high risk
        )

        # Render grouped
        lines = [
            f"📊 **Open Positions** ({len(positions)})\n",
            f"Sort: [⚠️ Risk] [💰 Size] [📈 PnL] [🔤 Name]\n",
        ]

        if high:
            lines.append(f"{high_label} ({len(high)})")
            lines.append("━━━━━━━━━━━━━━━━━")
            for pos in high:
                lines.append(_format_position_item(pos))
            lines.append("")

        if low:
            lines.append(f"{low_label} ({len(low)})")
            lines.append("━━━━━━━━━━━━━━━━━")
            for pos in low:
                lines.append(_format_position_item(pos))

        return "\n".join(lines)

    else:
        # Regular sorted list
        lines = [
            f"📊 **Open Positions** ({len(positions)})\n",
            f"Sort: [⚠️ Risk] [💰 Size] [📈 PnL] [🔤 Name]\n",
            "━━━━━━━━━━━━━━━━━",
        ]

        for pos in sorted_positions:
            lines.append(_format_position_item(pos))

        return "\n".join(lines)


def _format_position_item(pos: dict) -> str:
    """Format single position item."""
    side_emoji = "🟢" if pos['size'] > 0 else "🔴"
    pnl_str, pnl_emoji = format_pnl(pos['unrealized_pnl'], pos['pnl_pct'])
    risk = get_risk_indicator(pos['liquidation_distance_pct'])

    has_sl = pos.get('has_stop_loss', False)
    sl_indicator = "✅" if has_sl else "❌"

    return f"""
{side_emoji} **{pos['coin']}** {pos['side']} • {pnl_emoji} {pnl_str}
   Liq: {pos['liquidation_distance_pct']:.1f}% away {risk.emoji} | SL {sl_indicator}
   [Details] [Set SL] [Close]
"""
```

---

## 🏗️ Level 3: Organism Components (Complete Flows)

### 3.1 Order Flow Pattern

#### `OrderFlowOrchestrator` Class

```python
# src/bot/components/flows/order_flow.py

from typing import Optional
from dataclasses import dataclass
from telegram import Update
from telegram.ext import ContextTypes

@dataclass
class OrderFlowState:
    """State management for order flow."""
    coin: Optional[str] = None
    side: Optional[str] = None  # "BUY" / "SELL"
    amount_usd: Optional[float] = None
    leverage: Optional[int] = None
    preview_mode: str = "quick"  # "quick" / "full"

class OrderFlowOrchestrator:
    """
    Orchestrate complete order flow with consistent UX.

    Flow:
    1. Coin Selection
    2. Side Selection (Buy/Sell)
    3. Amount Entry
    4. Leverage Selection (context-aware)
    5. Preview (two-tier)
    6. Confirmation & Execution
    7. Success with Next Actions
    """

    def __init__(self):
        self.state = OrderFlowState()

    async def step_1_coin_selection(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Step 1: Select coin."""
        # Implementation using components
        pass

    async def step_2_side_selection(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        coin: str
    ):
        """Step 2: Buy or Sell."""
        self.state.coin = coin

        message = f"💰 **{coin} Market Order**\n\nStep 2/5: Buy or Sell?"

        buttons = ButtonBuilder()\
            .add_row(
                ("Buy", f"order_side:buy:{coin}", "🟢"),
                ("Sell", f"order_side:sell:{coin}", "🔴")
            )\
            .add_back_cancel()\
            .build()

        query = update.callback_query
        await query.edit_message_text(message, reply_markup=buttons)

    async def step_3_amount_entry(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        side: str
    ):
        """Step 3: Enter USD amount."""
        self.state.side = side

        # Show quick amount buttons
        message = (
            f"💰 **{self.state.coin} {side}**\n\n"
            f"Step 3/5: Enter amount in USD\n\n"
            f"Choose a preset or enter custom:"
        )

        buttons = ButtonBuilder()\
            .add_row(
                ("$100", "amount:100", ""),
                ("$500", "amount:500", ""),
                ("$1000", "amount:1000", "")
            )\
            .add_secondary("Custom Amount", "amount:custom")\
            .add_back_cancel()\
            .build()

        query = update.callback_query
        await query.edit_message_text(message, reply_markup=buttons)

    async def step_4_leverage_selection(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        amount_usd: float
    ):
        """Step 4: Select leverage (context-aware)."""
        self.state.amount_usd = amount_usd

        # Fetch buying power
        await LoadingMessage.show(update, "account")

        # Get account data (mock for example)
        account_value = 5200.0

        # Build context-aware leverage selector
        message = (
            f"⚡ **Select Leverage for {format_currency(amount_usd)} {self.state.coin}**\n\n"
            f"Your order: {format_currency(amount_usd)}\n"
            f"Available: {format_currency(account_value)}\n\n"
        )

        # Calculate buying power at each level
        leverage_options = [
            (1, account_value, "⚪ Conservative"),
            (3, account_value * 3, "✨ Good for this size"),
            (5, account_value * 5, "🟡 Higher risk"),
            (10, account_value * 10, "🔴 Risky"),
            (20, account_value * 20, "💀 Extreme risk")
        ]

        for lev, buying_power, label in leverage_options:
            can_afford = "✅" if buying_power >= amount_usd else "❌"
            message += f"{lev}x → {format_currency(buying_power)} max {can_afford} {label}\n"

        message += f"\n💡 For {format_currency(amount_usd)} orders, 3-5x balances opportunity and safety."

        # Build buttons
        builder = ButtonBuilder()
        for lev, _, _ in leverage_options[:4]:  # Show first 4
            builder.add_row((f"{lev}x", f"leverage:{lev}", ""))

        builder.add_secondary("Custom Leverage", "leverage:custom")\
               .add_back_cancel()

        query = update.callback_query
        await query.edit_message_text(message, reply_markup=builder.build())

    async def step_5_preview(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        leverage: int
    ):
        """Step 5: Show preview (two-tier)."""
        self.state.leverage = leverage

        # Calculate preview data
        await LoadingMessage.show(update, "preview")

        # Build preview (using PreviewBuilder)
        preview_data = await self._calculate_preview()

        if self.state.preview_mode == "quick":
            message = PreviewBuilder.build_quick_preview(preview_data)
            buttons = build_confirm_action_buttons(
                f"{self.state.side.title()} {format_currency(self.state.amount_usd)} {self.state.coin}",
                f"confirm_order:{self.state.coin}:{self.state.amount_usd}:{leverage}",
                details_callback="preview_full"
            )
        else:
            message = PreviewBuilder.build_full_preview(preview_data)
            buttons = build_confirm_action_buttons(
                f"{self.state.side.title()} {format_currency(self.state.amount_usd)} {self.state.coin}",
                f"confirm_order:{self.state.coin}:{self.state.amount_usd}:{leverage}",
                cancel_callback="menu_main"
            )

        query = update.callback_query
        await query.edit_message_text(message, parse_mode="Markdown", reply_markup=buttons)

    async def step_6_execute(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Step 6: Execute order."""
        await LoadingMessage.show(update, "order")

        # Execute order (mock)
        # ... actual execution logic

        # Success message with next actions
        success_msg = self._build_success_message()

        buttons = ButtonBuilder()\
            .add_action("Set Stop Loss", f"set_sl:{self.state.coin}", "🛡️")\
            .add_secondary("View Position", f"view_pos:{self.state.coin}", "📊")\
            .add_secondary("Main Menu", "menu_main", "🔙")\
            .build()

        query = update.callback_query
        await query.edit_message_text(success_msg, parse_mode="Markdown", reply_markup=buttons)

    async def _calculate_preview(self) -> PreviewData:
        """Calculate preview data."""
        # Mock implementation - replace with actual calculations
        return PreviewData(
            coin=self.state.coin,
            side=self.state.side,
            amount_usd=self.state.amount_usd,
            leverage=self.state.leverage,
            entry_price=98500.0,
            margin_required=self.state.amount_usd / self.state.leverage,
            margin_available=5200.0,
            buying_power_used_pct=3.8,
            liquidation_price=78800.0,
            liquidation_distance_pct=20.0,
            size_coin=0.01015
        )

    def _build_success_message(self) -> str:
        """Build success message."""
        return f"""
✅ **Order Executed!**

⚡ Leverage set to {self.state.leverage}x for {self.state.coin}
📈 Market {self.state.side} executed
   Value: {format_currency(self.state.amount_usd)}

💰 New Position created
   Liquidation: ~20% away

━━━━━━━━━━━━━━━━━
**What's next?**
"""
```

---

### 3.2 Position Display Pattern

#### Complete Position Display Component

```python
# src/bot/components/flows/position_display.py

from typing import List, Optional

class PositionDisplay:
    """Unified position display with all UX enhancements."""

    @staticmethod
    def build_list_view(
        positions: List[dict],
        sort_by: SortOption = SortOption.RISK,
        total_value: float = 0,
        total_pnl: float = 0,
        margin_used_pct: float = 0
    ) -> str:
        """
        Build complete position list view.

        Includes:
        - Summary stats
        - Sort controls
        - Risk-based grouping
        - Quick actions per position
        """
        # Header with stats
        pnl_str, pnl_emoji = format_pnl(total_pnl, (total_pnl / total_value * 100) if total_value > 0 else 0)

        header = [
            f"📊 **Open Positions** ({len(positions)})\n",
            f"Total Value: {format_currency(total_value)}",
            f"Total PnL: {pnl_emoji} {pnl_str}",
            f"Margin Used: {margin_used_pct:.0f}%\n",
        ]

        # Build sorted/grouped list
        position_list = build_position_list(positions, sort_by)

        # Risk summary footer
        high_risk_count = sum(1 for p in positions if p['liquidation_distance_pct'] < 15)
        no_sl_count = sum(1 for p in positions if not p.get('has_stop_loss', False))

        footer = []
        if high_risk_count > 0 or no_sl_count > 0:
            footer.append("\n━━━━━━━━━━━━━━━━━")
            footer.append("⚠️ **Risk Summary:**")
            if no_sl_count > 0:
                footer.append(f"• {no_sl_count} position(s) without stop loss")
            if high_risk_count > 0:
                footer.append(f"• {high_risk_count} position(s) with HIGH risk")

        return "\n".join(header) + "\n" + position_list + "\n".join(footer)

    @staticmethod
    def build_detail_view(position: dict) -> str:
        """
        Build detailed view for single position.

        Includes all risk metrics, stop loss info, scenarios.
        """
        # Position Info Card
        info_card = InfoCard("POSITION INFO", "💰")
        info_card.add_field("Coin", position['coin'])
        info_card.add_field("Side", f"{position['side']} {'🟢' if position['size'] > 0 else '🔴'}")
        info_card.add_field("Size", format_coin_size(abs(position['size']), position['coin']))
        info_card.add_field("Entry Price", format_currency(position['entry_price']))
        info_card.add_field("Current Price", format_currency(position['current_price']))
        info_card.add_field("Position Value", format_currency(position['position_value']))

        # Performance Card
        pnl_str, pnl_emoji = format_pnl(position['unrealized_pnl'], position['pnl_pct'])
        perf_card = InfoCard("PERFORMANCE", "📈")
        perf_card.add_field("Unrealized PnL", pnl_str, pnl_emoji)
        perf_card.add_field("ROI", f"{position['roi']:.1f}%")
        perf_card.add_field("Price Change", f"{position['price_change_pct']:.1f}%")

        # Leverage & Margin Card
        lev_card = InfoCard("LEVERAGE & MARGIN", "⚡")
        lev_card.add_field("Leverage", f"{position['leverage']}x")
        lev_card.add_field("Margin Used", format_currency(position['margin_used']))
        lev_card.add_field("Margin Type", position['margin_type'].title())

        # Risk Metrics Card
        risk = get_risk_indicator(position['liquidation_distance_pct'])
        risk_card = InfoCard("RISK METRICS", "🎯")
        risk_card.add_field("Liquidation Price", format_currency(position['liquidation_price']))
        risk_card.add_field("Distance", f"{position['liquidation_distance_pct']:.1f}% (from current)")
        risk_card.add_field("Safety Buffer", f"{format_currency(abs(position['current_price'] - position['liquidation_price']))} price drop")
        risk_card.add_field("Risk Level", f"{risk.level} {risk.emoji}")

        # Stop Loss Card
        sl_card = InfoCard("STOP LOSS", "🛡️")
        if position.get('has_stop_loss'):
            sl_card.add_field("Active SL", f"{format_currency(position['stop_loss_price'])} ✅")
            sl_card.add_field("Trigger", f"{position['stop_loss_distance_pct']:.1f}% from current")
            sl_card.add_field("Potential Loss", format_currency(position['potential_loss_at_sl']))
            sl_card.add_field("Order ID", f"#{position['stop_loss_order_id']}")
        else:
            sl_card.add_field("Status", "No stop loss set ❌")

        # Scenarios
        scenarios = self._build_scenarios(position)

        # Combine all parts
        parts = [
            f"📊 **{position['coin']} {position['side']} Position Details**\n",
            info_card.render(),
            perf_card.render(),
            lev_card.render(),
            risk_card.render(),
            sl_card.render(),
            scenarios
        ]

        return "\n\n".join(parts)

    @staticmethod
    def _build_scenarios(position: dict) -> str:
        """Build scenario analysis."""
        scenarios = InfoCard("SCENARIOS", "💡")

        # Price targets
        current = position['current_price']
        entry = position['entry_price']
        liq = position['liquidation_price']

        # +5%, +10% scenarios
        up_5 = current * 1.05
        up_10 = current * 1.10
        down_5 = current * 0.95
        down_10 = current * 0.90

        scenarios.add_field(
            f"If {position['coin']} reaches:",
            f"• {format_currency(up_5)} (+5%): +{format_currency((up_5 - entry) * abs(position['size']))} PnL\n"
            f"• {format_currency(up_10)} (+10%): +{format_currency((up_10 - entry) * abs(position['size']))} PnL\n"
            f"• {format_currency(down_5)} (-5%): {format_currency((down_5 - entry) * abs(position['size']))} PnL\n"
            f"• {format_currency(down_10)} (-10%): {format_currency((down_10 - entry) * abs(position['size']))} PnL\n"
            f"• {format_currency(liq)} (liq): 💀 LIQUIDATED"
        )

        return scenarios.render()
```

---

## 📐 Implementation Guide for Developers

### File Structure

```
src/bot/components/
├── __init__.py
├── formatters.py       # Currency, percentage, PnL formatters
├── risk.py             # Risk level indicators
├── buttons.py          # ButtonBuilder and presets
├── loading.py          # LoadingMessage component
├── cards.py            # InfoCard and preset cards
├── preview.py          # PreviewBuilder (two-tier)
├── lists.py            # SortableList and builders
└── flows/
    ├── __init__.py
    ├── order_flow.py   # OrderFlowOrchestrator
    └── position_display.py  # PositionDisplay
```

### Usage Examples

#### Example 1: Market Order Handler

```python
# src/bot/handlers/wizard_market_order.py (refactored)

from src.bot.components.flows.order_flow import OrderFlowOrchestrator

order_flow = OrderFlowOrchestrator()

async def market_wizard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start market order - now using orchestrator."""
    await order_flow.step_1_coin_selection(update, context)

async def handle_leverage_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leverage selection - delegates to orchestrator."""
    query = update.callback_query
    leverage = int(query.data.split(":")[1])

    await order_flow.step_5_preview(update, context, leverage)
```

#### Example 2: Position Display

```python
# src/bot/handlers/commands.py (refactored)

from src.bot.components.flows.position_display import PositionDisplay

async def positions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show positions using new component."""
    # Fetch positions
    positions = position_service.list_positions()

    # Calculate totals
    total_value = sum(p['position_value'] for p in positions)
    total_pnl = sum(p['unrealized_pnl'] for p in positions)
    margin_used_pct = 62.0  # from account service

    # Build view
    message = PositionDisplay.build_list_view(
        positions,
        sort_by=SortOption.RISK,
        total_value=total_value,
        total_pnl=total_pnl,
        margin_used_pct=margin_used_pct
    )

    # Send
    await update.message.reply_text(message, parse_mode="Markdown")
```

#### Example 3: Using Components Directly

```python
# Quick preview in any handler

from src.bot.components.preview import PreviewBuilder, PreviewData
from src.bot.components.buttons import build_confirm_action_buttons

# Build preview data
preview_data = PreviewData(
    coin="BTC",
    side="BUY",
    amount_usd=1000,
    leverage=5,
    entry_price=98500,
    margin_required=200,
    margin_available=5200,
    buying_power_used_pct=3.8,
    liquidation_price=78800,
    liquidation_distance_pct=20.0
)

# Render quick preview
message = PreviewBuilder.build_quick_preview(preview_data)

# Build buttons
buttons = build_confirm_action_buttons(
    "Buy $1,000 BTC",
    "confirm_buy:BTC:1000:5",
    details_callback="preview_full"
)

# Send
await query.edit_message_text(message, reply_markup=buttons)
```

---

## ✅ Testing Strategy

### Unit Tests for Components

```python
# tests/bot/components/test_formatters.py

import pytest
from src.bot.components.formatters import format_currency, format_pnl

class TestFormatters:
    def test_format_currency_positive(self):
        assert format_currency(1234.56) == "$1,234.56"

    def test_format_currency_negative(self):
        assert format_currency(-500.00) == "-$500.00"

    def test_format_pnl_positive(self):
        text, emoji = format_pnl(123.45, 5.2)
        assert text == "+$123.45 (+5.2%)"
        assert emoji == "🟢"

    def test_format_pnl_negative(self):
        text, emoji = format_pnl(-50.00, -2.5)
        assert text == "-$50.00 (-2.5%)"
        assert emoji == "🔴"
```

### Integration Tests for Flows

```python
# tests/bot/components/test_order_flow.py

import pytest
from unittest.mock import Mock, AsyncMock
from src.bot.components.flows.order_flow import OrderFlowOrchestrator

@pytest.mark.asyncio
async def test_order_flow_complete():
    """Test complete order flow."""
    orchestrator = OrderFlowOrchestrator()

    # Mock update and context
    update = Mock()
    context = Mock()

    # Step through flow
    await orchestrator.step_2_side_selection(update, context, "BTC")
    assert orchestrator.state.coin == "BTC"

    await orchestrator.step_3_amount_entry(update, context, "BUY")
    assert orchestrator.state.side == "BUY"

    # ... test remaining steps
```

---

## 📊 Component Maintenance Checklist

### When Adding a New Component

- [ ] Create component file in appropriate directory
- [ ] Write comprehensive docstrings with examples
- [ ] Add type hints for all parameters
- [ ] Create unit tests (target: 90% coverage)
- [ ] Add integration test for flows
- [ ] Document in this file
- [ ] Create usage example
- [ ] Update CHANGELOG.md

### When Updating a Component

- [ ] Check all usages (grep search)
- [ ] Update tests
- [ ] Update documentation
- [ ] Verify backward compatibility
- [ ] Update version number if breaking change

### Code Review Standards

- [ ] Follows component patterns from this doc
- [ ] Has clear separation of concerns
- [ ] Reuses existing components where possible
- [ ] No hardcoded strings (use constants)
- [ ] Mobile-optimized (fits on small screens)
- [ ] Accessible (clear hierarchy)
- [ ] Tested

---

## 🔄 Migration Path

### Phase 1: Foundation (Week 1)
1. ✅ Create component directory structure
2. ✅ Implement Level 1 components (formatters, buttons, loading)
3. ✅ Write unit tests
4. ✅ Update 1-2 handlers to use new components (proof of concept)

### Phase 2: Molecular Components (Week 2)
1. ✅ Implement Level 2 components (cards, previews, lists)
2. ✅ Refactor market order wizard to use components
3. ✅ Refactor positions view to use components
4. ✅ Write integration tests

### Phase 3: Organism Components (Week 3)
1. ✅ Implement Level 3 flows (OrderFlowOrchestrator, PositionDisplay)
2. ✅ Refactor scale order wizard
3. ✅ Refactor close position flow
4. ✅ Full test coverage

### Phase 4: Cleanup (Week 4)
1. ✅ Remove old code
2. ✅ Update all remaining handlers
3. ✅ Performance optimization
4. ✅ Documentation update
5. ✅ Launch to production

---

## 📚 Additional Resources

### Related Documents
- [PHASE_7_PLAN.md](./PHASE_7_PLAN.md) - Feature specifications
- [UX_IMPROVEMENT_OPPORTUNITIES.md](./UX_IMPROVEMENT_OPPORTUNITIES.md) - Analysis of all flows
- [NAMING_CONVENTION.md](./NAMING_CONVENTION.md) - Code style guide

### Design References
- Telegram Bot API: https://core.telegram.org/bots/api
- Atomic Design Methodology: https://atomicdesign.bradfrost.com/
- Mobile-First UX Best Practices

---

**Last Updated**: 2025-12-01
**Component Library Version**: 1.0
**Maintained By**: Hyperbot UX & Development Team
**Next Review**: After Phase 7 implementation
