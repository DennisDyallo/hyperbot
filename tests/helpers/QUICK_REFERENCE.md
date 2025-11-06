# Test Helpers Quick Reference

⚡ **Quick lookup for common testing patterns**

---

## 🔧 Service Mocking

### Create Service with Dependencies
```python
from tests.helpers import create_service_with_mocks, ServiceMockBuilder

service = create_service_with_mocks(
    LeverageService,
    'src.services.leverage_service',
    {
        'hyperliquid_service': ServiceMockBuilder.hyperliquid_service(),
        'position_service': ServiceMockBuilder.position_service()
    }
)
```

### Pre-configured Service Mocks
```python
from tests.helpers import ServiceMockBuilder

mock_hl = ServiceMockBuilder.hyperliquid_service()
mock_pos = ServiceMockBuilder.position_service()
mock_ord = ServiceMockBuilder.order_service()
mock_acc = ServiceMockBuilder.account_service()
mock_mkt = ServiceMockBuilder.market_data_service({"BTC": 50000.0})
mock_lev = ServiceMockBuilder.leverage_service()
mock_reb = ServiceMockBuilder.rebalance_service()
```

---

## 📦 Data Builders

### Position
```python
from tests.helpers import PositionBuilder

# Long position
position = PositionBuilder()      \
    .with_coin("BTC")             \
    .with_size(0.5)               \
    .long()                       \
    .with_pnl(100.0)              \
    .with_leverage(5)             \
    .build()

# Short position
position = PositionBuilder()      \
    .with_coin("ETH")             \
    .with_size(10.0)              \
    .short()                      \
    .with_pnl(-50.0)              \
    .build()

# Quick helpers
from tests.helpers import make_long_position, make_short_position
pos = make_long_position("BTC", 0.5)
pos = make_short_position("ETH", 10.0)
```

### Account Summary
```python
from tests.helpers import AccountSummaryBuilder

summary = AccountSummaryBuilder() \
    .with_total_value(10000.0)   \
    .with_available_balance(5000)\
    .with_pnl(150.0)              \
    .with_positions(3)            \
    .testnet()                    \
    .build()
```

### Market Data
```python
from tests.helpers import MarketDataBuilder

# Prices
builder = MarketDataBuilder()
prices = builder.with_price("DOGE", 0.12).build_prices()

# Metadata
metadata = builder.with_metadata("DOGE", sz_decimals=0).build_metadata("DOGE")
```

### Order Response
```python
from tests.helpers import OrderResponseBuilder

response = OrderResponseBuilder()  \
    .success()                     \
    .with_filled_size(0.5)         \
    .with_avg_price(50100.0)       \
    .build()
```

---

## 📱 Telegram Mocks

### Factory Methods (Fast)
```python
from tests.helpers import TelegramMockFactory

# Command update
update = TelegramMockFactory.create_command_update("/start")

# Text message
update = TelegramMockFactory.create_text_update("Hello bot")

# Callback query
update = TelegramMockFactory.create_callback_update("menu_main")

# Authorized user
update = TelegramMockFactory.create_authorized_update("/buy")

# Unauthorized user
update = TelegramMockFactory.create_unauthorized_update("/buy")

# Context
context = TelegramMockFactory.create_context({"coin": "BTC"})
```

### Builder (Custom Config)
```python
from tests.helpers import UpdateBuilder, ContextBuilder

# Update with message
update = UpdateBuilder()                \
    .with_message()                     \
    .with_user(id=1383283890)           \
    .with_text("/buy BTC 100")          \
    .build()

# Update with callback
update = UpdateBuilder()                  \
    .with_callback_query("menu_trade")   \
    .with_user(id=1383283890)            \
    .build()

# Context with user data
context = ContextBuilder()                \
    .with_user_data({"coin": "BTC"})     \
    .build()
```

---

## ✅ Assertions

### Float Comparison
```python
from tests.helpers import assert_float_approx

assert_float_approx(actual, expected, precision=0.01)
assert_float_approx(100.005, 100.0)  # Passes with default 0.01 precision
```

### Telegram Messages
```python
from tests.helpers import assert_telegram_message_contains

assert_telegram_message_contains(
    mock_update.message.reply_text,
    "Success", "BTC", "0.5"  # All keywords must be present
)
```

### Service Calls
```python
from tests.helpers import assert_service_called_with_params

assert_service_called_with_params(
    mock_order_service,
    'place_market_order',
    coin="BTC",
    size=0.5,
    slippage=0.05
)
```

### Dict Contents
```python
from tests.helpers import assert_dict_contains

assert_dict_contains(
    summary,
    total=10000,
    pnl=150
)
```

### Response Success
```python
from tests.helpers import assert_response_success

response = await use_case.execute(request)
assert_response_success(response)
```

### List Length
```python
from tests.helpers import assert_list_length

assert_list_length(positions, 3, "Should have 3 positions")
```

---

## 🔀 Patching

### Multiple Services
```python
from tests.helpers import patch_services

with patch_services(
    hyperliquid='src.services.X.hyperliquid_service',
    position='src.services.X.position_service'
) as mocks:
    mocks.hyperliquid.is_initialized.return_value = True
    mocks.position.list_positions.return_value = []
    # Test code
```

### Hyperliquid Service
```python
from tests.helpers import patch_hyperliquid_service

with patch_hyperliquid_service() as mock_hl:
    mock_hl.get_info_client.return_value.user_state.return_value = {...}
    # Test code
```

### Settings Override
```python
from tests.helpers import patch_settings

with patch_settings(TELEGRAM_AUTHORIZED_USERS=[12345]):
    # Test with different authorized users
    result = handler(update, context)
```

---

## 🎯 Common Patterns

### Service Test with Position Data
```python
from tests.helpers import (
    create_service_with_mocks,
    ServiceMockBuilder,
    PositionBuilder
)

@pytest.fixture
def service(self):
    return create_service_with_mocks(
        LeverageService,
        'src.services.leverage_service',
        {
            'position_service': ServiceMockBuilder.position_service()
        }
    )

def test_something(self, service):
    position = PositionBuilder().with_coin("BTC").with_leverage(5).build()
    service.position_service.list_positions.return_value = [position]

    result = service.get_coin_leverage("BTC")

    assert result == 5
```

### Bot Handler Test
```python
from tests.helpers import TelegramMockFactory, assert_telegram_message_contains

@pytest.mark.asyncio
async def test_command_handler(self):
    update = TelegramMockFactory.create_command_update("/start")
    context = TelegramMockFactory.create_context()

    await handler(update, context)

    assert_telegram_message_contains(
        update.message.reply_text,
        "Welcome", "authorized"
    )
```

### Use Case Test
```python
from tests.helpers import (
    ServiceMockBuilder,
    assert_response_success,
    assert_service_called_with_params
)
from unittest.mock import patch

@pytest.mark.asyncio
async def test_place_order_use_case(self):
    mock_order = ServiceMockBuilder.order_service()
    mock_order.place_market_order.return_value = {"status": "success", "price": 50000.0}

    with patch('src.use_cases.trading.place_order.order_service', mock_order):
        use_case = PlaceOrderUseCase()
        response = await use_case.execute(request)

    assert_response_success(response)
    assert_service_called_with_params(
        mock_order,
        'place_market_order',
        coin="BTC",
        size=0.5
    )
```

---

## 📚 Import Cheat Sheet

```python
# Service mocking
from tests.helpers import (
    create_service_with_mocks,
    ServiceMockBuilder
)

# Data builders
from tests.helpers import (
    PositionBuilder,
    AccountSummaryBuilder,
    OrderResponseBuilder,
    MarketDataBuilder,
    make_long_position,
    make_short_position
)

# Telegram mocks
from tests.helpers import (
    TelegramMockFactory,
    UpdateBuilder,
    ContextBuilder
)

# Assertions
from tests.helpers import (
    assert_float_approx,
    assert_telegram_message_contains,
    assert_service_called_with_params,
    assert_dict_contains,
    assert_response_success,
    assert_list_length
)

# Patching
from tests.helpers import (
    patch_services,
    patch_hyperliquid_service,
    patch_settings
)
```

---

## 🆘 Troubleshooting

### "Module not found" error
```python
# ❌ Wrong
from tests.helpers.service_mocks import create_service_with_mocks

# ✅ Correct
from tests.helpers import create_service_with_mocks
```

### Service mock not working
```python
# ❌ Wrong - just patching isn't enough
with patch('src.services.X.dependency', mock):
    service = ServiceClass()  # Still has real dependency!

# ✅ Correct - use create_service_with_mocks
service = create_service_with_mocks(
    ServiceClass,
    'src.services.X',
    {'dependency': mock}
)
```

### Position structure doesn't match
```python
# ❌ Wrong - flat structure
{"coin": "BTC", "size": 0.5}

# ✅ Correct - nested structure (API format)
{"position": {"coin": "BTC", "size": "0.5"}}

# Use builder to get it right automatically
PositionBuilder().with_coin("BTC").with_size(0.5).build()
```

---

## 📖 More Help

- **Full Documentation**: `docs/TEST_REFACTORING_SUMMARY.md`
- **Migration Guide**: `tests/conftest.py` (bottom section)
- **Working Examples**: `tests/services/test_leverage_service_refactored_demo.py`
- **Module Docstrings**: Check each helper module for detailed docs

---

**Last Updated**: November 6, 2025
