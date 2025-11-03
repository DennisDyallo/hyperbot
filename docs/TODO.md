# Hyperbot TODO List

**Last Updated**: 2025-10-31
**Current Phase**: ✅ Phase 2A Complete - Rebalancing Engine with Risk Management

---

## ✅ Completed

### Phase 0: Foundation
- [x] FastAPI minimal setup
- [x] Health check endpoints
- [x] Swagger UI auto-documentation
- [x] Migrate to `uv` package manager
- [x] Project structure (src/, tests/, docs/)
- [x] Documentation system (Claude.md, API docs)
- [x] .gitignore for Python
- [x] README.md with setup instructions

### Phase 1A.1: Configuration System
- [x] Create `src/config/` directory
- [x] Create `src/config/settings.py` with environment variables
- [x] Create `src/config/logger.py` with loguru
- [x] Test configuration loading
- [x] Commit configuration system

### Phase 1A.2: Hyperliquid Service Integration
- [x] Create `src/services/` directory
- [x] Create `src/services/hyperliquid_service.py`
- [x] Implement HyperliquidService class with initialize() and health_check()
- [x] Add testnet/mainnet switching
- [x] Update health endpoint to check Hyperliquid status
- [x] Create manual test script: `scripts/test_hyperliquid.py`
- [x] Commit Hyperliquid service
- [x] ✅ Successfully tested with valid testnet credentials

### Phase 1A.3: Account Service
- [x] Create `src/api/models/` directory and response models (Pydantic)
- [x] Create `src/services/account_service.py` with AccountService class
- [x] Implement `get_account_info()` method with perps + spot
- [x] Implement `get_account_summary()` method
- [x] Implement `get_balance_details()` method
- [x] Create `src/api/routes/` directory
- [x] Create `src/api/routes/account.py` with endpoints
- [x] Register account routes in main.py with `/api` prefix
- [x] Test all account endpoints
- [x] Commit account service

### Phase 1A.4: Position Service
- [x] Create `src/services/position_service.py` with PositionService class
- [x] Implement `list_positions()` method
- [x] Implement `get_position(coin)` method
- [x] Implement `close_position(coin, size)` method
- [x] Implement `get_position_summary()` method
- [x] Create position response models (PositionSummary, ClosePositionResponse)
- [x] Create `src/api/routes/positions.py` with endpoints
- [x] Register position routes in main.py
- [x] Test all position endpoints
- [x] Commit position service

### Phase 1A.5: Order Service
- [x] Create `src/services/order_service.py` with OrderService class
- [x] Implement `list_open_orders()` method
- [x] Implement `place_market_order()` method
- [x] Implement `place_limit_order()` method
- [x] Implement `cancel_order()` method
- [x] Implement `cancel_all_orders()` method
- [x] Create order response models (OrderResponse, CancelOrderResponse)
- [x] Create `src/api/routes/orders.py` with endpoints:
  - [x] `GET /api/orders/` - List open orders
  - [x] `POST /api/orders/market` - Place market order
  - [x] `POST /api/orders/limit` - Place limit order
  - [x] `DELETE /api/orders/{coin}/{order_id}` - Cancel order
  - [x] `DELETE /api/orders/all` - Cancel all orders
- [x] Register order routes in main.py
- [x] Test all order endpoints
- [x] Commit order service

### Phase 1A.6: Market Data Service
- [x] Create `src/services/market_data_service.py`
- [x] Implement MarketDataService class
  - [x] `get_all_prices()` method
  - [x] `get_price(symbol)` method
  - [x] `get_market_info()` method
  - [x] `get_order_book(coin)` method
  - [x] `get_asset_metadata(coin)` method
- [x] Create API routes: `src/api/routes/market_data.py`
  - [x] `GET /api/market/prices`
  - [x] `GET /api/market/price/{symbol}`
  - [x] `GET /api/market/info`
  - [x] `GET /api/market/orderbook/{coin}`
  - [x] `GET /api/market/asset/{coin}`
- [x] Test market data fetching
- [x] Commit market data service

### Phase 1B: Web Dashboard MVP
- [x] MVP.1: Foundation Setup (dependencies, Jinja2, static files)
- [x] MVP.2: Dashboard Page (account + position summaries)
- [x] MVP.3: Positions Table (real-time updates with HTMX)
- [x] MVP.4: Close Individual Position (with confirmation modal)
- [x] MVP.5: Bulk Close Positions (33%/66%/100% buttons)
- [x] MVP.6: Navigation & Polish (favicon, loading indicators, responsive design)
- [x] Test all dashboard functionality
- [x] Commit: "Phase 1B Complete: Web Dashboard MVP"

### Phase 2A: Rebalancing Engine with Risk Management
- [x] **Phase 2A.1**: Create Risk Calculator Service + Research Docs
  - [x] Created `docs/research/` directory for technical documentation
  - [x] Documented liquidation price calculation from Hyperliquid docs
  - [x] Created `src/services/risk_calculator.py` with RiskCalculator class
  - [x] Implemented position risk assessment (liquidation price, distance, health score)
  - [x] Implemented portfolio risk assessment (overall risk level, warnings)
  - [x] Added risk level enum (SAFE, LOW, MODERATE, HIGH, CRITICAL)
  - [x] Created comprehensive unit tests

- [x] **Phase 2A.2**: Create Rebalancing Service with Risk Integration
  - [x] Created `src/services/rebalance_service.py` with RebalanceService class
  - [x] Implemented portfolio rebalancing algorithm
  - [x] Integrated risk assessment into rebalancing decisions
  - [x] Added support for both percentage and target value rebalancing
  - [x] Implemented preview functionality (dry-run mode)
  - [x] Added risk-aware thresholds for small positions

- [x] **Phase 2A.3**: Create Rebalance API Endpoints
  - [x] Created `src/api/routes/rebalance.py` with endpoints
  - [x] `POST /api/rebalance/preview` - Preview rebalance plan
  - [x] `POST /api/rebalance/execute` - Execute rebalance
  - [x] Added comprehensive request/response models
  - [x] Integrated risk warnings in API responses
  - [x] Tested all endpoints on testnet

- [x] **Phase 2A.4**: Risk Visualization UI
  - [x] Updated `account_service.py` to fetch Cross Margin Ratio data
  - [x] Updated `risk_calculator.py` to use Margin Ratio as primary metric
  - [x] Added Hyperliquid GUI-style "Perps Overview" section to dashboard
  - [x] Displayed Cross Margin Ratio with progress bar (0-100%)
  - [x] Added Maintenance Margin and Cross Account Leverage metrics
  - [x] Updated positions table with risk indicators:
    - [x] Liquidation Price column
    - [x] Liquidation Distance % column (color-coded)
    - [x] Risk Level badge column (SAFE/LOW/MODERATE/HIGH/CRITICAL)
  - [x] Updated positions route to calculate risk for each position

- [x] **Phase 2A.5**: Testing & Documentation
  - [x] Tested risk calculator with live positions
  - [x] Tested rebalance API endpoints (preview & execute)
  - [x] Tested dashboard UI with Hyperliquid metrics
  - [x] Verified Cross Margin Ratio matches Hyperliquid GUI (3.63%)
  - [x] Verified positions table shows risk indicators correctly
  - [x] All tests passing with no errors
  - [x] Updated documentation

---

## 🔄 In Progress

_No active tasks - Phase 2A Complete!_

---

## 📋 Up Next

### Choose Next Phase
**Option A**: Phase 2B - Scale Orders & Advanced Trading
**Option B**: Phase 2C - Spot Trading Integration
**Option C**: Phase 3 - Telegram Bot Integration
**Option D**: Phase 1B.2 - Post-MVP Dashboard Features
**Option E**: Phase 1A.7 - Testing Infrastructure

### Phase 1A.7: Testing Infrastructure (Optional - May Defer)
- [ ] Create `pytest.ini`
- [ ] Write unit tests for services
- [ ] Write integration tests for API endpoints
- [ ] Create `tests/conftest.py` with fixtures
- [ ] Create mock Hyperliquid fixture
- [ ] Write unit tests:
  - [ ] Order validation tests (critical!)
  - [ ] Position closing validation tests (critical!)
  - [ ] Input validation tests
- [ ] Create `tests/integration/` directory
- [ ] Write integration tests:
  - [ ] Testnet connection test
  - [ ] Account fetch test
  - [ ] Position fetch test
  - [ ] Market data test
- [ ] Create manual test for order placement
- [ ] Create test runner script: `scripts/run_tests.sh`
- [ ] Create `docs/TESTING.md` with testing guide
- [ ] Document testing strategy
- [ ] Commit testing infrastructure

---

## 🔮 Future Phases

### Phase 1B: Web Dashboard (Split: MVP Now / Later)

#### MVP (Now) - Estimated: 5-6 hours
**Goal:** View account/positions + Close positions (individual & bulk)

- [ ] **MVP.1: Foundation Setup** (30 min)
  - [ ] Add dependencies: jinja2, python-multipart
  - [ ] Create src/api/templates/ and src/static/css/
  - [ ] Configure static files and Jinja2 in main.py
  - [ ] Create base.html with Tailwind, HTMX, Alpine.js CDN
  - [ ] Create basic navbar component
  - [ ] Create src/api/routes/web.py for HTML routes

- [ ] **MVP.2: Dashboard Page** (1 hour)
  - [ ] Create dashboard.html template
  - [ ] Add GET / route → renders dashboard
  - [ ] Account Summary Card (balance, equity, margin, available)
  - [ ] Positions Summary Widget (total, long/short, PnL)
  - [ ] HTMX auto-refresh every 10s
  - [ ] Responsive grid layout

- [ ] **MVP.3: Positions Table** (1.5 hours)
  - [ ] Create positions.html template
  - [ ] Add GET /positions route
  - [ ] Table: Coin | Side | Size | Entry | Current | Value | PnL | PnL% | Leverage | Actions
  - [ ] Color coding: Green (profit), Red (loss)
  - [ ] "Close" button per position
  - [ ] Empty state handling
  - [ ] HTMX auto-refresh table

- [ ] **MVP.4: Close Individual Position** (45 min)
  - [ ] Alpine.js confirmation modal component
  - [ ] Wire "Close" button to modal
  - [ ] HTMX POST to /api/positions/{coin}/close
  - [ ] Loading spinner on button
  - [ ] Success: Remove row with animation
  - [ ] Error: Show toast notification

- [ ] **MVP.5: Bulk Close Positions** (1.5 hours)
  - [ ] Add bulk action buttons: "Close 33%", "Close 66%", "Close 100%"
  - [ ] Create bulk close confirmation modal
  - [ ] Show affected positions + estimated PnL impact
  - [ ] Create POST /api/positions/bulk-close endpoint
  - [ ] Implement bulk_close_positions() service method
  - [ ] Wire buttons with HTMX
  - [ ] Show progress indicator
  - [ ] Success summary toast

- [ ] **MVP.6: Navigation & Polish** (30 min)
  - [ ] Navigation menu with active state
  - [ ] Page headers/titles
  - [ ] Loading states (skeletons, spinners)
  - [ ] Mobile responsive layout
  - [ ] Error handling (toasts, inline errors)
  - [ ] "Last Updated" timestamp

- [ ] **Test MVP and commit**

#### Later (Post-MVP)
- [ ] Orders page (view open orders)
- [ ] Cancel orders functionality
- [ ] Market order form
- [ ] Limit order form
- [ ] Dashboard: Market prices widget
- [ ] Dashboard: Recent activity feed
- [ ] Performance charts
- [ ] Dark mode toggle
- [ ] WebSocket live updates
- [ ] Desktop notifications

### Phase 2: Advanced Features
- [ ] Rebalancing service
- [ ] Scale order service
- [ ] Position history tracking
- [ ] Performance analytics

### Phase 3: Telegram Bot
- [ ] Telegram bot setup
- [ ] Command handlers
- [ ] Inline keyboards
- [ ] Notifications
- [ ] Confirmation dialogs

---

## 🚫 Blocked

None

---

## 📊 Progress Summary

- **Phase 0**: ✅ 100% Complete (Foundation)
- **Phase 1A**: ✅ 100% Complete (Core Services + API)
  - 1A.1 Configuration: ✅ Complete
  - 1A.2 Hyperliquid Service: ✅ Complete & Tested
  - 1A.3 Account Service: ✅ Complete & Tested
  - 1A.4 Position Service: ✅ Complete & Tested
  - 1A.5 Order Service: ✅ Complete & Tested
  - 1A.6 Market Data: ✅ Complete & Tested
  - 1A.7 Testing: ⏭️ Deferred
- **Phase 1B**: ✅ 100% Complete (Web Dashboard MVP)
- **Phase 2A**: ✅ 100% Complete (Rebalancing Engine with Risk Management) 🎉
  - 2A.1 Risk Calculator Service: ✅ Complete
  - 2A.2 Rebalancing Service: ✅ Complete
  - 2A.3 Rebalance API Endpoints: ✅ Complete & Tested
  - 2A.4 Risk Visualization UI: ✅ Complete
  - 2A.5 Testing & Documentation: ✅ Complete

---

## 📝 Notes

### Known Issues
- **Limit Order Tick Size**: Limit orders require prices to be divisible by the asset's tick size. Need to add price rounding utility.
  - Discovered during testing: "Price must be divisible by tick size. asset=3"
  - Affects limit orders placed programmatically
  - Market orders work perfectly

### Recent Fixes (Phase 1A.5 - 2025-10-31)
- **SDK Parameter Names**: Fixed `coin` → `name` for order(), market_open(), and cancel() methods
- **Wallet Initialization**: Fixed Exchange client to use `Account.from_key()` for wallet creation
- **Cancel All Orders**: Implemented using individual cancel() calls (no bulk cancel_all method in SDK)
- **Critical Error Handling Bug**: Fixed Hyperliquid response parsing
  - API was returning HTTP 200 even when orders failed
  - Added `_parse_hyperliquid_response()` helper function
  - Now properly raises ValueError (400) for validation errors
  - Now properly raises RuntimeError (500) for API errors
  - Created test_error_handling.py to validate fix (all tests passing)

### Testing Strategy
- Write unit tests for critical operations (order validation, position management)
- Use mocked Hyperliquid API for fast tests
- Use real testnet for integration tests
- Manual verification before mainnet

### Git Commit Strategy
- Commit after each sub-phase completion
- Use descriptive commit messages
- Push to feature branch regularly

### Documentation Updates
- Update this TODO.md after completing tasks
- Update PLAN.md when phases change
- Keep Claude.md in sync with current phase

---

**Next Action**:
- Choose next phase: 2B (Scale Orders), 2C (Spot Trading), or 3 (Telegram Bot)
- Consider adding price rounding utility for limit orders (tick size validation)
- Consider adding bulk order placement support

**Session Summary (2025-10-31) - Phase 2A Complete**:
- ✅ Completed Phase 2A.1: Risk Calculator Service + Research Docs
- ✅ Completed Phase 2A.2: Rebalancing Service with Risk Integration
- ✅ Completed Phase 2A.3: Rebalance API Endpoints
- ✅ Completed Phase 2A.4: Risk Visualization UI
- ✅ Completed Phase 2A.5: Testing & Documentation
- 📊 Phase 2A Progress: 0% → 100% 🎉
- 🔥 Key Achievement: Dashboard now matches Hyperliquid GUI metrics

**Phase 2A Key Features**:
- Risk Calculator: Liquidation price, distance, health score, risk levels
- Rebalancing Service: Portfolio rebalancing with risk integration
- Rebalance API: Preview and execute endpoints with risk warnings
- Risk Visualization:
  - Cross Margin Ratio display with progress bar (liquidation at 100%)
  - Perps Overview section matching Hyperliquid GUI
  - Positions table with Liquidation Price, Liq Distance %, Risk Level badges
- Cross Margin Ratio: 3.63% (verified matches Hyperliquid GUI)
- All endpoints tested successfully with no errors

**Technical Highlights**:
- Used Cross Margin Ratio as PRIMARY risk metric for cross-margin positions (official Hyperliquid approach)
- Liquidation distance used as SECONDARY metric for individual positions
- Color-coded risk indicators: SAFE (green), LOW (yellow), MODERATE (orange), HIGH (red), CRITICAL (dark red)
- Risk levels: SAFE <30%, LOW 30-50%, MODERATE 50-70%, HIGH 70-90%, CRITICAL >90%
- Comprehensive API data: `crossMaintenanceMarginUsed`, `marginSummary`, `crossMarginSummary`
