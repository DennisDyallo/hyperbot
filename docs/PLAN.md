# Hyperbot Implementation Plan

**Last Updated**: 2025-12-06
**Current Focus**: 🚧 Phase 7 – Telegram UX Component Library
**Progress Source**: This document now consolidates roadmap, status, and task tracking.
**Reference Notes**: See [../CLAUDE.md](../CLAUDE.md) for notable learnings and testing insights.

---

## Project Overview

Building a Python-based trading bot for Hyperliquid with multiple interfaces (Web Dashboard, Telegram Bot) that share a common service layer.

## Architecture

See [docs/ARCHITECTURE.md](ARCHITECTURE.md) for the detailed layer diagram, background
worker topology, and cross-cutting concerns.

---

## Implementation Phases

> **Note**: Detailed task breakdowns live in the "Current Focus" and "Open Follow-ups" sections below.

### ✅ Phase 6: Outstanding Orders Management
**Status**: ✅ Complete (2025-11-29)
**Highlights**:
- Added `ListOrdersUseCase`, `CancelOrderUseCase`, and bulk cancellation support with comprehensive unit coverage.
- Exposed REST endpoints (`GET /api/orders/`, `DELETE /api/orders/{coin}/{order_id}`, `POST /api/orders/cancel-bulk`).
- Delivered Telegram `/orders` command with pagination, per-order cancellation, and bulk cancel actions.
**Follow-ups**:
- Implement coin-filter callback in `src/bot/handlers/orders.py` to enable the existing “Filter by coin” button (low priority).
**Status**: ✅ Complete
**Deliverable**: Leverage API with validation, estimation, soft limits

**Features Delivered**:
- Get/set leverage for any coin (with Hyperliquid limitation handling)
- Soft limit warnings (5x recommended, 6-10x warning, 10x+ extreme)
- Liquidation price estimation for planned positions
- Risk assessment (LOW/MODERATE/HIGH/EXTREME)
- Integration with rebalancing service
- Complete REST API endpoints

---

### ✅ Phase 4: Code Consolidation & Use Case Layer
**Goal**: Eliminate code duplication and establish single source of truth
**Duration**: 1 session (5 sub-phases)
**Status**: ✅ Complete
**Priority**: HIGH - Prevents technical debt and API/Bot divergence

**Architecture Achievement**: Use Case Layer for shared business logic

**Code Statistics**:
- **Use Cases Created**: 2,798 LOC (11 use cases across 4 categories)
- **Total Codebase**: 12,076 LOC
- **Tests Passing**: 532 passed (55% coverage)
- **Duplicate Code**: Eliminated (response parsers centralized)

**Use Cases Implemented**:
1. **Common Utilities** (`src/use_cases/common/`)
   - Response parser (centralized Hyperliquid parsing)
   - USD converter (unified conversion logic)
   - Validators (orders, portfolio, leverage)

2. **Trading Use Cases** (`src/use_cases/trading/`)
   - PlaceOrderUseCase (market/limit with validation)
   - ClosePositionUseCase (with risk checks)

3. **Portfolio Use Cases** (`src/use_cases/portfolio/`)
   - PositionSummaryUseCase (aggregate with risk metrics)
   - RiskAnalysisUseCase (portfolio/position assessment)
   - RebalanceUseCase (preview/execution)

4. **Scale Order Use Cases** (`src/use_cases/scale_orders/`)
   - PreviewScaleOrderUseCase (calculate levels/sizes)
   - PlaceScaleOrderUseCase (execute multiple orders)
   - ListScaleOrdersUseCase, GetScaleOrderStatusUseCase, CancelScaleOrderUseCase

**Benefits Achieved**:
- ✅ Single Source of Truth: Features implemented once, used everywhere
- ✅ No API/Bot Divergence: Shared business logic prevents feature drift
- ✅ Easier Testing: Use cases testable independently
- ✅ Faster Development: Add feature once, appears in multiple interfaces
- ✅ Better Maintainability: Update business logic in one place

---

### ✅ Phase 5: Order Fill Notifications (Real-time + Recovery)
**Goal**: Real-time Telegram notifications for all order fills with offline recovery
**Duration**: 2.5-3.5 weeks (13-18 days)
**Status**: ✅ Complete - Hybrid WebSocket + Polling implemented
**Priority**: HIGH - Critical for active trading monitoring

**Architecture**: Hybrid WebSocket + Smart Polling

```
OrderMonitorService
├── WebSocket Subscriber (real-time fills)
│   └── Subscribe to Hyperliquid userEvents
├── Recovery Manager (startup polling)
│   └── Query user_fills() for missed events
├── Periodic Backup Polling (every 5 min)
│   └── Safety net if WebSocket fails
└── Deduplication Layer
    └── Fill hash cache (prevent duplicates)
```

**Key Design Decisions**:
- **WebSocket Primary**: <1s notification latency for fills
- **Polling Recovery**: Back-notify missed fills after bot restart
- **Minimal State**: Only store `last_processed_timestamp` + deduplication hashes
- **Smart Batching**: Individual notifications for ≤5 fills, summary for >5
- **Stateless Where Possible**: Rely on Hyperliquid API for state reconstruction

**State Persistence** (`data/notification_state.json`):
```json
{
  "last_processed_timestamp": "2025-11-12T14:23:45Z",
  "recent_fill_hashes": ["abc123...", "def456...", ...],
  "last_websocket_heartbeat": "2025-11-12T14:25:00Z",
  "websocket_reconnect_count": 2
}
```

**Notification Format Example**:
```
🎯 Limit Order Filled!

Coin: BTC
Side: BUY 📈
Size: 0.5 BTC
Avg Price: $67,850.00
Total Value: $33,925.00
Time: 2025-11-12 14:23:45 UTC

💰 Position opened at 3x leverage
```

**Sub-phases**:
- **5A**: Foundation + Learning Tests (3-4 days)
  - Integration tests to learn Hyperliquid WebSocket/fills APIs
  - Create models (NotificationState, OrderFillEvent)
  - Service skeletons

- **5B**: WebSocket Implementation (4-5 days)
  - WebSocket connection and subscription
  - Real-time fill event processing
  - Reconnection logic
  - Unit tests

- **5C**: Recovery Mechanism (3-4 days)
  - Startup recovery (query missed fills)
  - Periodic backup polling
  - Batch notifications for >5 fills
  - Unit tests

- **5D**: Telegram Integration (2-3 days)
  - Bot integration (post_init/post_shutdown)
  - Notification commands (/notify_status, /notify_test, /notify_history)
  - End-to-end testing

- **5E**: Scale Order Enhancement (1-2 days)
  - Aggregate notifications for scale order groups
  - "3/5 orders filled (60%)" format
  - User preferences

**Success Metrics**:
- ✅ 100% fill delivery (no missed notifications)
- ✅ 0% duplicate notifications
- ✅ <1s WebSocket notification latency
- ✅ <5min recovery notification after restart
- ✅ Handles 100+ fills/day reliably

**Development Approach**: Test-Driven Development
1. Write integration tests first (learn API behavior)
2. Implement code to make tests pass
3. Add comprehensive unit tests

---

## Current Focus: Phase 7 – Telegram UX Component Library

**Goal**: Deliver leverage-aware order flows and a reusable Telegram UX component set that improves capital transparency and reduces handler duplication.
**Status**: 🚧 In progress (`feature/ux-component-library`)
**Priority**: HIGH – UX team blocker for safer trading flows

### UX Pillars
- Progressive disclosure: quick previews by default with full detail on demand
- Mobile-first: enforce the 10-line quick preview constraint for small screens
- Context-aware guidance: leverage labels, action-forward button copy
- Safety through transparency: surface margin usage, buying power, liquidation range

### Active Workstreams
- **Atomic components**: add navigation presets plus remaining spec-alignment helpers for `ButtonBuilder`; expand risk indicator API with tooltips and descriptive levels.
- **Organism flows**: finish orchestration API (`start`, `handle_*`) so handlers can adopt flows without glue code; add integration tests that exercise complete market and position journeys with the new components.
- **Migration & adoption**: refactor `wizard_market_order.py`; migrate scale, rebalance, and close-position wizards; retrofit `/positions`, `/orders`, and `/account`; replace legacy menu builders with `ButtonBuilder`; enforce consistent loading and success templates.
- **Testing & docs**: rerun `uv run pytest` after integrations to keep ≥90% coverage in component modules; add end-to-end bot tests for quick/full preview toggles and success follow-ups; document usage patterns and migration notes in README and internal docs.
- **Design references**: Implement UX exactly as specified in `docs/UX_DESIGN_SPECIFICATIONS.md` (component formatting, spacing, button patterns) and prioritize the overhaul sequence documented in `docs/UX_IMPROVEMENT_OPPORTUNITIES.md`.
- **Margin mode selection**: Extend leverage-aware flows so traders choose cross vs isolated margin during order entry, with previews updating capital usage and liquidation math per mode.

### Known Gaps & Follow-ups
- Instantiate `ButtonBuilder` per reply to prevent shared state leakage.
- Align preview helper keyword arguments (`account_value`, `is_testnet`) with call sites.
- Add risk grouping plus action buttons to sortable lists per SPEC-004.
- Trim `PositionDisplay` quick view output to the 10-line mobile guideline.
- Extend success messages with "What's next?" action buttons for continuity.

### Implementation Notes
- Components must expose builders (text, keyboards, loading states) while ConversationHandler continues orchestrating flow control.
- Inline leverage selection should feed preview builders that show margin required, available buying power, liquidation estimates, and risk scoring before confirmation.
- Reuse service-layer calculations to validate buying power in real time as leverage and order size change.
- Margin mode selection must integrate with leverage steps—defaulting to cross, allowing isolated where supported, and updating previews with per-mode margin consumption and liquidation ranges.

### Success Metrics
- Inline leverage selection available for market, limit, and scale order wizards.
- Each preview surfaces margin required, buying power remaining, liquidation range, chosen margin mode, and risk level.
- Position views display liquidation distance and stop-loss status for every open position.
- Component modules maintain ≥90% unit-test coverage after refactors.

### Immediate Next Steps
1. Ship navigation preset helpers and the expanded risk indicator API.
2. Finalize the order-flow orchestrator surface and wire it into the market order wizard.
3. Introduce leverage-aware previews in the market flow, then propagate to remaining wizards.
4. Run the full test suite and publish migration guidance in README and Claude notes.

### Open Follow-ups (User Feedback – Dec 2025)
Source: [docs/user-feedback.md](../docs/user-feedback.md)

- **P0 · Restore critical commands**: `/close <coin>`, `/balance`, `/notifystatus`, and `/notifyhistory` currently return "Unknown command." Re-register handlers and update `/help` so published commands work.
- **P0 · Fill price gaps for unlisted spot tokens**: Resolve account valuation warnings when Hyperliquid omits tokens like JEFF/POINTS/OMNIX/UBTC/LICKO to keep mainnet balance totals accurate.
- **P0 · Reduce bot latency**: Audit RPC usage, caching, and batching to address slow command responses highlighted by traders.
- **P1 · Close-position UX upgrades**: Add quick buttons to close 100%/50%/25% of all positions, allow per-position selection, and surface a "Close Positions" shortcut from the main positions menu.
- **P1 · Partial stop-loss tooling**: Support percentage-based, reduce-only stop market orders so users can protect positions without full exits.
- **P2 · Order history pagination**: Provide a paginated history view with "load more" controls for older fills.
- **P2 · Open orders pagination enhancement**: Extend `/orders` to paginate beyond the first page so large books remain navigable.
---

## Future Phases (Planned)

> **Note**: Additional roadmap items are summarized here; expand details inline as they are scheduled.

### 📋 Phase 6: Outstanding Orders Management
**Goal**: List, filter, and manage all outstanding (open/unfilled) orders
**Status**: 📋 Planned
**Priority**: MEDIUM - Useful for order visibility and management
**Duration**: 1-2 days

**Scope**:
- List all outstanding orders (open/partially filled)
- Filter by coin, side (buy/sell), order type (limit/stop)
- Display order details (price, size, filled amount, timestamp)
- Cancel individual or bulk orders
- Integration with Telegram bot (/orders command)
- REST API endpoints

**User Stories**:
- As a trader, I want to see all my open orders to understand my active exposure
- As a trader, I want to filter orders by coin to focus on specific positions
- As a trader, I want to cancel multiple orders at once to quickly adjust strategy

**API Endpoints** (Planned):
```
GET  /api/orders/outstanding          # List all outstanding orders
GET  /api/orders/outstanding/{coin}   # Filter by coin
POST /api/orders/cancel/{order_id}    # Cancel single order
POST /api/orders/cancel-bulk          # Cancel multiple orders
```

---

#### Telegram UX Design

**Philosophy**: Follow established patterns from `/positions` command and wizards
- **Mobile-first**: Concise messages, emoji indicators, progressive disclosure
- **Interactive buttons**: Inline keyboards for filtering and actions
- **Clear hierarchy**: Overview → Details → Actions
- **Error prevention**: Confirmation dialogs for destructive actions

**Command Pattern**:
```
/orders                    # List all outstanding orders (main menu button)
/orders BTC                # Filter by coin (quick command)
```

**Message Flow** (3-level hierarchy):

**Level 1: Orders Overview**
```
📋 Outstanding Orders (7)

🟢 BUY Orders: 4
🔴 SELL Orders: 3

Filter by:
[All] [BTC] [ETH] [SOL] [More...]

[📊 View All] [🗑️ Cancel All] [🔙 Back]
```

**Level 2: Filtered/Detailed List** (when coin selected or "View All" pressed)
```
📋 BTC Orders (3)

1. 🟢 BUY Limit
   ├─ Price: $108,500
   ├─ Size: 0.01 BTC ($1,085)
   ├─ Filled: 0% (0/0.01)
   └─ Created: 2h ago
   [❌ Cancel]

2. 🟢 BUY Limit
   ├─ Price: $107,000
   ├─ Size: 0.02 BTC ($2,140)
   ├─ Filled: 50% (0.01/0.02)
   └─ Created: 30m ago
   [❌ Cancel]

[🗑️ Cancel All BTC] [🔙 Back]
```

**Level 3: Individual Order Actions** (callback from Cancel button)
```
⚠️ Confirm Cancel Order

Coin: BTC
Side: BUY 🟢
Type: Limit
Price: $108,500
Size: 0.01 BTC
Filled: 0%

Cancel this order?

[✅ Yes, Cancel] [❌ No, Keep]
```

**UX Patterns Used** (consistency with existing features):
- **Emoji indicators**: Same as `/positions` (🟢 BUY/LONG, 🔴 SELL/SHORT)
- **Tree structure**: `├─` and `└─` for nested info (from positions display)
- **Progressive disclosure**: Overview → Details → Confirmation (like market order wizard)
- **Inline keyboards**: Interactive buttons for all actions (standard pattern)
- **Loading states**: "⏳ Fetching orders..." (consistent with all commands)
- **Error handling**: "❌ Failed to fetch orders: {error}" with retry option

**Main Menu Integration**:
```
Main Menu updates:
📊 Account
### ⛔ Phase 1B.2: Post-MVP Dashboard Features
**Goal**: Enhanced dashboard with orders, market data, charts
**Status**: ⛔ Not Planned - Web dashboard abandoned in favor of Telegram

### ✅ Phase 2C: Spot Trading Integration
**Goal**: Add spot trading support (currently PERPS only)
**Status**: ✅ Complete - Spot trading fully supported

### ✅ Phase 3: Telegram Bot (Enhancement)
**Goal**: Mobile interface for trading and alerts
**Duration**: 4-5 days
**Status**: ✅ Complete - Full interactive Telegram bot with wizards
**Tech Stack**: python-telegram-bot library, reuses all services from Phase 1A

**Features Delivered**:
- Interactive trading wizards (market orders, scale orders)
- Position management (/positions, /close)
- Portfolio rebalancing wizard
- Order fill notifications (real-time + recovery)
- Account monitoring (/account, /balance)
- Leverage management

### ✅ Phase 1A.7: Testing Infrastructure
**Goal**: Comprehensive test suite with fixtures
**Status**: ✅ Complete - 55% test coverage with 532 passing tests

---

## Testing Strategy

### High-Level Philosophy

**Critical Operations** (Must Test):
- Order validation (size, side, type)
- Position closing validation
- Rebalancing calculations
- Scale order distributions

**Testing Layers**:
- **Unit Tests**: Fast tests with mocked Hyperliquid API, focus on validation logic
- **Integration Tests**: Real testnet API, verify connectivity, run before releases
- **Manual Tests**: Critical operations on testnet before mainnet

**Test Commands**:
```bash
# Unit tests only (fast)
uv run pytest tests/ -m "not integration"

# Integration tests (requires testnet)
uv run pytest tests/integration/ -v

# All tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

**Current Status**: 532 tests passing (55% coverage, target >80%)

> **Note**: Testing lessons, coverage history, and known issues are tracked in [../CLAUDE.md](../CLAUDE.md) under "Notable Learnings".

---

## Decision Log (Architecture Decision Records)

### Decision 1: FastAPI over Flask
**When**: Phase 0
**Context**: Need modern web framework with auto-documentation
**Decision**: Use FastAPI
**Rationale**:
- Auto-generated API docs (Swagger UI) - critical for testing
- Native async support (better for I/O-bound trading operations)
- Better type hints integration
- Modern and actively maintained

**Status**: ✅ Validated - Swagger UI has been invaluable for development

---

### Decision 2: Web Dashboard before Telegram Bot
**When**: Planning phase
**Context**: Need to choose first user interface
**Decision**: Build Web Dashboard first, Telegram later
**Rationale**:
- Better for development and testing (visual feedback)
- Can test complex scenarios more easily (multiple positions, bulk operations)
- Telegram can be added later as additional interface (service layer is UI-agnostic)

**Status**: ✅ Validated - Dashboard accelerated development, Telegram will reuse all services

---

### Decision 3: Use `uv` instead of `pip`
**When**: Phase 0
**Context**: Need reliable dependency management
**Decision**: Use `uv` package manager
**Rationale**:
- 10-100x faster than pip (Rust-based)
- Lockfile support (reproducible installs)
- Automatic virtual environment management
- Modern tooling with better error messages

**Status**: ✅ Validated - Dependency management has been smooth

---

### Decision 4: Service Layer Pattern
**When**: Planning phase
**Context**: Need to support multiple interfaces (Web, Telegram, CLI)
**Decision**: Implement service layer for UI-agnostic business logic
**Rationale**:
- Easy to add multiple interfaces (Web, Telegram, CLI)
- Better testability (test services independently)
- Clear separation of concerns (business logic vs presentation)
- Enables code reuse

**Status**: ✅ Validated - Phase 4 Use Case Layer built on this foundation

---

### Decision 8: Hybrid WebSocket + Polling for Order Fill Notifications
**When**: Phase 5 (Order Fill Notifications)
**Context**: Need reliable fill notifications with recovery capability after bot downtime
**Decision**: Hybrid architecture with WebSocket primary + polling recovery
**Alternatives Considered**:
- Pure WebSocket (no recovery for offline periods)
- Pure polling (higher latency, more API usage)
- WebSocket with message queue persistence (complex infrastructure)

**Rationale**:
- **Real-time performance**: WebSocket provides <1s notification latency
- **Reliability**: Polling recovery ensures no fills missed during downtime
- **API efficiency**: WebSocket reduces continuous polling overhead
- **Minimal complexity**: No message queue infrastructure needed
- **Stateless recovery**: Can reconstruct state from Hyperliquid API

**Implementation Details**:
- Primary: WebSocket subscription to `userEvents` (real-time)
- Recovery: On startup, query `user_fills(start_time)` for missed events
- Backup: 5-minute periodic polling as safety net
- Deduplication: Fill hash cache prevents duplicate notifications
- State: Only persist `last_processed_timestamp` + recent hashes

**Consequences**:
- ✅ Best of both worlds (real-time + reliability)
- ✅ Simple state management (minimal persistence)
- ✅ Graceful degradation (polling if WebSocket fails)
- ✅ WebSocket reconnection logic implemented
- ✅ State persistence in `data/notification_state.json`

**Status**: ✅ Complete - Production ready (Nov 29, 2025)

---

### Decision 5: SSR with HTMX vs SPA
**When**: Phase 1B (Web Dashboard)
**Context**: Need dynamic UI for position monitoring
**Decision**: Server-Side Rendering with HTMX
**Alternatives Considered**: React/Vue SPA, Next.js
**Rationale**:
- **Single deployment** (no separate frontend server, no CORS)
- **Faster initial load** (HTML rendered server-side)
- **Simpler workflow** (no build step, no bundler)
- **Progressive enhancement** (works without JavaScript)
- **HTMX sufficient** for 10-second polling (WebSockets overkill for MVP)

**Status**: ✅ Validated - Dashboard is fast and simple to maintain

---

### Decision 6: Tailwind CSS (CDN) vs Bootstrap
**When**: Phase 1B (Web Dashboard)
**Context**: Need responsive styling system
**Decision**: Tailwind CSS via CDN
**Alternatives Considered**: Bootstrap, custom CSS, Tailwind with build
**Rationale**:
- **Utility-first approach** (rapid prototyping)
- **No build step** with CDN (simpler deployment)
- **Modern and responsive** by default
- **Small bundle size** with JIT mode

**Status**: ✅ Validated - Fast UI development, clean code

---

### Decision 7: Use Case Layer Architecture
**When**: Phase 4
**Context**: Code duplication between API and Bot interfaces
**Decision**: Implement Use Case Layer with centralized utilities
**Rationale**:
- **Single Source of Truth** (business logic in one place)
- **Prevent Divergence** (API and Bot stay in sync automatically)
- **Easier Testing** (use cases testable independently)
- **Faster Development** (add feature once, appears everywhere)

**Status**: ✅ Validated - Eliminated 23 duplicate code blocks, 2,798 LOC in use cases

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hyperliquid SDK](../docs/hyperliquid/python-sdk.md)
- [Hyperliquid API Reference](../docs/hyperliquid/api-reference.md)
- [Testing Strategy](../docs/TESTING.md) (to be created)
- [../CLAUDE.md](../CLAUDE.md) - Notable learnings, testing patterns, and coverage notes
- [docs/UX_DESIGN_SPECIFICATIONS.md](../docs/UX_DESIGN_SPECIFICATIONS.md) - Pixel-perfect Telegram message and component specs
- [docs/UX_IMPROVEMENT_OPPORTUNITIES.md](../docs/UX_IMPROVEMENT_OPPORTUNITIES.md) - Flow-by-flow UX upgrade roadmap

---

## Next Steps

> **Strategic Direction**: Active planning lives in the "Current Focus" and "Future Enhancements" sections above.

**Completed Phases**:
1. ✅ Phase 0: FastAPI setup
2. ✅ Phase 1A: Core Services + API
3. ✅ Phase 2A: Rebalancing Engine
4. ✅ Phase 2B: Scale Orders
5. ✅ Phase 2C: Spot Trading Integration
6. ✅ Phase 2D: Leverage Management
7. ✅ Phase 3: Telegram Bot (Full Implementation)
8. ✅ Phase 4: Code Consolidation & Use Case Layer
9. ✅ Phase 5: Order Fill Notifications
10. ✅ Phase 1A.7: Testing Infrastructure (63% coverage)
11. ✅ Phase 6: Outstanding Orders Management

**Future Enhancements**:
- 📋 Phase 7: Leverage-Aware Order Placement & Capital Transparency (NEXT)
- 📋 Phase 8: Additional features (order modification, analytics, filter by coin completion)

**Not Planned**:
- ⛔ Phase 1B: Web Dashboard (abandoned - Telegram bot is primary interface)
- ⛔ Phase 1B.2: Post-MVP Dashboard Features

**Project Status**: Production ready with comprehensive order management
**Current Build**: 705 tests passing, 63% coverage, all core features operational
**Next Priority**: Tech debt (Pydantic V2 migration) or new feature requests
