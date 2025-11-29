# Hyperbot TODO List

> **For architecture and strategic decisions**, see [PLAN.md](PLAN.md)

**Last Updated**: 2025-11-29
**Current Phase**: ✅ All Phases Complete - Production Ready
**Status**: System operational with hybrid WebSocket + polling notifications

---

## ✅ Phase 5: Order Fill Notifications (Complete)

**Goal**: Real-time Telegram notifications for all order fills with offline recovery
**Architecture**: Hybrid WebSocket + Smart Polling
**Status**: ✅ Complete - All sub-phases delivered

### Delivered Features

✅ **WebSocket Real-time Notifications:**
- WebSocket connection to Hyperliquid userEvents
- Real-time fill event processing (<1s latency)
- Heartbeat tracking (last: Nov 29, 2025)
- Automatic reconnection logic

✅ **Recovery & Reliability:**
- Startup recovery (back-notifies missed fills after bot restart)
- Backup polling (every 5 minutes as safety net)
- State persistence (`data/notification_state.json`)
- Deduplication (1000 fill hash cache)

✅ **Telegram Integration:**
- Bot integration (post_init/post_shutdown lifecycle)
- Notification commands:
  - `/notify_status` - Show service status and health
  - `/notify_test` - Send test notification
  - `/notify_history` - Show recent fills
- Smart batching (individual for ≤5 fills, summary for >5)

✅ **Phase 5 Sub-Tasks:**
- Phase 5A: Foundation + Learning Tests ✅
- Phase 5B: WebSocket Implementation ✅
- Phase 5C: Recovery Mechanism ✅
- Phase 5D: Telegram Integration ✅
- Phase 5E: Scale Order Enhancement ✅ (aggregate notifications)

---

## 📋 Planned Features

### Phase 6: Outstanding Orders Management
**Goal**: List, filter, and manage all outstanding (open/unfilled) orders
**Status**: 📋 Planned
**Priority**: MEDIUM
**Duration**: 1-2 days

**Features**:
- List all outstanding orders with filters
- Cancel individual or bulk orders
- Integration with Telegram bot
- See detailed UX design in [PLAN.md](PLAN.md) Phase 6

---

## 🧪 Testing Lessons & Known Issues

**Last Updated**: 2025-11-29

### Critical Testing Patterns

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

#### 3. Mock Return Values Must Be Python Types, Not Mock Objects
**Problem**: `TypeError: 'Mock' object is not iterable` when code iterates over mock return values.

**Solution**: Always return actual Python types:
```python
# ❌ WRONG - Returns Mock object
mock_info.spot_user_state.return_value = Mock()

# ✅ CORRECT - Returns actual list
mock_info.spot_user_state.return_value = {"balances": []}
```

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

### Known Issues & Maintenance Notes

#### Wizard Tests Need Synchronization
⚠️ **Note**: When making changes to bot handlers or service imports, verify wizard tests are updated.

**Note**: Some wizard tests may be skipped during refactoring. Re-enable when stable.

### Test Coverage Summary
- **Total Tests**: 682 passing
- **Coverage**: 65%
- **Services with excellent coverage (>90%)**:
  - Config/Logger: 100%
  - HyperliquidService: 100%
  - MarketDataService: 98%
  - PositionService: 97%
  - ScaleOrderService: 96%
  - RiskCalculator: 95%
  - LeverageService: 93%

**Target**: Increase coverage to 70%+ for Phase 6

---

## 📝 Notes

### Recent Work (2025-11-29)

**System Status:**
- ✅ All core phases complete and operational
- ✅ WebSocket notifications working (heartbeat: Nov 29, 14:00)
- ✅ Backup polling active (5-minute safety net)
- ✅ 682 tests passing with 65% coverage
- 📋 Phase 6 (Outstanding Orders) designed and ready for implementation

**Production Readiness Checklist:**
- ✅ Core services (Account, Position, Order, Market Data)
- ✅ Rebalancing engine with risk management
- ✅ Scale orders (linear & geometric distribution)
- ✅ Leverage management with validation
- ✅ Telegram bot with interactive wizards
- ✅ Order fill notifications (real-time + recovery)
- ✅ Use case layer for code reuse
- ✅ Comprehensive test coverage
- ✅ Error handling and logging
- ✅ State persistence
- ✅ Testnet and mainnet support

### Testing Strategy

**Critical Operations** (Must Test):
- Order validation (size, side, type)
- Position closing validation
- Rebalancing calculations
- Scale order distributions
- **NEW**: WebSocket subscription and event processing

**Test Commands**:
```bash
# Unit tests only (fast)
uv run pytest tests/ -m "not integration"

# Integration tests (requires testnet)
uv run pytest tests/integration/ -v

# All tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

### Git Commit Strategy
- Commit after each sub-phase completion
- Use descriptive commit messages
- Push to feature branch regularly

### Documentation Updates
- Update this TODO.md after completing tasks
- Update PLAN.md when phases change
- Keep Claude.md in sync with current phase

---

## 🎯 Next Actions

**Phase 6: Outstanding Orders Management** (When ready to implement):

1. **Backend Implementation** (Day 1):
   - Add `list_outstanding_orders()` to OrderService
   - Create `ListOutstandingOrdersUseCase`
   - Implement filtering logic (by coin, side, type)
   - Add REST API endpoints
   - Write unit tests

2. **Telegram Integration** (Day 2):
   - Implement `/orders` command handler
   - Create interactive filter menus
   - Add individual cancel handlers
   - Add bulk cancel with confirmation
   - Integrate with main menu
   - End-to-end testing

3. **Testing & Refinement**:
   - Test with various order states
   - Verify pagination for >10 orders
   - Test filter combinations
   - Validate cancel operations
   - Test error scenarios

**Future Enhancements** (Post-Phase 6):
- Order modification (edit price/size)
- Order templates/presets
- Advanced filters (time range, partially filled)
- Order analytics (fill rate, avg execution time)
- Export order history

---

## 📊 Progress Summary

- **Phase 0**: ✅ 100% Complete (Foundation)
- **Phase 1A**: ✅ 100% Complete (Core Services + API)
- **Phase 1B**: ⛔ Not Planned (Web Dashboard - abandoned for Telegram)
- **Phase 2A**: ✅ 100% Complete (Rebalancing Engine)
- **Phase 2B**: ✅ 100% Complete (Scale Orders)
- **Phase 2C**: ✅ 100% Complete (Spot Trading Integration)
- **Phase 2D**: ✅ 100% Complete (Leverage Management)
- **Phase 3**: ✅ 100% Complete (Telegram Bot with Wizards)
- **Phase 4**: ✅ 100% Complete (Code Consolidation & Use Case Layer)
- **Phase 5**: ✅ 100% Complete (Order Fill Notifications)
  - 5A Foundation: ✅ Complete
  - 5B WebSocket: ✅ Complete
  - 5C Recovery: ✅ Complete
  - 5D Telegram: ✅ Complete
  - 5E Scale Orders: ✅ Complete
- **Phase 6**: 📋 Planned (Outstanding Orders Management)

**Overall Status**: Production Ready - 10 phases complete, 1 planned
