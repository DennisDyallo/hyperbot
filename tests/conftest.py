"""
Pytest configuration and shared fixtures.

This file provides globally available fixtures for all tests.
Enhanced with helpers from tests/helpers/ for reduced boilerplate.

Migration Guide:
    - Old fixtures are preserved for backward compatibility
    - New builder-based fixtures available for cleaner tests
    - See end of file for migration examples
"""
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

# Import helpers for use in fixtures and tests
from tests.helpers import (
    PositionBuilder,
    AccountSummaryBuilder,
    MarketDataBuilder,
    ServiceMockBuilder,
    TelegramMockFactory,
    UpdateBuilder,
    ContextBuilder
)


# =============================================================================
# Mock Data Fixtures
# =============================================================================

@pytest.fixture
def mock_asset_metadata() -> Dict[str, Any]:
    """Mock Hyperliquid asset metadata."""
    return {
        "BTC": {
            "name": "BTC",
            "szDecimals": 5,
            "maxLeverage": 50,
            "onlyIsolated": False
        },
        "ETH": {
            "name": "ETH",
            "szDecimals": 4,
            "maxLeverage": 50,
            "onlyIsolated": False
        },
        "SOL": {
            "name": "SOL",
            "szDecimals": 1,
            "maxLeverage": 20,
            "onlyIsolated": False
        }
    }


@pytest.fixture
def mock_prices() -> Dict[str, float]:
    """Mock market prices."""
    return {
        "BTC": 104088.0,
        "ETH": 3850.50,
        "SOL": 161.64,
        "ARB": 0.85,
        "AVAX": 35.20,
        "MATIC": 0.92
    }


@pytest.fixture
def mock_position_data() -> Dict[str, Any]:
    """Mock position data from Hyperliquid."""
    return {
        "position": {
            "coin": "BTC",
            "size": 0.00432,
            "entry_price": 104088.0,
            "position_value": 449.66,
            "unrealized_pnl": 5.25,
            "return_on_equity": 0.0117,
            "leverage": 2.5,
            "liquidation_price": 95000.0
        }
    }


@pytest.fixture
def mock_account_summary() -> Dict[str, Any]:
    """Mock account summary data."""
    return {
        "wallet_address": "0xF67332761483018d2e604A094d7f00cA8230e881",
        "total_account_value": 10942.58,
        "perps_account_value": 2850.25,
        "spot_account_value": 8092.33,
        "available_balance": 8500.00,
        "margin_used": 2442.58,
        "num_perp_positions": 3,
        "num_spot_balances": 5,
        "total_unrealized_pnl": 125.50,
        "cross_margin_ratio_pct": 22.35
    }


# =============================================================================
# Service Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_market_data_service(mock_prices, mock_asset_metadata):
    """Mock MarketDataService."""
    service = Mock()
    service.get_price = Mock(side_effect=lambda coin: mock_prices.get(coin))
    service.get_all_prices = Mock(return_value=mock_prices)
    service.get_asset_metadata = Mock(
        side_effect=lambda coin: mock_asset_metadata.get(coin)
    )
    return service


@pytest.fixture
def mock_order_service():
    """Mock OrderService."""
    service = Mock()
    service.place_market_order = Mock(return_value={
        "status": "success",
        "result": {"statuses": [{"filled": {"totalSz": "0.00432", "avgPx": "104088.0"}}]}
    })
    return service


@pytest.fixture
def mock_position_service(mock_position_data):
    """Mock PositionService."""
    service = Mock()
    service.get_position = Mock(return_value=mock_position_data)
    service.list_positions = Mock(return_value=[mock_position_data])
    service.close_position = Mock(return_value={
        "status": "success",
        "coin": "BTC",
        "size_closed": 0.00432,
        "result": {"status": "ok"}
    })
    return service


@pytest.fixture
def mock_account_service(mock_account_summary):
    """Mock AccountService."""
    service = Mock()
    service.get_account_summary = Mock(return_value=mock_account_summary)
    return service


# =============================================================================
# Telegram Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_telegram_update():
    """Mock Telegram Update object."""
    update = Mock()
    update.effective_user = Mock()
    update.effective_user.id = 1383283890
    update.effective_user.username = "testuser"
    update.effective_message = Mock()
    update.message = Mock()
    update.callback_query = None
    return update


@pytest.fixture
def mock_telegram_callback_query():
    """Mock Telegram CallbackQuery object."""
    query = Mock()
    query.data = "menu_main"
    query.answer = MagicMock()
    query.edit_message_text = MagicMock()
    query.from_user = Mock()
    query.from_user.id = 1383283890
    query.from_user.username = "testuser"
    return query


@pytest.fixture
def mock_telegram_context():
    """Mock Telegram Context object."""
    context = Mock()
    context.user_data = {}
    context.bot = Mock()
    context.bot.send_message = MagicMock()
    return context


# =============================================================================
# Hyperliquid SDK Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_hyperliquid_info():
    """Mock Hyperliquid Info API client."""
    info = Mock()
    info.all_mids = Mock(return_value={
        "BTC": "104088.0",
        "ETH": "3850.50",
        "SOL": "161.64"
    })
    info.user_state = Mock(return_value={
        "marginSummary": {
            "accountValue": "10942.58",
            "totalMarginUsed": "2442.58"
        },
        "assetPositions": []
    })
    info.meta = Mock(return_value={
        "universe": [
            {"name": "BTC", "szDecimals": 5},
            {"name": "ETH", "szDecimals": 4},
            {"name": "SOL", "szDecimals": 1}
        ]
    })
    return info


@pytest.fixture
def mock_hyperliquid_exchange():
    """Mock Hyperliquid Exchange API client."""
    exchange = Mock()
    exchange.market_open = Mock(return_value={
        "status": "ok",
        "response": {
            "type": "order",
            "data": {"statuses": [{"filled": {"totalSz": "0.00432", "avgPx": "104088.0"}}]}
        }
    })
    exchange.market_close = Mock(return_value={
        "status": "ok",
        "response": {
            "type": "order",
            "data": {"statuses": [{"filled": {"totalSz": "0.00432", "avgPx": "104088.0"}}]}
        }
    })
    return exchange


@pytest.fixture
def mock_hyperliquid_service(mock_hyperliquid_info, mock_hyperliquid_exchange):
    """Mock HyperliquidService singleton."""
    service = Mock()
    service.is_initialized = Mock(return_value=True)
    service.get_info_client = Mock(return_value=mock_hyperliquid_info)
    service.get_exchange_client = Mock(return_value=mock_hyperliquid_exchange)
    service.initialize = Mock()
    service.health_check = Mock(return_value={"status": "healthy"})
    return service


# Note: Removed autouse fixture for hyperliquid_service patching
# Tests should use mock_hyperliquid_service fixture directly and patch as needed


# =============================================================================
# New Builder Fixtures (For convenience in tests)
# =============================================================================

@pytest.fixture
def position_builder():
    """
    Fixture that returns a fresh PositionBuilder instance.

    Example:
        def test_something(position_builder):
            position = position_builder.with_coin("ETH").with_size(10).build()
    """
    return PositionBuilder()


@pytest.fixture
def account_summary_builder():
    """
    Fixture that returns a fresh AccountSummaryBuilder instance.

    Example:
        def test_something(account_summary_builder):
            summary = account_summary_builder.with_total_value(50000).build()
    """
    return AccountSummaryBuilder()


@pytest.fixture
def market_data_builder():
    """
    Fixture that returns a fresh MarketDataBuilder instance.

    Example:
        def test_something(market_data_builder):
            prices = market_data_builder.with_price("DOGE", 0.12).build_prices()
    """
    return MarketDataBuilder()


@pytest.fixture
def update_builder():
    """
    Fixture that returns a fresh UpdateBuilder instance.

    Example:
        def test_something(update_builder):
            update = update_builder.with_message().with_text("/start").build()
    """
    return UpdateBuilder()


@pytest.fixture
def context_builder():
    """
    Fixture that returns a fresh ContextBuilder instance.

    Example:
        def test_something(context_builder):
            context = context_builder.with_user_data({"coin": "BTC"}).build()
    """
    return ContextBuilder()


# =============================================================================
# Additional Service Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_leverage_service():
    """
    Mock LeverageService with common methods configured.

    Example usage:
        def test_something(mock_leverage_service):
            mock_leverage_service.get_coin_leverage.return_value = 5
    """
    return ServiceMockBuilder.leverage_service()


@pytest.fixture
def mock_rebalance_service():
    """
    Mock RebalanceService with common methods configured.

    Example usage:
        def test_something(mock_rebalance_service):
            mock_rebalance_service.calculate_current_allocation.return_value = {}
    """
    return ServiceMockBuilder.rebalance_service()


# =============================================================================
# User ID Fixtures for Authorization Testing
# =============================================================================

@pytest.fixture
def authorized_user_id() -> int:
    """Return the default authorized user ID (1383283890)."""
    return 1383283890


@pytest.fixture
def unauthorized_user_id() -> int:
    """Return an unauthorized user ID for testing access control (999999999)."""
    return 999999999


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """
    Pytest configuration hook.

    Adds custom markers for categorizing tests.
    """
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (requires real services)"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests (fully mocked)"
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (may take several seconds)"
    )


# =============================================================================
# Migration Examples
# =============================================================================

"""
MIGRATION GUIDE: From Old Fixtures to New Helpers
==================================================

The test suite now has helpers in tests/helpers/ that reduce boilerplate
and enforce consistent patterns from CLAUDE.md.

Example 1: Creating Position Data
----------------------------------

OLD (manual dictionary creation):
    position = {
        "position": {
            "coin": "BTC",
            "size": "0.5",
            "entry_price": "50000.0",
            "position_value": "25000.0",
            "unrealized_pnl": "100.0",
            "leverage_value": 3
        }
    }

NEW (using PositionBuilder):
    from tests.helpers import PositionBuilder

    position = PositionBuilder()    \\
        .with_coin("BTC")           \\
        .with_size(0.5)             \\
        .long()                     \\
        .with_pnl(100.0)            \\
        .with_leverage(3)           \\
        .build()


Example 2: Creating Service Mocks
----------------------------------

OLD (manual Mock setup):
    @pytest.fixture
    def mock_position_service(self):
        mock = Mock()
        mock.list_positions = Mock(return_value=[])
        mock.get_position = Mock(return_value=None)
        mock.close_position = Mock()
        return mock

NEW (using ServiceMockBuilder):
    from tests.helpers import ServiceMockBuilder

    # In fixture or directly in test:
    mock_position_service = ServiceMockBuilder.position_service()
    mock_position_service.list_positions.return_value = [position_data]


Example 3: Service with Mocked Dependencies
--------------------------------------------

OLD (manual patching):
    @pytest.fixture
    def service(self, mock_hyperliquid_service, mock_position_service):
        with patch('src.services.leverage_service.hyperliquid_service', mock_hyperliquid_service):
            with patch('src.services.leverage_service.position_service', mock_position_service):
                svc = LeverageService()
                return svc

NEW (using create_service_with_mocks):
    from tests.helpers import create_service_with_mocks, ServiceMockBuilder

    @pytest.fixture
    def service(self):
        return create_service_with_mocks(
            LeverageService,
            'src.services.leverage_service',
            {
                'hyperliquid_service': ServiceMockBuilder.hyperliquid_service(),
                'position_service': ServiceMockBuilder.position_service()
            }
        )


Example 4: Telegram Update Mocks
---------------------------------

OLD (manual Update creation):
    update = Mock()
    update.message = Mock()
    update.message.reply_text = AsyncMock()
    update.effective_user = Mock()
    update.effective_user.id = 1383283890

NEW (using TelegramMockFactory):
    from tests.helpers import TelegramMockFactory

    # Command update
    update = TelegramMockFactory.create_command_update("/start")

    # Callback query
    update = TelegramMockFactory.create_callback_update("menu_main")

    # Or use builder for custom config
    from tests.helpers import UpdateBuilder

    update = UpdateBuilder()                \\
        .with_message()                     \\
        .with_user(id=1383283890)           \\
        .with_text("/start")                \\
        .build()


Example 5: Common Assertions
-----------------------------

OLD (manual assertion):
    assert result == pytest.approx(expected, abs=0.01)
    call_args = mock.call_args
    assert call_args[1]["param"] == value

NEW (using assertion helpers):
    from tests.helpers import assert_float_approx, assert_service_called_with_params

    assert_float_approx(result, expected, precision=0.01)
    assert_service_called_with_params(
        mock_service,
        'method_name',
        param=value
    )


Benefits of Migration:
----------------------
1. ✅ Less boilerplate (50-70% reduction in fixture code)
2. ✅ Consistent patterns enforced from CLAUDE.md
3. ✅ Fluent interface improves readability
4. ✅ Type safety with builders (IDE autocomplete)
5. ✅ Centralized mock data maintenance
6. ✅ Easier to add new test cases

Migration is OPTIONAL - all old fixtures still work!
Migrate incrementally as you update tests.
"""
