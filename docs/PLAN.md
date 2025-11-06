# Hyperbot Implementation Plan

**Last Updated**: 2025-11-06
**Current Phase**: ✅ Phase 4 Complete - Code Consolidation & Use Case Layer
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

### ✅ Phase 1B: Web Dashboard MVP
**Goal**: Functional web UI for account monitoring and position management
**Duration**: 5-6 hours
**Status**: ✅ Complete
**Deliverable**: Dashboard at `http://localhost:8000` with real-time updates
**Key Decisions**:
- **SSR (FastAPI + Jinja2)** vs SPA (simpler deployment, no CORS)
- **Tailwind CSS (CDN)** vs Bootstrap (modern, no build step)
- **HTMX** vs WebSockets (simpler, sufficient for 10s polling)
- **Alpine.js** vs React (minimal footprint for modals)

**Features Delivered**:
- Real-time account/position monitoring
- Individual position closing with confirmation
- Bulk close (33%/66%/100%) functionality
- Mobile-responsive design
- Auto-refresh every 10 seconds

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
- **Tests Passing**: 106 passed, 2 skipped
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

## Future Phases (Planned)

> **Note**: See [TODO.md](TODO.md) for detailed planning of future phases.

### Phase 1B.2: Post-MVP Dashboard Features (Optional)
**Goal**: Enhanced dashboard with orders, market data, charts
**Status**: Planned

### Phase 2C: Spot Trading Integration (Optional)
**Goal**: Add spot trading support (currently PERPS only)
**Status**: Planned

### Phase 3: Telegram Bot (Enhancement)
**Goal**: Mobile interface for trading and alerts
**Duration**: 4-5 days
**Status**: Planned
**Tech Stack**: python-telegram-bot library, reuses all services from Phase 1A

### Phase 1A.7: Testing Infrastructure (Optional)
**Goal**: Comprehensive test suite with fixtures
**Status**: Deferred (manual testnet testing sufficient)

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

**Current Status**: 106 tests passing, 2 skipped (25% coverage, target >80%)

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

**Completed**:
1. ✅ Phase 0: FastAPI setup
2. ✅ Phase 1A: Core Services + API
3. ✅ Phase 1B: Web Dashboard MVP
4. ✅ Phase 2A: Rebalancing Engine
5. ✅ Phase 2B: Scale Orders
6. ✅ Phase 2D: Leverage Management
7. ✅ Phase 4: Code Consolidation & Use Case Layer

**Options for Next Phase**:
- **Option A**: Phase 1B.2 - Post-MVP Dashboard Features (orders, market data, charts)
- **Option B**: Phase 2C - Spot Trading Integration
- **Option C**: Phase 3 - Telegram Bot Enhancement
- **Option D**: Phase 1A.7 - Testing Infrastructure (increase coverage from 25% to >80%)

**Recommendation**: Assess project priorities - Feature expansion (A/B), Mobile interface (C), or Technical debt (D)?
