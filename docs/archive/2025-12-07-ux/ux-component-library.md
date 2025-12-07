# UX Component Library Implementation

**Epic**: Reusable Telegram Bot UX Components
**Branch**: `feature/ux-component-library`
**Priority**: High
**Estimated Effort**: 4 weeks

## 📋 Overview

Implement a comprehensive component library for Telegram bot interactions to ensure consistency, maintainability, and professional UX across all flows.

**Related Documentation**:
- [TELEGRAM_UX_COMPONENT_LIBRARY.md](docs/TELEGRAM_UX_COMPONENT_LIBRARY.md) - Component specifications
- [COMPONENT_IMPLEMENTATION_GUIDE.md](docs/COMPONENT_IMPLEMENTATION_GUIDE.md) - Developer guide
- [UX_DESIGN_SPECIFICATIONS.md](docs/UX_DESIGN_SPECIFICATIONS.md) - Design specs
- [UX_IMPROVEMENT_OPPORTUNITIES.md](docs/UX_IMPROVEMENT_OPPORTUNITIES.md) - Flow analysis

## 🎯 Goals

- ✅ Create reusable components for common UX patterns
- ✅ Reduce code duplication across handlers (currently ~40% duplicate formatting)
- ✅ Ensure consistent formatting, spacing, emoji usage
- ✅ Improve mobile UX with two-tier previews
- ✅ 90% test coverage for all components

## 📦 Implementation Checklist

### Phase 1: Level 1 - Atomic Components (Week 1)

#### Formatters (`src/bot/components/formatters.py`)
- [ ] `format_currency(value: float, show_sign: bool = False) -> str`
- [ ] `format_percentage(value: float, decimals: int = 1, show_sign: bool = True) -> str`
- [ ] `format_coin_size(size: float, coin: str) -> str`
- [ ] `format_pnl(pnl_usd: float, pnl_pct: float) -> str` with emoji
- [ ] `format_timestamp(dt: datetime) -> str`
- [ ] Unit tests for all formatters (edge cases: zero, negative, very large)

#### Buttons (`src/bot/components/buttons.py`)
- [ ] `ButtonBuilder` class
  - [ ] `action(label: str, callback: str, style: str = "primary") -> Self`
  - [ ] `cancel(label: str = "❌ Cancel") -> Self`
  - [ ] `back(label: str = "🔙 Back") -> Self`
  - [ ] `build() -> list[list[InlineKeyboardButton]]`
- [ ] `build_action_button(text: str, callback: str) -> InlineKeyboardButton`
- [ ] `build_navigation_row() -> list[InlineKeyboardButton]`
- [ ] Unit tests for button layouts (1, 2, 3, 4 button variations)

#### Loading States (`src/bot/components/loading.py`)
- [ ] `LoadingMessage` class
  - [ ] `show(update: Update, action: str, **kwargs) -> Message`
  - [ ] `hide(message: Message) -> None`
- [ ] Pre-defined loading messages (order, price, leverage, etc.)
- [ ] Unit tests for loading state display

#### Risk Indicators (`src/bot/components/risk.py`)
- [ ] `RiskLevel` enum (SAFE, LOW, MODERATE, HIGH, CRITICAL, EXTREME)
- [ ] `calculate_risk_level(liq_distance_pct: float, leverage: int) -> RiskLevel`
- [ ] `get_risk_emoji(level: RiskLevel) -> str`
- [ ] `format_risk_indicator(level: RiskLevel) -> str`
- [ ] Unit tests for risk calculations

### Phase 2: Level 2 - Molecular Components (Week 2)

#### Info Cards (`src/bot/components/cards.py`)
- [ ] `InfoCard` class
  - [ ] `add_field(label: str, value: str) -> Self`
  - [ ] `add_separator() -> Self`
  - [ ] `render() -> str`
- [ ] `build_capital_impact_card(margin_req, margin_avail, bp_used) -> InfoCard`
- [ ] `build_risk_assessment_card(entry, liq, liq_dist, leverage) -> InfoCard`
- [ ] Unit tests for card rendering

#### Preview Builder (`src/bot/components/preview.py`)
- [ ] `PreviewBuilder` class
  - [ ] `set_order_details(coin, side, amount, leverage) -> Self`
  - [ ] `set_capital_impact(...) -> Self`
  - [ ] `set_risk_assessment(...) -> Self`
  - [ ] `build_quick() -> str` (mobile-optimized, 10 lines max)
  - [ ] `build_full() -> str` (comprehensive)
- [ ] Unit tests for both preview tiers

#### Sortable List (`src/bot/components/lists.py`)
- [ ] `SortableList` class
  - [ ] `add_item(item: dict) -> Self`
  - [ ] `sort_by_risk() -> Self`
  - [ ] `sort_by_size() -> Self`
  - [ ] `sort_by_pnl() -> Self`
  - [ ] `group_by_urgency() -> dict`
  - [ ] `render() -> str`
- [ ] Unit tests for sorting and grouping

### Phase 3: Level 3 - Organism Flows (Week 3)

#### Order Flow Orchestrator (`src/bot/components/flows/order_flow.py`)
- [ ] `OrderFlowOrchestrator` class
  - [ ] `start(update, context) -> str`
  - [ ] `handle_leverage_selection(update, context) -> str`
  - [ ] `handle_preview(update, context) -> str`
  - [ ] `handle_confirmation(update, context) -> str`
- [ ] Integration tests for complete flow

#### Position Display (`src/bot/components/flows/position_display.py`)
- [ ] `PositionDisplay` class
  - [ ] `render_list(positions: list) -> str`
  - [ ] `render_detail(position: dict) -> str`
  - [ ] `render_empty_state() -> str`
- [ ] Integration tests with mock position data

### Phase 4: Migration & Testing (Week 4)

#### Refactor Existing Handlers
- [ ] Market order wizard → use new components
- [ ] Positions view → use SortableList + PositionDisplay
- [ ] Scale order wizard → simplify with OrderFlowOrchestrator
- [ ] Rebalance wizard → use PreviewBuilder

#### Testing
- [ ] Unit tests: 90% coverage for all components
- [ ] Integration tests: End-to-end flow testing
- [ ] Manual testing: Mobile UX verification (iPhone SE, Android)
- [ ] Performance testing: Button response times <500ms

#### Documentation
- [ ] Update README with component usage examples
- [ ] Add inline docstrings to all public methods
- [ ] Create migration guide for other developers

## 📊 Success Metrics

- [ ] Code duplication reduced by 50%+
- [ ] 90%+ test coverage on components
- [ ] All wizards use consistent formatting
- [ ] Mobile preview fits on screen (≤10 lines)
- [ ] No UX regressions (user testing)

## 🔗 Dependencies

- `python-telegram-bot` >= 20.0
- Existing service layer (`src/services/`)
- Pytest for testing

## 🚀 Deployment Plan

1. Merge to `main` after PR approval
2. Deploy to staging environment
3. Monitor for 48 hours
4. Gradual rollout to production (10% → 50% → 100%)
5. Collect user feedback

## 📝 Notes

- All components should be stateless where possible
- Use type hints throughout
- Follow existing code style (Black formatter)
- Mobile-first design approach
- Keep backward compatibility during migration

---

**Assignee**: TBD
**Reviewers**: UX Team, Backend Team
**Labels**: `enhancement`, `ux`, `telegram-bot`, `refactor`
