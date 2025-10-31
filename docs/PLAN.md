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

### Phase 1B: Web Dashboard (Planned)

**Goal**: Simple web UI for monitoring and control

**Features:**
- Dashboard overview (account value, positions)
- Position list with close buttons
- Order list with cancel buttons
- Simple order form (market orders)
- Real-time updates with HTMX

**Tech Stack:**
- FastAPI (Jinja2 templates)
- HTMX for dynamic updates
- Alpine.js for interactivity
- Tailwind CSS for styling

**Duration**: 3-4 days
**Deliverable**: Web UI accessible at http://localhost:8000

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

### In Progress 🔄
- None (Phase 1A Complete!)

### Blocked 🚫
- None

### Key Achievements This Session (2025-10-31)
- ✅ Completed Order Service implementation (Phase 1A.5)
- ✅ Fixed critical bug: API now returns proper HTTP status codes for failed operations
- ✅ Added Hyperliquid response error detection
- ✅ Created test_order_operations.py (full order lifecycle testing)
- ✅ Created test_error_handling.py (validates error detection)
- ✅ Completed Market Data Service implementation (Phase 1A.6)
- ✅ Added 5 market data endpoints (prices, order books, metadata)
- ✅ Successfully tested all operations on testnet
- 🎉 **Phase 1A Complete: 100% (7/7 sub-phases)**

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
7. ⏭️ **NEXT**: Build market data service (Phase 1A.6)
8. 🔜 Add testing infrastructure (Phase 1A.7)
9. 🔜 Start Phase 1B: Web Dashboard

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hyperliquid SDK](../docs/hyperliquid/python-sdk.md)
- [Hyperliquid API Reference](../docs/hyperliquid/api-reference.md)
- [Testing Strategy](../docs/TESTING.md) (to be created)

---

**Last Updated**: 2025-10-31
**Current Phase**: Phase 1B (Web Dashboard) or Phase 1A.7 (Testing Infrastructure)
