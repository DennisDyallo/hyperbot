# Telegram UX System Guide

**Status**: Canonical Design System Reference
**Effective**: 2025-12-07
**Supersedes**: `docs/TELEGRAM_UX_COMPONENT_LIBRARY.md`, `docs/UX_DESIGN_SPECIFICATIONS.md`

> The historical versions of the superseded documents live in `docs/archive/2025-12-07-ux/`. Use this guide as the single source of truth for Telegram UX patterns and component expectations. Implementation guidance now lives in `docs/telegram-ux-implementation-playbook.md`.

---

## 1. Purpose & Scope

- Provide the definitive rules for how Hyperbot communicates inside Telegram.
- Align engineering, UX, and QA on component behavior, formatting, and interaction patterns.
- Serve as the reference point for future design reviews and regression checks.

## 2. Design Principles

- **Consistency**: Every flow uses the same building blocks—formatters, cards, previews, and navigation patterns.
- **Clarity**: Information is scannable on a single mobile screen; the most important values are visually prioritized.
- **Safety**: Risk states and leverage implications are explicit and reinforced with standardized language and emojis.
- **Performance**: Responses render quickly, avoid unnecessary markdown, and keep keyboards reachable with thumbs.
- **Testability**: Components produce deterministic output so unit tests can assert exact strings and button layouts.

## 3. Foundations

### 3.1 Typography Hierarchy

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HEADING 1 (Main titles)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Format: **TITLE TEXT**
Usage: Section headers, main titles
Example: **💰 CAPITAL IMPACT**

Heading 2 (Subsections)
Format: **Text**
Usage: Subsection titles
Example: **Order Preview**

Body Text
Format: Plain text
Usage: Labels, descriptions
Example: Margin Required: $200.00

Emphasis
Format: **Value** or _Text_
Usage: Highlight key numbers
Example: PnL: **+$123.45 (+5.2%)**

Inline Code
Format: `text`
Usage: Order IDs, wallet addresses
Example: Order ID: `#12345678`
```

### 3.2 Spacing & Layout Rules

- Use `\n` for single line breaks and `\n\n` for blank lines between sections.
- Title sits at the top—never prepend blank lines.
- When separating sections, insert `━━━━━━━━━━━━━━━━━` (17 characters) with a blank line above and below.
- Always include a blank line before inline keyboard buttons.
- Keep quick previews ≤10 lines to avoid scrolling on 4.7" screens.

### 3.3 Visual Semantics (Emoji Legend)

| Emoji | Meaning | Typical Use |
| --- | --- | --- |
| 🟢 | Positive, safe | Profit, healthy risk, long bias |
| 🔴 | Negative, danger | Losses, critical risk, urgent errors |
| 🟡 | Caution | Moderate risk, warnings |
| 🟠 | High risk | Actions requiring immediate attention |
| ⚪ | Neutral | Zero PnL, informational states |
| ✨ | Recommended | Highlighted options, defaults |
| ⚡ | Leverage | Display leverage levels and power |
| 💀 | Extreme danger | Liquidation warnings, irreversible actions |

Maintain consistent emoji positioning so users learn the visual language.

## 4. Component Architecture

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

Atomic pieces must be implemented and tested first; higher-level components compose only from lower-level abstractions.

## 5. Level 1 — Atomic Components

### 5.1 Text Formatters (`src/bot/components/formatters.py`)

- Provide deterministic helpers such as `format_currency`, `format_percentage`, `format_coin_size`, and `format_pnl`.
- Default to two decimal places for USD values; auto-adjust decimals for coin sizes based on magnitude.
- `format_pnl` returns both formatted string and emoji so messaging stays consistent.
- Unit tests must cover zero, negative, and large values.

### 5.2 Button Patterns (`src/bot/components/buttons.py`)

- `ButtonBuilder` constructs inline keyboards with expressive helpers: `.action`, `.back`, `.cancel`, `.navigation_back_cancel`, `.navigation_main`, `.next_actions`, `.build`.
- Action buttons include verb + amount (e.g., `✅ Buy $1,000 BTC`).
- Provide preset navigation rows for common flows (Back/Cancel/Home) and grouped follow-up actions.
- Ensure callback data remains stable for integration tests.

### 5.3 Loading States (`src/bot/components/loading.py`)

- `LoadingMessage` shows contextual progress ("⏳ Calculating preview…").
- Always pair `show` with `hide` to prevent lingering messages.
- Offer named presets for expensive operations (pricing, leverage, settlement).
- Use awaitable helpers so handlers remain concise.

### 5.4 Risk Indicators (`src/bot/components/risk.py`)

- `RiskLevel` enum (SAFE→EXTREME) maps to frozen `RiskDescriptor` records for emoji, severity, summary, tooltip.
- `calculate_risk_level` converts liquidation distance into standardized risk tiers.
- `format_risk_indicator`, `build_risk_summary`, `build_risk_tooltip` keep messaging consistent across cards and previews.
- Keep threshold values centralized to avoid divergence across flows.

## 6. Level 2 — Molecular Components

### 6.1 Info Cards (`src/bot/components/cards.py`)

- `InfoCard` exposes `add_field`, `add_separator`, and `render` for structured sections.
- Provide factories for capital impact, risk assessment, and summary cards.
- Cards respect typography and spacing rules from §3.

### 6.2 Preview Builder (`src/bot/components/preview.py`)

- Two-tier previews: `build_quick()` for 10-line mobile summary, `build_full()` for detailed breakdowns.
- Quick preview must include order headline, leverage, capital usage, liquidation estimate, and risk indicator.
- Full preview expands with fee assumptions, what-if scenarios, and next-step suggestions.
- Always supply `set_order_details`, `set_capital_impact`, and `set_risk_assessment` before rendering.

### 6.3 Sortable Lists & Forms (`src/bot/components/lists.py`)

- Lists support sorting by risk, size, and PnL; grouping by urgency helps prioritise user attention.
- Renderers output markdown-friendly tables or enumerated lists tuned for Telegram readability.
- Keep mutation-free—methods return `self` for chaining but do not modify inputs in place.

## 7. Level 3 — Organism Patterns

### 7.1 Order Flow Orchestrator (`src/bot/components/flows/order_flow.py`)

- Handles start → leverage selection → preview → confirmation.
- Uses loading helpers around expensive service calls.
- Produces action-specific confirmations ("Buy $1,000 BTC") and registers undo timers when required.

### 7.2 Position Display (`src/bot/components/flows/position_display.py`)

- Lists positions sorted by risk; provides detail and empty states.
- Integrates list builders and cards to keep formatting uniform.

### 7.3 Risk Summary Modules

- Combine indicators, margin metrics, and recommendation buttons to guide users to safer actions (e.g., set stop loss).
- Always reference `RiskLevel` constants and shared copy.

## 8. Quick Preview Specification (SPEC-001)

```
📋 **Order Preview**

💰 {coin} {side} {side_emoji}: {format_currency(amount_usd)} @ {execution_hint}
⚡ Leverage: {leverage}x
📊 Margin: {format_currency(margin_req)} / {format_currency(margin_avail)} available
🎯 Liquidation: {format_currency(liq_price)} ({format_percentage(liq_dist, show_sign=False)} away)
⚠️ Risk: {risk_label} {risk_emoji}
```

- Buttons (full width each):
  1. `✅ {side_title} {format_currency(amount_usd)} {coin}` → confirmation callback.
  2. `📊 Full Details` → shows `build_full()` preview.
  3. `❌ Cancel` → aborts flow.
- Variations: replace `@ market` with limit price context; add "🔒 Reduce Only: Yes" when applicable.

## 9. Accessibility & Testing Guidelines

- Design for one-handed Telegram use; keep primary actions on the first row.
- Avoid markdown that Telegram renders inconsistently (e.g., nested bold/italic).
- When editing component output, update snapshot/unit tests to cover variations and edge cases.
- Provide fixture data that mirrors live API responses (nested structures, enums).
- Before shipping new flows, run manual checks on iOS (iPhone SE) and small Android devices.

## 10. Related Assets & Change Control

- Implementation tasks and migration plan: `docs/telegram-ux-implementation-playbook.md`.
- Historical references and rationale: `docs/archive/2025-12-07-ux/`.
- Any deviations from this guide require UX + engineering approval and must be recorded in the playbook change log.
