# Hyperbot Implementation Plan

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
└──────────────────┬──────────────────────┘
                   │
┌──────────────────┴──────────────────────┐
│        FastAPI REST API Layer           │
│        (Exposes all functionality)      │
└──────────────────┬──────────────────────┘
                   │
    ┌──────────────┼──────────────┬───────┐
    ▼              ▼              ▼       ▼
┌────────┐  ┌──────────┐  ┌────────┐  ┌───┐
│Web UI  │  │ Telegram │  │Swagger │  │CLI│
│(Phase2)│  │(Phase 3) │  │  UI    │  │...│
└────────┘  └──────────┘  └────────┘  └───┘
```

## Implementation Phases

### ✅ Phase 0: Foundation (Completed)
- [x] FastAPI minimal setup
- [x] Health check endpoints
- [x] Swagger UI auto-documentation
- [x] Migrate to `uv` package manager
- [x] Project structure

### ✅ Phase 1A: Core Services + API (100% Complete)

**Goal**: Working REST API with all bot functionality testable via Swagger UI
**Note**: This phase implements **PERPS trading only**. Spot support will be added in Phase 2.

**Sub-phases:**

#### ✅ 1A.1: Configuration & Setup (Complete)
- [x] Create `src/config/settings.py`
- [x] Load environment variables with python-dotenv
- [x] Create `src/config/logger.py` with loguru
- [x] Test configuration loading

#### ✅ 1A.2: Hyperliquid Service Integration (Complete)
- [x] Create `src/services/hyperliquid_service.py`
- [x] Initialize Hyperliquid SDK with proper wallet creation
- [x] Test connection to testnet
- [x] Implement health check with Hyperliquid status
- [x] Create manual test scripts

#### ✅ 1A.3: Account Service (Complete)
- [x] Create `src/services/account_service.py`
- [x] Implement `get_account_info()` (Perps + Spot)
- [x] Implement `get_account_summary()`
- [x] Implement `get_balance_details()`
- [x] Create API endpoints: `GET /api/account/info`, `GET /api/account/summary`
- [x] Test with real testnet

#### ✅ 1A.4: Position Service (Complete)
- [x] Create `src/services/position_service.py`
- [x] Implement `list_positions()`
- [x] Implement `get_position()`
- [x] Implement `close_position()` with error handling
- [x] Implement `get_position_summary()`
- [x] Create API endpoints:
  - `GET /api/positions/`
  - `GET /api/positions/summary`
  - `GET /api/positions/{symbol}`
  - `POST /api/positions/{symbol}/close`
- [x] Test position closing on testnet

#### ✅ 1A.5: Order Service (Complete)
- [x] Create `src/services/order_service.py`
- [x] Implement `place_market_order()` with error handling
- [x] Implement `place_limit_order()` with error handling
- [x] Implement `list_open_orders()`
- [x] Implement `cancel_order()` with error handling
- [x] Implement `cancel_all_orders()` with error handling
- [x] Create API endpoints:
  - `GET /api/orders/`
  - `POST /api/orders/market`
  - `POST /api/orders/limit`
  - `DELETE /api/orders/{coin}/{order_id}`
  - `DELETE /api/orders/all`
- [x] Test order placement on testnet
- [x] Fix critical error handling bug (Hyperliquid response parsing)
- [x] Create comprehensive test suite

#### ✅ 1A.6: Market Data Service (Complete)
- [x] Create `src/services/market_data_service.py`
- [x] Implement `get_all_prices()` (1547 trading pairs)
- [x] Implement `get_price(symbol)` with validation
- [x] Implement `get_market_info()` (exchange metadata)
- [x] Implement `get_order_book(coin)` (L2 snapshots)
- [x] Implement `get_asset_metadata(coin)` (tick sizes, leverage)
- [x] Create API endpoints:
  - `GET /api/market/prices`
  - `GET /api/market/price/{symbol}`
  - `GET /api/market/info`
  - `GET /api/market/orderbook/{coin}`
  - `GET /api/market/asset/{coin}`
- [x] Test with real testnet data

#### 1A.7: Testing Infrastructure
- [ ] Create `pytest.ini`
- [ ] Create `tests/conftest.py` with fixtures
- [ ] Write critical unit tests for order validation
- [ ] Write critical unit tests for position management
- [ ] Write integration tests for testnet
- [ ] Create test runner script
- [ ] Document testing approach

**Duration**: 3-4 days
**Deliverable**: Working API with all bot functionality, testable via Swagger UI

---

### ✅ Phase 1B: Web Dashboard MVP (COMPLETE)

**Goal**: Functional web UI for account monitoring and position management

**Status**: MVP Complete - Dashboard with real-time position monitoring and bulk close functionality

**Strategy**: Build MVP first (view + close positions), defer advanced features to Phase 1B.2

---

#### Tech Stack Decisions

**Server-Side Rendering (SSR) - Monolithic Approach**
- **Selected**: FastAPI + Jinja2 templates (same app as API)
- **Reasoning**:
  - Single deployment target (no separate frontend server)
  - No CORS complications
  - Faster initial page load (HTML rendered server-side)
  - Simpler development workflow
  - Progressive enhancement (works without JavaScript)
- **Alternatives Considered**:
  - Separate React/Vue SPA: More complex, requires build step, separate deployment
  - Next.js: Overkill for simple dashboard, adds Node.js dependency

**Styling - Tailwind CSS (CDN)**
- **Selected**: Tailwind CSS via CDN
- **Reasoning**:
  - Utility-first approach (rapid prototyping)
  - No build step required with CDN
  - Modern, responsive by default
  - Small bundle size with JIT mode
- **Alternatives Considered**:
  - Bootstrap: More opinionated, heavier, less modern
  - Custom CSS: Slower development, more maintenance
  - Tailwind with build: Unnecessary complexity for MVP

**Dynamic Updates - HTMX**
- **Selected**: HTMX for auto-refresh and partial updates
- **Reasoning**:
  - HTML-driven (declarative, minimal JavaScript)
  - Perfect for server-side rendering
  - Auto-refresh with polling (simple implementation)
  - Small library size (~14KB)
  - Progressive enhancement friendly
- **Alternatives Considered**:
  - WebSockets: More complex, overkill for 10-second polling
  - React/Vue: Requires full SPA, separate build pipeline
  - Vanilla JS fetch(): More boilerplate, manual DOM manipulation

**Interactivity - Alpine.js**
- **Selected**: Alpine.js for modals and UI state
- **Reasoning**:
  - Minimal footprint (~15KB)
  - Declarative syntax (like Vue, but lighter)
  - Perfect for modals, dropdowns, confirmations
  - Works seamlessly with HTMX
- **Alternatives Considered**:
  - Vanilla JS: More verbose, harder to maintain
  - jQuery: Outdated, larger bundle
  - Full framework (React/Vue): Overkill for simple interactions

**Dependencies to Add**:
```toml
jinja2 = ">=3.1.4"           # Template engine
python-multipart = ">=0.0.9" # Form handling
```

**CDN Resources** (No build step needed):
```html
<!-- Tailwind CSS -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- HTMX -->
<script src="https://unpkg.com/htmx.org@1.9.10"></script>

<!-- Alpine.js -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

---

#### MVP (Now) - Estimated: 5-6 hours

**Goal**: View account/positions + Close positions (individual & bulk)

**MVP.1: Foundation Setup** (30 min)
- Add dependencies: `jinja2`, `python-multipart`
- Create directory structure:
  ```
  src/api/templates/
    - base.html
    - dashboard.html
    - positions.html
  src/static/css/
    - custom.css
  ```
- Configure static files in `main.py`:
  ```python
  from fastapi.staticfiles import StaticFiles
  from fastapi.templating import Jinja2Templates

  app.mount("/static", StaticFiles(directory="src/static"), name="static")
  templates = Jinja2Templates(directory="src/api/templates")
  ```
- Create `base.html` with:
  - Tailwind CSS CDN
  - HTMX CDN
  - Alpine.js CDN
  - Basic navbar component
  - Common layout structure
- Create `src/api/routes/web.py` for HTML routes
- Test: Render basic page at http://localhost:8000

**MVP.2: Dashboard Page** (1 hour)
- Create `dashboard.html` template
- Add `GET /` route → renders dashboard
- Implement cards:
  - **Account Summary Card**:
    - Total Balance (USDC)
    - Account Equity
    - Margin Used
    - Available Margin
  - **Positions Summary Widget**:
    - Total Open Positions
    - Long/Short breakdown
    - Total Unrealized PnL (with color: green profit, red loss)
- Use HTMX for auto-refresh every 10 seconds:
  ```html
  <div hx-get="/api/account/summary" hx-trigger="every 10s" hx-swap="innerHTML">
    <!-- Content auto-refreshes -->
  </div>
  ```
- Responsive grid layout (Tailwind grid classes)
- Test: Dashboard shows live account data

**MVP.3: Positions Table** (1.5 hours)
- Create `positions.html` template
- Add `GET /positions` route (renders HTML page)
- Implement positions table with columns:
  - Coin (symbol)
  - Side (Long/Short with color badges)
  - Size (amount)
  - Entry Price
  - Current Price
  - Position Value (USDC)
  - Unrealized PnL (USDC)
  - Unrealized PnL% (percentage)
  - Leverage (e.g., "5x")
  - Actions (Close button)
- Color coding:
  - Green text for profit positions
  - Red text for loss positions
  - Green badge for Long, Red badge for Short
- Empty state handling: "No open positions"
- HTMX auto-refresh table every 10 seconds
- Responsive: Horizontal scroll on mobile
- Test: Table shows all positions with live updates

**MVP.4: Close Individual Position** (45 min)
- Create Alpine.js confirmation modal component in `base.html`:
  ```html
  <div x-data="{ open: false, coin: '', size: 0 }" x-show="open" @close-modal.window="open = false">
    <!-- Modal content with confirmation -->
  </div>
  ```
- Wire "Close" button to modal (Alpine.js `@click` directive)
- Modal shows:
  - Position details (coin, size, current PnL)
  - Confirmation message: "Are you sure you want to close this position?"
  - Estimated impact (current PnL realization)
  - Buttons: "Cancel" and "Confirm Close"
- HTMX POST to `/api/positions/{coin}/close` on confirm
- Loading spinner on button during request
- Success behavior:
  - Remove row from table with fade animation
  - Show success toast notification
- Error behavior:
  - Show error toast with message
  - Keep row in table
- Test: Close position, verify order placed on testnet

**MVP.5: Bulk Close Positions** (1.5 hours)
- Add bulk action buttons above positions table:
  - "Close 33% of Positions"
  - "Close 66% of Positions"
  - "Close 100% of Positions"
- Create bulk close confirmation modal (Alpine.js):
  - Show list of affected positions (sorted by size or PnL)
  - Display estimated total PnL impact
  - Warning message for 100%: "This will close ALL positions"
  - Buttons: "Cancel" and "Confirm Close {percentage}%"
- Create service method in `position_service.py`:
  ```python
  def bulk_close_positions(
      self,
      percentage: int,  # 33, 66, or 100
      coins: Optional[List[str]] = None  # If None, close all positions
  ) -> Dict[str, Any]:
      """
      Close percentage of open positions.
      Algorithm: Sort positions by size (descending), close top N% by count.
      Returns: { "success": int, "failed": int, "errors": [...] }
      """
  ```
- Create API endpoint in `positions.py`:
  ```python
  @router.post("/bulk-close", summary="Close percentage of all positions")
  async def bulk_close_positions(request: BulkCloseRequest):
      # request.percentage: 33, 66, or 100
      # request.coins: Optional[List[str]]
  ```
- Wire buttons with HTMX:
  ```html
  <button hx-post="/api/positions/bulk-close"
          hx-vals='{"percentage": 33}'
          hx-trigger="click"
          @click="showBulkModal(33)">
    Close 33%
  </button>
  ```
- Show progress indicator during bulk operation
- Success: Show summary toast ("Closed 5 of 15 positions")
- Test: Close 33% on testnet, verify orders

**MVP.6: Navigation & Polish** (30 min)
- Add navigation menu to `base.html`:
  - Dashboard (/)
  - Positions (/positions)
  - Active state highlighting (Tailwind classes)
- Page headers with titles
- Loading states:
  - Skeleton loaders for cards during initial load
  - Spinner overlays for actions
- Mobile responsive layout:
  - Collapsible navbar on mobile
  - Stacked cards on small screens
  - Horizontal scroll for positions table
- Error handling:
  - Toast notifications for errors (Alpine.js + Tailwind)
  - Inline error messages for failed actions
- "Last Updated" timestamp on dashboard (with HTMX refresh)
- Favicon and page titles
- Test: Mobile responsive, all interactions work

**MVP.7: Test & Commit**
- Manual testing checklist:
  - [ ] Dashboard loads with correct data
  - [ ] Positions table shows all positions
  - [ ] Individual close works (testnet)
  - [ ] Bulk close 33% works (testnet)
  - [ ] Bulk close 66% works (testnet)
  - [ ] Bulk close 100% works (testnet)
  - [ ] Auto-refresh updates data
  - [ ] Mobile responsive
  - [ ] Error handling works
  - [ ] Loading states display correctly
- Commit: "Phase 1B MVP Complete: Web Dashboard with Bulk Position Closing"

**Duration**: 5-6 hours
**Deliverable**: Functional web UI at http://localhost:8000

---

#### Later (Post-MVP)

**Deferred Features** (Phase 1B.2):
- Orders page (view open orders with filters)
- Cancel orders functionality (individual + cancel all)
- Market order form (place new market orders)
- Limit order form (place limit orders with price input)
- Dashboard: Market prices widget (top coins)
- Dashboard: Recent activity feed (last 10 fills)
- Performance charts (PnL over time, equity curve)
- Dark mode toggle (persist in localStorage)
- WebSocket live updates (replace HTMX polling)
- Desktop notifications (browser Notification API)
- Order history page (past 7 days)
- Position history page (closed positions)
- Export functionality (CSV download for positions/orders)
- Advanced filters (filter by coin, side, PnL range)

**Reasoning for Deferral**:
- MVP focuses on core value: viewing and closing positions
- Advanced features require additional complexity
- Can iterate based on user feedback after MVP
- WebSockets add deployment complexity (prefer polling for MVP)
- Order placement available via API/Swagger UI for now

---

### Phase 2: Advanced Features (Planned)

**Features to implement:**
- **Spot Trading Support** (Currently PERPS only)
  - Add `is_spot` parameter to order/position services
  - Handle spot asset naming (10000 + index convention)
  - Separate spot orders from perps orders
- Rebalancing engine
- Scale order system
- Performance analytics
- Position history

---

### Phase 3: Telegram Bot (Planned)

**Goal**: Mobile interface for trading and alerts

**Features:**
- All core commands (/account, /positions, /close, etc.)
- Interactive inline keyboards
- Real-time notifications
- Confirmation dialogs for critical actions

**Tech Stack:**
- python-telegram-bot library
- Reuses all services from Phase 1A

**Duration**: 4-5 days
**Deliverable**: Telegram bot interface

---

## Testing Strategy

### Critical Operations (Must Test)
- ✅ Order validation (size, side, type)
- ✅ Position closing validation
- ⚠️ Rebalancing calculations
- ⚠️ Scale order distributions

### Unit Tests
- Fast tests with mocked Hyperliquid API
- Focus on validation logic
- Run on every commit

### Integration Tests
- Use real testnet API
- Verify actual connectivity
- Run before major releases

### Manual Tests
- Test critical operations (order placement, position closing)
- Verify on testnet before mainnet
- Document results

### Test Commands
```bash
# Unit tests only (fast)
uv run pytest tests/ -m "not integration"

# Integration tests (requires testnet)
uv run pytest tests/integration/ -v

# All tests
uv run pytest tests/ -v

# Critical tests only
uv run pytest tests/ -m critical
```

---

## Current Progress

### Completed ✅
- **Phase 0**: FastAPI setup, Swagger UI, project structure, `uv` migration
- **Phase 1A.1**: Configuration system (settings, logger, env variables)
- **Phase 1A.2**: Hyperliquid SDK integration with proper wallet initialization
- **Phase 1A.3**: Account service (info, summary, balance - Perps + Spot)
- **Phase 1A.4**: Position service (list, get, close, summary)
- **Phase 1A.5**: Order service (market, limit, cancel, cancel all)
  - Fixed critical error handling bug (Hyperliquid response parsing)
  - Created comprehensive test suites
  - Tested successfully on Hyperliquid testnet
- **Phase 1A.6**: Market data service (prices, order books, metadata)
  - 1547 trading pairs, 198 with full metadata
  - L2 order book snapshots
  - Asset metadata with tick sizes and leverage limits
- **Phase 1B**: Web Dashboard MVP (Complete)
- **Phase 2A**: Rebalancing Engine with Risk Management (Complete)
- **Phase 2B**: Scale Orders & Advanced Trading (Complete)
- **Phase 2D**: Leverage Management Service (Complete)
- **Phase 4**: Code Consolidation & Use Case Layer (Complete - 2025-11-06)
  - Phase 4.1: Foundation - Centralized Utilities & Use Case Infrastructure
  - Phase 4.2: Trading Use Cases + API/Bot Migration
  - Phase 4.3: Portfolio Use Cases - API Integration
  - Phase 4.4: Scale Order Use Cases - API Integration
  - Phase 4.5: Cleanup & Testing Complete
  - 2,798 LOC in use cases
  - 12,076 total LOC
  - 106 tests passing

### In Progress 🔄
- None (Phase 4 Complete!)

### Blocked 🚫
- None

### Key Achievements This Session (2025-11-06)
- ✅ Completed Phase 4.1: Foundation - Centralized Utilities
  - Created response_parser.py, usd_converter.py, validators.py
  - Removed duplicate code from services
- ✅ Completed Phase 4.2: Trading Use Cases
  - PlaceOrderUseCase, ClosePositionUseCase
  - Migrated API routes to use use cases
- ✅ Completed Phase 4.3: Portfolio Use Cases
  - PositionSummaryUseCase, RiskAnalysisUseCase, RebalanceUseCase
  - Integrated with API routes
- ✅ Completed Phase 4.4: Scale Order Use Cases
  - PreviewScaleOrderUseCase, PlaceScaleOrderUseCase, TrackScaleOrderUseCase
  - All scale order endpoints use use cases
- ✅ Completed Phase 4.5: Cleanup & Testing
  - All 106 tests passing
  - Documentation updated
- 🎉 **Phase 4 Complete: 100% (5/5 sub-phases)**
- 🎯 **Codebase**: 12,076 LOC total, 2,798 LOC in use cases

---

## Decision Log

### Architecture Decisions

**Decision 1: FastAPI over Flask**
- **When**: Phase 0
- **Rationale**:
  - Auto-generated API docs (Swagger UI)
  - Native async support
  - Better type hints
  - Modern and actively maintained

**Decision 2: Web Dashboard before Telegram Bot**
- **When**: Planning phase
- **Rationale**:
  - Better for development and testing
  - Visual feedback more intuitive
  - Can test complex scenarios easier
  - Telegram can be added later as additional interface

**Decision 3: Use `uv` instead of `pip`**
- **When**: Phase 0
- **Rationale**:
  - 10-100x faster
  - Lockfile support (reproducible installs)
  - Automatic virtual environment management
  - Modern tooling

**Decision 4: Service Layer Pattern**
- **When**: Planning phase
- **Rationale**:
  - UI-agnostic business logic
  - Easy to add multiple interfaces
  - Better testability
  - Clear separation of concerns

---

## Next Steps

1. ✅ Complete Phase 0 (FastAPI setup)
2. ✅ Implement configuration system (Phase 1A.1)
3. ✅ Add Hyperliquid service (Phase 1A.2)
4. ✅ Build account service (Phase 1A.3)
5. ✅ Build position service (Phase 1A.4)
6. ✅ Build order service (Phase 1A.5)
7. ✅ Build market data service (Phase 1A.6)
8. ✅ Phase 1B MVP: Web Dashboard Complete
   - ✅ MVP.1: Foundation Setup
   - ✅ MVP.2: Dashboard Page (account + position summaries)
   - ✅ MVP.3: Positions Table (real-time updates)
   - ✅ MVP.4: Close Individual Position
   - ✅ MVP.5: Bulk Close Positions (33%/66%/100%)
   - ✅ MVP.6: Navigation & Polish (favicon, loading indicators)
   - ✅ Committed: "Phase 1B Complete: Web Dashboard MVP"
9. ⏭️ **NEXT**: Choose next phase
   - Option A: Phase 1B.2 - Post-MVP Dashboard Features (orders, market data)
   - Option B: Phase 2 - Advanced Features (Rebalancing, Scale Orders, Spot Trading)
   - Option C: Phase 3 - Telegram Bot
   - Option D: Phase 1A.7 - Testing Infrastructure
10. 🔜 Phase 1B.2: Post-MVP Dashboard Features
11. 🔜 Phase 2: Advanced Features (Rebalancing, Scale Orders, Spot Trading)
12. 🔜 Phase 3: Telegram Bot

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hyperliquid SDK](../docs/hyperliquid/python-sdk.md)
- [Hyperliquid API Reference](../docs/hyperliquid/api-reference.md)
- [Testing Strategy](../docs/TESTING.md) (to be created)

---

**Last Updated**: 2025-11-06
**Current Phase**: ✅ Phase 4 Complete - Code Consolidation & Use Case Layer
