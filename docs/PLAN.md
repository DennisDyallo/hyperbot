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

### 🔄 Phase 1A: Core Services + API (In Progress)

**Goal**: Working REST API with all bot functionality testable via Swagger UI
**Note**: This phase implements **PERPS trading only**. Spot support will be added in Phase 2.

**Sub-phases:**

#### 1A.1: Configuration & Setup ⏭️ NEXT
- [ ] Create `src/config/settings.py`
- [ ] Load environment variables with python-dotenv
- [ ] Create `src/config/logger.py` with loguru
- [ ] Test configuration loading

#### 1A.2: Hyperliquid Service Integration
- [ ] Create `src/services/hyperliquid_service.py`
- [ ] Initialize Hyperliquid SDK
- [ ] Test connection to testnet
- [ ] Implement health check with Hyperliquid status
- [ ] Create manual test script

#### 1A.3: Account Service
- [ ] Create `src/services/account_service.py`
- [ ] Implement `get_account_info()`
- [ ] Implement `get_balance_details()`
- [ ] Create API endpoint: `GET /api/account/info`
- [ ] Test with real testnet

#### 1A.4: Position Service
- [ ] Create `src/services/position_service.py`
- [ ] Implement `get_all_positions()`
- [ ] Implement `get_position_by_symbol()`
- [ ] Implement `close_position()`
- [ ] Create API endpoints:
  - `GET /api/positions/list`
  - `GET /api/positions/{symbol}`
  - `POST /api/positions/close/{symbol}`
- [ ] Test position closing on testnet

#### 1A.5: Order Service
- [ ] Create `src/services/order_service.py`
- [ ] Implement `place_order()` (market & limit)
- [ ] Implement `get_open_orders()`
- [ ] Implement `cancel_order()`
- [ ] Create API endpoints:
  - `POST /api/orders/place`
  - `GET /api/orders/list`
  - `DELETE /api/orders/cancel/{symbol}/{order_id}`
- [ ] Test order placement on testnet

#### 1A.6: Market Data Service
- [ ] Create `src/services/market_data_service.py`
- [ ] Implement `get_all_prices()`
- [ ] Implement `get_price(symbol)`
- [ ] Implement `get_market_info()`
- [ ] Create API endpoints:
  - `GET /api/market/prices`
  - `GET /api/market/price/{symbol}`
  - `GET /api/market/info`

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
- FastAPI setup with Swagger UI
- Health check endpoints
- Project structure
- Modern dependency management with `uv`
- pyproject.toml configuration

### In Progress 🔄
- Configuration system (next step)

### Blocked 🚫
- None

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
2. ⏭️ Implement configuration system (Phase 1A.1)
3. 🔜 Add Hyperliquid service (Phase 1A.2)
4. 🔜 Build out remaining services (Phase 1A.3-1A.6)
5. 🔜 Add testing infrastructure (Phase 1A.7)

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hyperliquid SDK](../docs/hyperliquid/python-sdk.md)
- [Hyperliquid API Reference](../docs/hyperliquid/api-reference.md)
- [Testing Strategy](../docs/TESTING.md) (to be created)

---

**Last Updated**: 2025-10-30
**Current Phase**: Phase 1A.1 (Configuration)
