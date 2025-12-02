# Hyperbot Implementation Plan

**Last Updated**: 2025-11-29
**Current Phase**: ✅ All Phases Complete - Production Ready
**Progress Tracking**: See [TODO.md](TODO.md) for detailed task checklists and current progress

---

## Project Overview

Building a Python-based trading bot for Hyperliquid with multiple interfaces (Web Dashboard, Telegram Bot) that share a common service layer.

## Architecture

```
┌─────────────────────────────────────────┐
│        Core Services Layer              │
│        (Business Logic - UI Agnostic)   │
│                                          │
│  • AccountService                       │
│  • PositionService                      │
│  • OrderService                         │
│  • RebalanceService                     │
│  • ScaleOrderService                    │
│  • MarketDataService                    │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│        FastAPI REST API Layer           │
│        (Exposes all functionality)      │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────────┬───────┐
    ▼          ▼              ▼       ▼
┌────────┐  ┌──────────┐  ┌────────┐  ┌───┐
│Web UI  │  │ Telegram │  │Swagger │  │CLI│
│(Phase2)│  │(Phase 3) │  │  UI    │  │...│
└────────┘  └──────────┘  └────────┘  └───┘
```

---

## Implementation Phases

> **Note**: See [TODO.md](TODO.md) for detailed task checklists, implementation specifics, and progress tracking.

### ✅ Phase 0: Foundation
**Goal**: FastAPI project setup with modern Python tooling
**Duration**: 1 day
**Status**: ✅ Complete
**Deliverable**: Running FastAPI app with Swagger UI
**Key Decisions**:
- FastAPI over Flask (better async, auto-docs)
- `uv` package manager (10-100x faster than pip)

---

### ✅ Phase 1A: Core Services + API
**Goal**: Working REST API with all bot functionality testable via Swagger UI
**Duration**: 3-4 days
**Status**: ✅ Complete
**Deliverable**: Full-featured API for account, positions, orders, market data
**Key Decision**: Service layer pattern for UI-agnostic business logic
**Note**: Implements PERPS trading only. Spot support deferred to Phase 2C.

**Sub-phases**:
- **1A.1**: Configuration & Setup (settings, logger, env variables)
- **1A.2**: Hyperliquid Service Integration (SDK initialization, health checks)
- **1A.3**: Account Service (info, summary, balance - Perps + Spot)
- **1A.4**: Position Service (list, get, close, summary)
- **1A.5**: Order Service (market, limit, cancel - with critical error handling fix)
- **1A.6**: Market Data Service (1547 pairs, order books, metadata)
- **1A.7**: Testing Infrastructure (deferred - manual testing on testnet sufficient for now)

---

### ⛔ Phase 1B: Web Dashboard MVP
**Goal**: Functional web UI for account monitoring and position management
**Duration**: 5-6 hours
**Status**: ⛔ Not Planned - Telegram bot provides sufficient UI
**Decision**: Focus on mobile-first Telegram interface instead of web dashboard

---

### ✅ Phase 2A: Rebalancing Engine with Risk Management
**Goal**: Portfolio rebalancing with integrated risk assessment
**Duration**: 1 week
**Status**: ✅ Complete
**Deliverable**: Preview and execute rebalancing with risk warnings
**Key Achievement**: Dashboard matches Hyperliquid GUI metrics (Cross Margin Ratio: 3.63%)

**Features Delivered**:
- Risk Calculator Service (liquidation price, distance, health scores)
- Rebalancing Service (preview/execute modes, leverage management)
- Rebalance API endpoints (preview, execute, risk summary)
- Risk Visualization UI (Cross Margin Ratio, position-level risk badges)
- Comprehensive testing with live positions (99.96% portfolio value preservation)

---

### ✅ Phase 2B: Scale Orders & Advanced Trading
**Goal**: Place coordinated ladder orders at multiple price levels
**Duration**: 1 day
**Status**: ✅ Complete
**Deliverable**: Scale order API with preview, placement, tracking, cancellation

**Features Delivered**:
- Linear and geometric size distribution (configurable ratio 1.0-3.0)
- Preview before placement
- Group tracking with unique `scale_order_id`
- Fill percentage monitoring
- Atomic cancellation of order groups
- Price/size rounding for tick size compliance

**Example Usage**:
```bash
# Place 5 BTC buy orders from $108k to $106k with geometric distribution
curl -X POST '/api/scale-orders/place' -d '{
  "coin":"BTC", "is_buy":true, "total_size":0.01,
  "num_orders":5, "start_price":108000, "end_price":106000,
  "distribution_type":"geometric", "geometric_ratio":2.0
}'
```

---

### ✅ Phase 2D: Leverage Management Service
**Goal**: Centralized leverage management with validation and risk assessment
**Duration**: 1 day
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

## Future Phases (Planned)

> **Note**: See [TODO.md](TODO.md) for detailed planning of future phases.

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
💼 Positions
📋 Orders          ← New button
💰 Trade
⚙️ Settings
```

**Special Cases**:

1. **No orders**:
```
📭 No outstanding orders

You have no open orders at the moment.

[🔙 Back to Menu]
```

2. **Partially filled orders** (highlight):
```
📋 Partially Filled Orders (2)

1. 🟢 BUY Limit - BTC
   ├─ Price: $107,000
   ├─ Size: 0.05 BTC
   ├─ ⚡ Filled: 60% (0.03/0.05)  ← Highlighted
   └─ Remaining: 0.02 BTC
   [❌ Cancel Remaining]
```

3. **Bulk cancel confirmation**:
```
⚠️ Cancel All BTC Orders?

You are about to cancel 3 orders:
• 2 BUY limit orders
• 1 SELL limit order

Total value: $5,500

This action cannot be undone.

[✅ Yes, Cancel All] [❌ Keep Orders]
```

4. **Scale order grouping** (future enhancement):
```
📋 Scale Orders (2 groups)

🎯 Scale Group #abc123 - BTC BUY
   ├─ Orders: 5 (3 filled, 2 open)
   ├─ Progress: 60%
   └─ Range: $106k - $108k
   [📊 Details] [❌ Cancel All]
```

**Accessibility Considerations**:
- **Max 8 coin filter buttons** per row (Telegram limitation)
- **"More..." button** for additional coins (opens full list)
- **Order ID truncation** if displayed (show last 8 chars: `#...xyz123`)
- **Timestamp formatting**: Human-readable ("2h ago" vs ISO string)
- **Amount rounding**: Match Hyperliquid tick size rules

**Performance Optimization**:
- **Cache order data** for 30s (reduce API calls on filter changes)
- **Pagination** if >10 orders (show 10 at a time with Next/Prev)
- **Lazy load details**: Only fetch full order details when requested

**Technical Implementation Notes**:
- Use `info.openOrders()` from Hyperliquid SDK
- Reuse existing `OrderService` with new methods
- Add `ListOutstandingOrdersUseCase` in use case layer
- Reuse cancel logic from existing order cancellation
- Store `last_orders_filter` in `context.user_data` for back navigation

---

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

> **Note**: See [TODO.md](TODO.md) for testing lessons learned, known issues, and coverage by service.

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
- [TODO.md](TODO.md) - Detailed task tracking and progress

---

## Next Steps

> **Strategic Direction**: See [TODO.md](TODO.md) for detailed next steps and task planning.

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
