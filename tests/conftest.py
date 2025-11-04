"""
Pytest configuration and shared fixtures.
"""
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any


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
