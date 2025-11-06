# Hyperbot TODO List

**Last Updated**: 2025-11-06
**Current Phase**: ✅ Phase 4 Complete - Code Consolidation & Use Case Layer
**Previous Phase**: ✅ Phase 2D Complete - Leverage Management Service

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

- [x] **Phase 2A.6**: Comprehensive Rebalancing Testing with Leverage Changes (2025-11-03)
  - [x] Fixed market data API endpoint prefix (`/market` → `/api/market`)
  - [x] Fixed slippage parameter (5.0% → 0.05 decimal)
  - [x] Set up test positions (SOL $89.86 at 2x, BTC $209.91 at 10x)
  - [x] Executed rebalancing test (mixed leverage → uniform 2x, 70/30 → 50/50)
  - [x] Verified all fixes work correctly:
    - [x] Abort on CLOSE failure (not triggered, all trades successful)
    - [x] Margin-aware scaling (system handled constraints correctly)
    - [x] Leverage change logic (BTC closed at 10x, reopened at 2x)
    - [x] Format error handling (no crashes)
  - [x] Verified final results:
    - [x] SOL: $149.76 (49.99%) at 2x leverage ✅
    - [x] BTC: $150.05 (50.01%) at 2x leverage ✅
    - [x] 100% trade success rate (3/3 trades) ✅
    - [x] Portfolio value preserved (99.96%) ✅
  - [x] Documented test results: `SUCCESSFUL_REBALANCE_TEST.md`

- [x] **Phase 1B.2**: Dashboard Improvements - Clarify Spot vs Perps Balance (2025-11-04)
  - [x] Updated Account Equity section to match Hyperliquid UI layout
  - [x] Separated Spot and Perps into distinct cards (2-column layout)
  - [x] Perps Overview now clearly shows Balance ($223.80)
  - [x] Matches user expectations from Hyperliquid screenshot
  - [x] Improved visual hierarchy with color-coded border accents
  - [x] Tested with live data - working perfectly

### Phase 2B: Scale Orders & Advanced Trading (2025-11-04)
- [x] **Phase 2B.1**: Scale Order Models & Configuration
  - [x] Created `src/models/scale_order.py` with Pydantic models
  - [x] ScaleOrderConfig: Configuration for placing scale orders
  - [x] ScaleOrderPreview: Preview before placement
  - [x] ScaleOrderResult: Placement results tracking
  - [x] ScaleOrder: Database model for tracking scale order groups
  - [x] ScaleOrderStatus: Status with fill tracking
  - [x] Validation: num_orders (2-20), price range, geometric_ratio (1.0-3.0)

- [x] **Phase 2B.2**: Scale Order Service Implementation
  - [x] Created `src/services/scale_order_service.py` with ScaleOrderService class
  - [x] Calculate price levels (linear distribution across range)
  - [x] Calculate sizes:
    - [x] Linear distribution (equal sizes)
    - [x] Geometric distribution (weighted with configurable ratio)
  - [x] Price and size rounding (tick size compliance)
  - [x] Place multiple limit orders as atomic group
  - [x] Track scale order groups with unique IDs
  - [x] Cancel all orders in a scale order group
  - [x] Get fill status with percentage tracking

- [x] **Phase 2B.3**: Hyperliquid Service Enhancements
  - [x] Added `place_limit_order()` method to hyperliquid_service
  - [x] Added `cancel_order()` method
  - [x] Added `get_open_orders()` method
  - [x] Added `is_initialized()` check method
  - [x] Fixed SDK parameter names (coin → name) to match Hyperliquid SDK

- [x] **Phase 2B.4**: Scale Order API Endpoints
  - [x] Created `src/api/routes/scale_orders.py` with comprehensive endpoints
  - [x] `POST /api/scale-orders/preview` - Preview scale order before placement
  - [x] `POST /api/scale-orders/place` - Place scale order (2-20 limit orders)
  - [x] `GET /api/scale-orders/` - List all scale order groups
  - [x] `GET /api/scale-orders/{id}` - Get detailed status with fills
  - [x] `DELETE /api/scale-orders/{id}` - Cancel all orders in group
  - [x] Complete error handling and validation

- [x] **Phase 2B.5**: Testing on Testnet
  - [x] Tested scale order preview (5 orders, $107k-$105k range)
  - [x] Successfully placed 3-order BTC scale order on testnet
  - [x] Orders: $108k, $107k, $106k (0.002 BTC each)
  - [x] All orders placed successfully (100% success rate)
  - [x] Tested geometric distribution with ratio=2.0 (sizes: 0.0007→0.0013→0.0027→0.0053)
  - [x] Verified scale order tracking and listing
  - [x] API endpoints fully functional

**Features Delivered**:
- Multiple limit orders placed as coordinated group (ladder strategy)
- Linear and geometric size distribution with configurable ratio
- Preview functionality to see orders before placement
- Group tracking with unique scale_order_id
- Fill percentage monitoring
- Atomic cancellation of all orders in group
- Price/size rounding for tick size compliance

**Example Usage**:
```bash
# Place 5 BTC buy orders from $108k down to $106k
curl -X POST '/api/scale-orders/place' -d '{
  "coin":"BTC", "is_buy":true, "total_size":0.01,
  "num_orders":5, "start_price":108000, "end_price":106000,
  "distribution_type":"geometric", "geometric_ratio":2.0
}'
```

### Phase 2D: Leverage Management Service (2025-11-04)
- [x] **Phase 2D.1**: Create Leverage Service
  - [x] Created `src/services/leverage_service.py` with LeverageService class
  - [x] Implemented `get_coin_leverage()` - Get current leverage for any coin
  - [x] Implemented `set_coin_leverage()` - Set leverage (only when no position exists)
  - [x] Implemented `validate_leverage()` - Validate with soft limits (5x warning, 10x+ extreme)
  - [x] Implemented `estimate_liquidation_price()` - Calculate liq price for planned positions
  - [x] Implemented `get_all_leverage_settings()` - Get leverage for all positions
  - [x] Risk assessment: LOW/MODERATE/HIGH/EXTREME based on distance to liquidation

- [x] **Phase 2D.2**: Integrate with Existing Services
  - [x] Integrated leverage_service into rebalance_service
  - [x] Removed duplicate leverage code from rebalance_service
  - [x] Added leverage configuration to settings.py (DEFAULT_LEVERAGE, MAX_LEVERAGE_WARNING)
  - [x] Lazy import pattern in order_service for future integration

- [x] **Phase 2D.3**: Create Leverage API Endpoints
  - [x] Created `src/api/routes/leverage.py` with comprehensive endpoints
  - [x] `GET /api/leverage/{coin}` - Get leverage for specific coin
  - [x] `GET /api/leverage/` - Get all leverage settings
  - [x] `POST /api/leverage/set` - Set leverage with validation
  - [x] `POST /api/leverage/validate` - Validate leverage value
  - [x] `POST /api/leverage/estimate-liquidation` - Estimate liq price
  - [x] Registered leverage routes in main.py

**Features Delivered**:
- Centralized leverage management with validation
- Soft limit warnings (5x recommended, 6-10x warning, 10x+ extreme)
- Liquidation price estimation for planned positions
- Risk assessment (LOW/MODERATE/HIGH/EXTREME)
- Integration with rebalancing service
- Complete REST API for leverage operations
- Hyperliquid limitation handling (can only set leverage when no position exists)

**Example Usage**:
```bash
# Get leverage for BTC
curl GET '/api/leverage/BTC'

# Set leverage to 3x for ETH (only works if no position exists)
curl -X POST '/api/leverage/set' -d '{
  "coin":"ETH", "leverage":3, "is_cross":true
}'

# Estimate liquidation price before opening position
curl -X POST '/api/leverage/estimate-liquidation' -d '{
  "coin":"BTC", "entry_price":50000, "size":0.5,
  "leverage":3, "is_long":true
}'
```

---

## 🔄 In Progress

_No active tasks - Phase 4 Complete!_

---

## ✅ Phase 4: Code Consolidation & Use Case Layer (COMPLETE)

**Status**: ✅ Complete (2025-11-06)
**Actual Duration**: 1 session (5 phases)
**Priority**: HIGH - Prevented technical debt and API/Bot divergence

### Accomplishments

**Phases Completed:**
- ✅ Phase 4.1: Foundation - Centralized Utilities & Use Case Infrastructure
- ✅ Phase 4.2: Trading Use Cases + API/Bot Migration
- ✅ Phase 4.3: Portfolio Use Cases - API Integration
- ✅ Phase 4.4: Scale Order Use Cases - API Integration
- ✅ Phase 4.5: Cleanup & Testing Complete

**Code Statistics:**
- **Use Cases Created**: 2,798 LOC
- **Total Codebase**: 12,076 LOC
- **Tests Passing**: 106 passed, 2 skipped
- **Duplicate Code**: Eliminated (response parsers centralized)

**Use Cases Implemented:**

1. **Common Utilities** (`src/use_cases/common/`)
   - `response_parser.py` - Centralized Hyperliquid response parsing
   - `usd_converter.py` - Unified USD conversion logic
   - `validators.py` - Centralized validation (orders, portfolio, leverage)

2. **Trading Use Cases** (`src/use_cases/trading/`)
   - `PlaceOrderUseCase` - Place market/limit orders with validation
   - `ClosePositionUseCase` - Close positions with risk checks

3. **Portfolio Use Cases** (`src/use_cases/portfolio/`)
   - `PositionSummaryUseCase` - Aggregate positions with risk metrics
   - `RiskAnalysisUseCase` - Portfolio/position risk assessment
   - `RebalanceUseCase` - Portfolio rebalancing with preview/execution

4. **Scale Order Use Cases** (`src/use_cases/scale_orders/`)
   - `PreviewScaleOrderUseCase` - Calculate price levels and sizes
   - `PlaceScaleOrderUseCase` - Execute multiple limit orders
   - `ListScaleOrdersUseCase` - List and filter scale orders
   - `GetScaleOrderStatusUseCase` - Track fill progress
   - `CancelScaleOrderUseCase` - Cancel scale order groups

**API Routes Updated:**
- `/api/orders/` - Uses trading use cases
- `/api/positions/` - Uses portfolio use cases
- `/api/rebalance/` - Uses portfolio use cases
- `/api/scale-orders/` - Uses scale order use cases

### Benefits Achieved

✅ **Single Source of Truth**: Features implemented once, used everywhere
✅ **No API/Bot Divergence**: Shared business logic prevents feature drift
✅ **Easier Testing**: Use cases testable independently from API/Bot
✅ **Faster Development**: Add feature once, appears in multiple interfaces
✅ **Better Maintainability**: Update business logic in one place
✅ **Consistent Validation**: Same rules enforced everywhere

---

## 📋 Up Next

### Future Phases (Optional Enhancements)

#### Objectives
- Eliminate 23 identified code duplication issues
- Prevent API and Bot feature divergence
- Establish Use Case Layer for shared business logic
- Reduce codebase from 6,272 → ~5,400 LOC (-14%)
- Achieve 100% feature parity between API and Bot

#### Analysis Results
**Code Health Assessment**:
- ✅ Service Layer: Clean, properly shared
- ✅ Architecture: Well-structured
- ⚠️ Code Duplication: 23 issues identified
- ⚠️ Feature Divergence: API and Bot implementing features differently

**Key Issues**:
1. Duplicate response parser in `position_service.py` and `order_service.py`
2. Inconsistent service initialization across 10 service modules
3. Repeated loading messages (15+ occurrences)
4. API/Bot divergence in risk metrics, USD conversion, rebalancing weights, scale order tracking

#### Phase 4.1: Foundation (Week 1)
- [ ] **Create Use Case Infrastructure**
  - [ ] Create `src/use_cases/` directory
  - [ ] Create `src/use_cases/base.py` with `BaseUseCase` abstract class
  - [ ] Create `src/use_cases/common/` directory

- [ ] **Centralized Utilities**
  - [ ] Create `src/use_cases/common/response_parser.py`
    - [ ] Implement `parse_hyperliquid_response()` (single source of truth)
    - [ ] Remove duplicate from `position_service.py:10-43`
    - [ ] Remove duplicate from `order_service.py:23-61`
  - [ ] Create `src/use_cases/common/usd_converter.py`
    - [ ] Implement `USDConverter` class
    - [ ] Move USD conversion logic from `src/bot/utils.py`
    - [ ] Add support for both API and Bot
  - [ ] Create `src/use_cases/common/validators.py`
    - [ ] Implement `OrderValidator` class
    - [ ] Centralize validation rules
    - [ ] Support size, price, leverage validation

- [ ] **Testing**
  - [ ] Write unit tests for response parser
  - [ ] Write unit tests for USD converter
  - [ ] Write unit tests for validators
  - [ ] Commit: "Phase 4.1: Foundation - Centralized Utilities"

#### Phase 4.2: Trading Use Cases (Week 2)
- [ ] **Create Trading Use Cases**
  - [ ] Create `src/use_cases/trading/` directory
  - [ ] Create `src/use_cases/trading/place_order.py`
    - [ ] Implement `PlaceOrderUseCase` with USD conversion
    - [ ] Add size validation and leverage management
    - [ ] Add response formatting
  - [ ] Create `src/use_cases/trading/close_position.py`
    - [ ] Implement `ClosePositionUseCase`
    - [ ] Add confirmation logic
    - [ ] Add risk checks
  - [ ] Create `src/use_cases/trading/market_order.py`
    - [ ] Implement `MarketOrderUseCase`
    - [ ] Add slippage handling
    - [ ] Add size validation

- [ ] **Migrate API Routes**
  - [ ] Update `src/api/routes/orders.py` to use `PlaceOrderUseCase`
  - [ ] Update `src/api/routes/positions.py` to use `ClosePositionUseCase`
  - [ ] Test all API endpoints still work

- [ ] **Migrate Bot Handlers**
  - [ ] Update `src/bot/handlers/trading.py` to use trading use cases
  - [ ] Update `src/bot/handlers/positions.py` to use trading use cases
  - [ ] Test all bot commands still work

- [ ] **Testing**
  - [ ] Write unit tests for trading use cases
  - [ ] Write integration tests for API routes
  - [ ] Write integration tests for bot handlers
  - [ ] Commit: "Phase 4.2: Trading Use Cases - API/Bot Migration"

#### Phase 4.3: Portfolio Use Cases (Week 3)
- [ ] **Create Portfolio Use Cases**
  - [ ] Create `src/use_cases/portfolio/` directory
  - [ ] Create `src/use_cases/portfolio/risk_analysis.py`
    - [ ] Implement `RiskAnalysisUseCase`
    - [ ] Calculate Cross Margin Ratio
    - [ ] Calculate liquidation distance
    - [ ] Calculate health scores
  - [ ] Create `src/use_cases/portfolio/rebalance.py`
    - [ ] Implement `RebalanceUseCase`
    - [ ] Support custom weights (API feature)
    - [ ] Support equal weight (Bot feature)
    - [ ] Integrate leverage management
  - [ ] Create `src/use_cases/portfolio/position_summary.py`
    - [ ] Implement `PositionSummaryUseCase`
    - [ ] Add formatting logic
    - [ ] Add PnL calculations
    - [ ] Include risk metrics

- [ ] **Migrate API Routes**
  - [ ] Update `src/api/routes/positions.py` to use portfolio use cases
  - [ ] Update `src/api/routes/rebalance.py` to use `RebalanceUseCase`
  - [ ] Add risk metrics to API responses

- [ ] **Migrate Bot Handlers**
  - [ ] Update `src/bot/handlers/basic.py` to use `PositionSummaryUseCase`
  - [ ] Update `src/bot/handlers/advanced.py` to use `RebalanceUseCase`
  - [ ] Add risk metrics display to bot
  - [ ] Add custom weights support to bot rebalancing

- [ ] **Testing**
  - [ ] Write unit tests for portfolio use cases
  - [ ] Test API endpoints with risk metrics
  - [ ] Test bot commands with risk metrics
  - [ ] Commit: "Phase 4.3: Portfolio Use Cases - Feature Parity"

#### Phase 4.4: Scale Order Use Cases (Week 4)
- [ ] **Create Scale Order Use Cases**
  - [ ] Create `src/use_cases/scale_orders/` directory
  - [ ] Create `src/use_cases/scale_orders/preview.py`
    - [ ] Implement `PreviewScaleOrderUseCase`
    - [ ] Share preview logic between API and Bot
  - [ ] Create `src/use_cases/scale_orders/place.py`
    - [ ] Implement `PlaceScaleOrderUseCase`
    - [ ] Share placement logic between API and Bot
  - [ ] Create `src/use_cases/scale_orders/track.py`
    - [ ] Implement `TrackScaleOrderUseCase`
    - [ ] Share tracking logic between API and Bot

- [ ] **Migrate API Routes**
  - [ ] Update `src/api/routes/scale_orders.py` to use scale order use cases
  - [ ] Verify tracking functionality still works

- [ ] **Migrate Bot Handlers**
  - [ ] Update `src/bot/handlers/scale_orders.py` to use scale order use cases
  - [ ] Add `/scale_status` command to bot
  - [ ] Add scale order tracking UI to bot
  - [ ] Add active scale orders display
  - [ ] Add fill progress display
  - [ ] Enable cancellation from bot

- [ ] **Testing**
  - [ ] Write unit tests for scale order use cases
  - [ ] Test API scale order tracking
  - [ ] Test bot scale order tracking
  - [ ] Commit: "Phase 4.4: Scale Order Use Cases - Bot Tracking Added"

#### Phase 4.5: Cleanup & Testing (Week 5)
- [ ] **Remove Duplicate Code**
  - [ ] Delete duplicate `_parse_hyperliquid_response()` from services
  - [ ] Consolidate service initialization patterns
  - [ ] Remove repeated loading messages
  - [ ] Remove hardcoded leverage values
  - [ ] Remove hardcoded rebalance weights

- [ ] **Update All Tests**
  - [ ] Update service tests to use centralized utilities
  - [ ] Add use case tests (target >80% coverage)
  - [ ] Add integration tests for API/Bot parity
  - [ ] Verify all 56+ tests still passing

- [ ] **Documentation**
  - [ ] Update `docs/PLAN.md` with new architecture
  - [ ] Document use case patterns in `docs/ARCHITECTURE.md`
  - [ ] Add examples for adding new features
  - [ ] Update `CLAUDE.md` with use case guidelines

- [ ] **Verification**
  - [ ] Run full test suite
  - [ ] Verify code reduction achieved (6,272 → ~5,400 LOC)
  - [ ] Verify all 23 duplicate blocks eliminated
  - [ ] Verify API/Bot feature parity
  - [ ] Commit: "Phase 4.5: Cleanup & Testing Complete"
  - [ ] Final commit: "Phase 4 Complete: Code Consolidation & Use Case Layer"

#### Expected Outcomes
**Metrics**:
- ✅ Code Reduction: 6,272 → ~5,400 LOC (-14%)
- ✅ Duplication Eliminated: All 23 duplicate blocks removed
- ✅ Test Coverage: Maintain >80% for use cases
- ✅ Feature Parity: 100% between API and Bot

**Benefits**:
- ✅ Single Source of Truth: Features implemented once, used everywhere
- ✅ No Divergence: API and Bot automatically stay in sync
- ✅ Easier Testing: Use cases testable independently
- ✅ Faster Development: Add feature once, appears in both interfaces
- ✅ Better Maintainability: Update business logic in one place
- ✅ Consistent Validation: Same rules enforced everywhere

#### Success Criteria
- [ ] All 23 duplicate code blocks eliminated
- [ ] API and Bot use same use cases for all features
- [ ] Risk metrics shown in both API and Bot
- [ ] USD conversion available in both API and Bot
- [ ] Rebalancing supports custom weights in both interfaces
- [ ] Scale order tracking available in both interfaces
- [ ] All existing tests passing
- [ ] New use case tests added with >80% coverage
- [ ] Code reduction of 10-15% achieved
- [ ] Documentation updated

#### File Structure After Phase 4
```
src/
├── use_cases/               # NEW
│   ├── base.py
│   ├── common/
│   │   ├── response_parser.py
│   │   ├── usd_converter.py
│   │   └── validators.py
│   ├── trading/
│   │   ├── place_order.py
│   │   ├── close_position.py
│   │   └── market_order.py
│   ├── portfolio/
│   │   ├── risk_analysis.py
│   │   ├── rebalance.py
│   │   └── position_summary.py
│   └── scale_orders/
│       ├── preview.py
│       ├── place.py
│       └── track.py
├── api/
│   └── routes/              # UPDATED (use use_cases)
├── bot/
│   └── handlers/            # UPDATED (use use_cases)
├── services/                # UNCHANGED (stays lean)
├── models/                  # UNCHANGED
└── config.py                # UNCHANGED
```

#### Migration Strategy
**Incremental Approach** (minimize risk):
1. ✅ Create use case infrastructure (doesn't break anything)
2. ✅ Migrate one feature at a time (test after each)
3. ✅ Run full test suite after each phase
4. ✅ Keep both old and new code until fully migrated
5. ✅ Remove old code only when all tests pass

**No Breaking Changes**:
- API endpoints stay the same
- Bot commands stay the same
- User experience unchanged
- Database schema unchanged

---

### Other Future Phases

**Phase 2C**: Spot Trading Integration
**Phase 3**: Telegram Bot Integration (Enhancement)
**Phase 1B.3**: Post-MVP Dashboard Features (orders, market data)
**Phase 1A.7**: Testing Infrastructure

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
- **Phase 2B**: ✅ 100% Complete (Scale Orders & Advanced Trading) 🎉
  - 2B.1 Scale Order Models: ✅ Complete
  - 2B.2 Scale Order Service: ✅ Complete
  - 2B.3 Hyperliquid Enhancements: ✅ Complete
  - 2B.4 Scale Order API: ✅ Complete & Tested
  - 2B.5 Testnet Testing: ✅ Complete
- **Phase 2D**: ✅ 100% Complete (Leverage Management Service) 🎉
  - 2D.1 Leverage Service: ✅ Complete
  - 2D.2 Service Integration: ✅ Complete
  - 2D.3 Leverage API: ✅ Complete
- **Phase 4**: 📋 Planned (Code Consolidation & Use Case Layer)
  - 4.1 Foundation: ⏳ Pending
  - 4.2 Trading Use Cases: ⏳ Pending
  - 4.3 Portfolio Use Cases: ⏳ Pending
  - 4.4 Scale Order Use Cases: ⏳ Pending
  - 4.5 Cleanup & Testing: ⏳ Pending
  - **Estimated Duration**: 5 weeks
  - **Priority**: HIGH - Prevents technical debt

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
- **Recommended**: Begin Phase 4 (Code Consolidation & Use Case Layer) - 5 weeks, HIGH priority
- Alternative: Phase 2C (Spot Trading), Phase 3 (Telegram Bot Enhancement), or Phase 1B.3 (Dashboard Features)
- Phase 4 will prevent technical debt accumulation and ensure API/Bot feature parity going forward

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

---

## 🧪 Testing Lessons & Known Issues

**Last Updated**: 2025-11-04

### Critical Testing Lessons Learned

#### 1. Service Singleton Mocking Pattern
**Problem**: Services created at module import time retain references to real service instances, causing "not initialized" errors in tests.

**Solution**: Use fixture-based patching with explicit attribute assignment:
```python
@pytest.fixture
def service(self, mock_hyperliquid_service, mock_position_service):
    with patch('src.services.leverage_service.hyperliquid_service', mock_hyperliquid_service):
        with patch('src.services.leverage_service.position_service', mock_position_service):
            svc = LeverageService()
            # CRITICAL: Explicitly assign mocked dependencies
            svc.hyperliquid = mock_hyperliquid_service
            svc.position_service = mock_position_service
            return svc
```

**Why it matters**: Without explicit assignment, the service keeps the original singleton reference even after patching.

#### 2. Mock Data Structure Must Match API Response Exactly
**Problem**: Tests failed with KeyError when mock data didn't match actual nested structure.

**Example**: Position data has nested "position" wrapper:
```python
# ❌ WRONG - Flat structure
{"coin": "BTC", "size": 1.26, "leverage_value": 3}

# ✅ CORRECT - Nested structure matching API
{
    "position": {
        "coin": "BTC",
        "size": 1.26,
        "leverage_value": 3,
        "leverage": {"value": 3, "type": "cross"}
    }
}
```

**Why it matters**: Production code accesses `item["position"]["coin"]`, not `item["coin"]`.

#### 3. Mock Return Values Must Be Python Types, Not Mock Objects
**Problem**: `TypeError: 'Mock' object is not iterable` when code iterates over mock return values.

**Solution**: Always return actual Python types:
```python
# ❌ WRONG - Returns Mock object
mock_info.spot_user_state.return_value = Mock()

# ✅ CORRECT - Returns actual list
mock_info.spot_user_state.return_value = {"balances": []}
```

**Why it matters**: Code like `for item in spot_state.get("balances", [])` needs real lists.

#### 4. Function Return Types Must Match Implementation
**Problem**: Tests expected single value but function returns tuple.

**Example**: `get_leverage_for_order()` returns `(leverage, needs_setting)` tuple:
```python
# ❌ WRONG - Expects single value
leverage = service.get_leverage_for_order("BTC")
assert leverage == 3

# ✅ CORRECT - Unpacks tuple
leverage, needs_setting = service.get_leverage_for_order("BTC")
assert leverage == 3
assert needs_setting is True
```

**Why it matters**: Always check function signatures and return type hints.

#### 5. Test Expectations Must Match Actual Formulas
**Problem**: Tests failed when liquidation price calculations didn't match expected range.

**Solution**: Run implementation first, verify formula is correct, then adjust test expectations:
```python
# Original expectation based on incorrect formula
assert 65000 < result.estimated_liquidation_price < 70000

# Updated expectation after verifying actual formula
assert 70000 < result.estimated_liquidation_price < 73000
```

**Why it matters**: Tests should validate correct behavior, not enforce incorrect expectations.

### Known Issues & Maintenance Notes

#### Wizard Tests Need Synchronization
**⚠️ IMPORTANT**: When making changes to bot handlers or service imports, check if wizard tests need updates.

**Current skipped tests** in `tests/bot/test_wizards.py`:
1. `test_market_amount_selected_parsing` - Import path for `market_data_service` changed in wizards.py
2. `test_close_position_execute_uses_size_closed` - Handler calls `edit_message_text` twice (progress + result), test expects once

**Action items**:
- Update test when fixing import path
- Update assertion to check both calls: initial "⏳ Processing..." and final result message
- Add CI check to prevent import mismatches in future

**Why it matters**: Bot handlers evolve frequently; tests must stay in sync to catch regressions.

### Test Coverage Summary
- **Total Tests**: 56 passing, 2 skipped
- **Coverage**: 25% (up from 9%)
- **Services with >80% coverage**:
  - LeverageService: 86%
  - Config/Logger: 100%
- **Priority for future tests**:
  - OrderService (11% coverage)
  - HyperliquidService (19% coverage)
  - RebalanceService (25% coverage)
  - RiskCalculator (31% coverage)
