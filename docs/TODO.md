# Hyperbot TODO List

> **For architecture and strategic decisions**, see [PLAN.md](PLAN.md)

**Last Updated**: 2025-11-16
**Current Phase**: 🔄 Phase 5 - Order Fill Notifications (Real-time + Recovery)
**Status**: WebSocket Investigation - Backup polling working, real-time notifications not working

---

## 🔄 Phase 5: Order Fill Notifications (In Progress)

**Goal**: Real-time Telegram notifications for all order fills with offline recovery
**Architecture**: Hybrid WebSocket + Smart Polling

### Current Status

✅ **Working:**
- Startup recovery (back-notifies missed fills after bot restart)
- Backup polling (every 5 minutes)
- Telegram integration
- State persistence (`data/notification_state.json`)
- Deduplication (1000 fill hash cache)

❌ **Not Working:**
- **WebSocket real-time notifications** (last heartbeat: Nov 13, 3 days ago!)
- Result: 5-minute delay instead of <1s real-time

### Phase 5 Sub-Tasks

#### Phase 5A: Foundation + Learning Tests ✅
- [x] Integration tests for WebSocket/fills APIs
- [x] Create models (NotificationState, OrderFillEvent)
- [x] Service skeletons
- [x] State persistence with atomic writes

#### Phase 5B: WebSocket Implementation 🔄
- [x] WebSocket connection and subscription
- [x] Real-time fill event processing
- [x] Heartbeat tracking
- [ ] **FIX: WebSocket connection not receiving events** ⚠️
- [ ] Test reconnection logic
- [ ] Verify events are being received

#### Phase 5C: Recovery Mechanism ✅
- [x] Startup recovery (query missed fills)
- [x] Periodic backup polling (5 min safety net)
- [x] Batch notifications for >5 fills
- [x] Individual notifications for ≤5 fills

#### Phase 5D: Telegram Integration ✅
- [x] Bot integration (post_init/post_shutdown)
- [x] Notification commands:
  - [x] `/notify_status` - Show service status
  - [x] `/notify_test` - Send test notification
  - [x] `/notify_history` - Show recent fills

#### Phase 5E: Scale Order Enhancement (Future)
- [ ] Aggregate notifications for scale order groups
- [ ] "3/5 orders filled (60%)" format
- [ ] User preferences

### Current Issue: WebSocket Not Working

**Symptoms:**
```json
"last_websocket_heartbeat": "2025-11-13 14:00:02.792918+00:00"
```
- Last heartbeat 3 days ago
- Backup polling catching fills every 5 minutes
- No real-time notifications

**Investigation Needed:**
1. Check if WebSocket is actually connected
2. Verify subscription to userEvents channel
3. Check if SDK is properly threading/async
4. Test with manual WebSocket subscription
5. Check Hyperliquid SDK version

**Files to Check:**
- `src/services/order_monitor_service.py:406` - `_on_websocket_event()` callback
- `src/services/hyperliquid_service.py` - WebSocket initialization
- Hyperliquid SDK threading behavior

**Diagnostic Commands:**
```bash
# In Telegram bot
/notify_status

# Check logs for WebSocket events
tail -f logs/hyperbot.log | grep -i "websocket"

# Check if WebSocket is receiving ANY events
tail -f logs/hyperbot.log | grep "WebSocket event received"
```

---

## 🧪 Testing Lessons & Known Issues

**Last Updated**: 2025-11-06

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

#### WebSocket Connection Issues
**⚠️ CURRENT ISSUE**: WebSocket not receiving events (last heartbeat 3 days ago)

**Symptoms:**
- No real-time notifications
- Backup polling works (5-minute delay)
- No WebSocket heartbeat updates

**Possible Causes:**
- SDK threading issues
- Async event loop conflicts
- WebSocket connection dropped
- Subscription not working

#### Wizard Tests Need Synchronization
**⚠️ IMPORTANT**: When making changes to bot handlers or service imports, check if wizard tests need updates.

**Current skipped tests** in `tests/bot/test_wizards.py`:
1. `test_market_amount_selected_parsing` - Import path for `market_data_service` changed
2. `test_close_position_execute_uses_size_closed` - Handler calls `edit_message_text` twice

**Action items**:
- Update test when fixing import path
- Update assertion to check both calls: initial "⏳ Processing..." and final result message

### Test Coverage Summary
- **Total Tests**: 682 passing
- **Coverage**: 66%
- **Services with excellent coverage (>90%)**:
  - Config/Logger: 100%
  - LeverageService: 93%
  - HyperliquidService: 100%
  - MarketDataService: 98%
  - PositionService: 97%
  - ScaleOrderService: 96%
  - RiskCalculator: 95%

---

## 📝 Notes

### Recent Work (2025-11-16)

**Order Fill Notifications - WebSocket Issue:**
- Diagnosed: WebSocket not receiving events (last heartbeat Nov 13)
- Backup polling working (5-minute delay)
- Need to investigate SDK threading/async behavior
- Consider testing with manual WebSocket connection

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

**Immediate Priority**:
1. **Fix WebSocket real-time notifications**
   - Investigate why WebSocket stopped receiving events
   - Test WebSocket connection manually
   - Check SDK threading/async behavior
   - Verify subscription is active

2. **Test reconnection logic**
   - Verify reconnection works after WebSocket drop
   - Test exponential backoff

3. **Verify end-to-end**
   - Place test order on testnet
   - Verify real-time notification (<1s)
   - Verify no duplicates

**Future Enhancements**:
- Phase 5E: Scale order notifications
- User notification preferences
- Notification templates/customization

---

## 📊 Progress Summary

- **Phase 0**: ✅ 100% Complete (Foundation)
- **Phase 1A**: ✅ 100% Complete (Core Services + API)
- **Phase 1B**: ✅ 100% Complete (Web Dashboard MVP)
- **Phase 2A**: ✅ 100% Complete (Rebalancing Engine)
- **Phase 2B**: ✅ 100% Complete (Scale Orders)
- **Phase 2D**: ✅ 100% Complete (Leverage Management)
- **Phase 4**: ✅ 100% Complete (Code Consolidation & Use Case Layer)
- **Phase 5**: 🔄 85% Complete (Order Fill Notifications)
  - 5A Foundation: ✅ Complete
  - 5B WebSocket: 🔄 In Progress (WebSocket issue)
  - 5C Recovery: ✅ Complete
  - 5D Telegram: ✅ Complete
  - 5E Scale Orders: ⏳ Pending
