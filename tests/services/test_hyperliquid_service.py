"""
Unit tests for HyperliquidService.

Tests initialization, health checks, and API wrapper methods.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.hyperliquid_service import HyperliquidService


class TestHyperliquidService:
    """Test HyperliquidService methods."""

    @pytest.fixture
    def service(self):
        """Create fresh HyperliquidService instance for each test."""
        return HyperliquidService()

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with default test configuration."""
        with patch('src.services.hyperliquid_service.settings') as mock_settings:
            mock_settings.HYPERLIQUID_TESTNET = True
            mock_settings.HYPERLIQUID_WALLET_ADDRESS = "0x1234567890abcdef"
            # Valid 32-byte private key (64 hex chars)
            mock_settings.HYPERLIQUID_SECRET_KEY = "0x" + "deadbeef" * 8
            yield mock_settings

    # ===================================================================
    # __init__() tests
    # ===================================================================

    def test_init_creates_uninitialized_service(self):
        """Test that __init__ creates service in uninitialized state."""
        service = HyperliquidService()

        assert service.info is None
        assert service.exchange is None
        assert service._initialized is False

    # ===================================================================
    # initialize() tests
    # ===================================================================

    @patch('src.services.hyperliquid_service.Info')
    @patch('src.services.hyperliquid_service.Exchange')
    @patch('src.services.hyperliquid_service.Account')
    def test_initialize_success_with_full_credentials(
        self, mock_account, mock_exchange_class, mock_info_class, service, mock_settings
    ):
        """Test successful initialization with full credentials."""
        # Setup mocks
        mock_info = Mock()
        mock_exchange = Mock()
        mock_wallet = Mock()

        mock_info_class.return_value = mock_info
        mock_exchange_class.return_value = mock_exchange
        mock_account.from_key.return_value = mock_wallet

        service.initialize()

        # Verify initialization
        assert service._initialized is True
        assert service.info is mock_info
        assert service.exchange is mock_exchange

        # Verify Info was created with testnet URL
        mock_info_class.assert_called_once()
        assert "testnet" in str(mock_info_class.call_args).lower()

        # Verify Exchange was created with wallet
        mock_exchange_class.assert_called_once()
        assert mock_exchange_class.call_args.kwargs["wallet"] == mock_wallet
        assert mock_exchange_class.call_args.kwargs["account_address"] == "0x1234567890abcdef"

    @patch('src.services.hyperliquid_service.Info')
    def test_initialize_readonly_without_credentials(
        self, mock_info_class, service, mock_settings
    ):
        """Test initialization without credentials creates read-only service."""
        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None
        mock_settings.HYPERLIQUID_SECRET_KEY = None

        mock_info = Mock()
        mock_info_class.return_value = mock_info

        service.initialize()

        # Verify Info API initialized but not Exchange
        assert service._initialized is True
        assert service.info is mock_info
        assert service.exchange is None

    @patch('src.services.hyperliquid_service.Info')
    @patch('src.services.hyperliquid_service.Exchange')
    @patch('src.services.hyperliquid_service.Account')
    def test_initialize_uses_mainnet_when_testnet_false(
        self, mock_account, mock_exchange_class, mock_info_class, service, mock_settings
    ):
        """Test initialization uses mainnet URL when testnet is False."""
        mock_settings.HYPERLIQUID_TESTNET = False

        mock_info_class.return_value = Mock()
        mock_exchange_class.return_value = Mock()
        mock_account.from_key.return_value = Mock()

        service.initialize()

        # Verify mainnet URL was used (not testnet)
        call_args_str = str(mock_info_class.call_args)
        assert "mainnet" in call_args_str.lower() or "api.hyperliquid.xyz" in call_args_str

    @patch('src.services.hyperliquid_service.Info')
    def test_initialize_already_initialized_warns_and_returns(
        self, mock_info_class, service, mock_settings
    ):
        """Test that calling initialize() twice warns and returns early."""
        mock_info_class.return_value = Mock()

        # First initialization
        service.initialize()
        first_info = service.info

        # Second initialization should not replace clients
        service.initialize()

        assert service.info is first_info
        # Info should only be instantiated once
        assert mock_info_class.call_count == 1

    @patch('src.services.hyperliquid_service.Info')
    def test_initialize_handles_initialization_failure(
        self, mock_info_class, service, mock_settings
    ):
        """Test that initialization failures are properly raised."""
        mock_info_class.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            service.initialize()

        assert service._initialized is False

    # ===================================================================
    # health_check() tests
    # ===================================================================

    def test_health_check_not_initialized(self, service):
        """Test health_check returns error when not initialized."""
        result = service.health_check()

        assert result["status"] == "error"
        assert result["message"] == "Service not initialized"
        assert result["info_api"] is False
        assert result["exchange_api"] is False

    @patch('src.services.hyperliquid_service.Info')
    def test_health_check_info_api_only(self, mock_info_class, service, mock_settings):
        """Test health_check with Info API only (no Exchange)."""
        mock_info = Mock()
        mock_info.meta.return_value = {"universe": [{"name": "BTC"}, {"name": "ETH"}]}
        mock_info_class.return_value = mock_info

        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None
        mock_settings.HYPERLIQUID_SECRET_KEY = None

        service.initialize()
        result = service.health_check()

        assert result["status"] == "healthy"
        assert result["info_api"] is True
        assert result["exchange_api"] is False
        assert result["available_pairs"] == 2

    @patch('src.services.hyperliquid_service.Info')
    @patch('src.services.hyperliquid_service.Exchange')
    @patch('src.services.hyperliquid_service.Account')
    def test_health_check_full_health(
        self, mock_account, mock_exchange_class, mock_info_class, service, mock_settings
    ):
        """Test health_check with both Info and Exchange API working."""
        mock_info = Mock()
        mock_info.meta.return_value = {"universe": [{"name": "BTC"}]}
        mock_info.user_state.return_value = {
            "marginSummary": {"accountValue": "10000.50"}
        }
        mock_info_class.return_value = mock_info

        mock_exchange_class.return_value = Mock()
        mock_account.from_key.return_value = Mock()

        service.initialize()
        result = service.health_check()

        assert result["status"] == "healthy"
        assert result["info_api"] is True
        assert result["exchange_api"] is True
        assert result["account_value"] == "10000.50"
        assert result["wallet_address"] == "0x1234567890abcdef"

    @patch('src.services.hyperliquid_service.Info')
    @patch('src.services.hyperliquid_service.Exchange')
    @patch('src.services.hyperliquid_service.Account')
    def test_health_check_degraded_when_exchange_fails(
        self, mock_account, mock_exchange_class, mock_info_class, service, mock_settings
    ):
        """Test health_check returns degraded when Exchange API fails."""
        mock_info = Mock()
        mock_info.meta.return_value = {"universe": []}
        mock_info.user_state.side_effect = Exception("API Error")
        mock_info_class.return_value = mock_info

        mock_exchange_class.return_value = Mock()
        mock_account.from_key.return_value = Mock()

        service.initialize()
        result = service.health_check()

        assert result["status"] == "degraded"
        assert result["info_api"] is True
        assert result["exchange_api"] is False
        assert "exchange_api_error" in result

    @patch('src.services.hyperliquid_service.Info')
    def test_health_check_unhealthy_when_info_fails(
        self, mock_info_class, service, mock_settings
    ):
        """Test health_check returns unhealthy when Info API fails."""
        mock_info = Mock()
        mock_info.meta.side_effect = Exception("Connection timeout")
        mock_info_class.return_value = mock_info

        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None
        mock_settings.HYPERLIQUID_SECRET_KEY = None

        service.initialize()
        result = service.health_check()

        assert result["status"] == "unhealthy"
        assert result["info_api"] is False
        assert "info_api_error" in result

    # ===================================================================
    # get_info_client() tests
    # ===================================================================

    @patch('src.services.hyperliquid_service.Info')
    def test_get_info_client_success(self, mock_info_class, service, mock_settings):
        """Test get_info_client returns Info instance when initialized."""
        mock_info = Mock()
        mock_info_class.return_value = mock_info

        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None
        mock_settings.HYPERLIQUID_SECRET_KEY = None

        service.initialize()
        client = service.get_info_client()

        assert client is mock_info

    def test_get_info_client_not_initialized(self, service):
        """Test get_info_client raises when not initialized."""
        with pytest.raises(RuntimeError, match="not initialized"):
            service.get_info_client()

    # ===================================================================
    # get_exchange_client() tests
    # ===================================================================

    @patch('src.services.hyperliquid_service.Info')
    @patch('src.services.hyperliquid_service.Exchange')
    @patch('src.services.hyperliquid_service.Account')
    def test_get_exchange_client_success(
        self, mock_account, mock_exchange_class, mock_info_class, service, mock_settings
    ):
        """Test get_exchange_client returns Exchange instance when initialized."""
        mock_exchange = Mock()
        mock_info_class.return_value = Mock()
        mock_exchange_class.return_value = mock_exchange
        mock_account.from_key.return_value = Mock()

        service.initialize()
        client = service.get_exchange_client()

        assert client is mock_exchange

    def test_get_exchange_client_not_initialized(self, service):
        """Test get_exchange_client raises when not initialized."""
        with pytest.raises(RuntimeError, match="not initialized"):
            service.get_exchange_client()

    @patch('src.services.hyperliquid_service.Info')
    def test_get_exchange_client_not_available(
        self, mock_info_class, service, mock_settings
    ):
        """Test get_exchange_client raises when Exchange not available."""
        mock_info_class.return_value = Mock()
        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None
        mock_settings.HYPERLIQUID_SECRET_KEY = None

        service.initialize()

        with pytest.raises(RuntimeError, match="Exchange API not available"):
            service.get_exchange_client()

    # ===================================================================
    # is_initialized() tests
    # ===================================================================

    def test_is_initialized_false_initially(self, service):
        """Test is_initialized returns False before initialization."""
        assert service.is_initialized() is False

    @patch('src.services.hyperliquid_service.Info')
    def test_is_initialized_true_after_init(
        self, mock_info_class, service, mock_settings
    ):
        """Test is_initialized returns True after initialization."""
        mock_info_class.return_value = Mock()
        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None
        mock_settings.HYPERLIQUID_SECRET_KEY = None

        service.initialize()

        assert service.is_initialized() is True

    # ===================================================================
    # place_limit_order() tests (async)
    # ===================================================================

    @pytest.mark.asyncio
    @patch('src.services.hyperliquid_service.Info')
    @patch('src.services.hyperliquid_service.Exchange')
    @patch('src.services.hyperliquid_service.Account')
    async def test_place_limit_order_success(
        self, mock_account, mock_exchange_class, mock_info_class, service, mock_settings
    ):
        """Test successfully placing a limit order."""
        mock_exchange = Mock()
        mock_exchange.order.return_value = {
            "status": "ok",
            "response": {"data": {"statuses": [{"resting": {"oid": 12345}}]}}
        }

        mock_info_class.return_value = Mock()
        mock_exchange_class.return_value = mock_exchange
        mock_account.from_key.return_value = Mock()

        service.initialize()
        result = await service.place_limit_order(
            coin="BTC", is_buy=True, size=0.5, price=50000.0
        )

        assert result["status"] == "ok"
        mock_exchange.order.assert_called_once_with(
            name="BTC",
            is_buy=True,
            sz=0.5,
            limit_px=50000.0,
            order_type={"limit": {"tif": "Gtc"}},
            reduce_only=False
        )

    @pytest.mark.asyncio
    @patch('src.services.hyperliquid_service.Info')
    @patch('src.services.hyperliquid_service.Exchange')
    @patch('src.services.hyperliquid_service.Account')
    async def test_place_limit_order_with_custom_tif(
        self, mock_account, mock_exchange_class, mock_info_class, service, mock_settings
    ):
        """Test placing limit order with custom time-in-force."""
        mock_exchange = Mock()
        mock_exchange.order.return_value = {"status": "ok"}

        mock_info_class.return_value = Mock()
        mock_exchange_class.return_value = mock_exchange
        mock_account.from_key.return_value = Mock()

        service.initialize()
        await service.place_limit_order(
            coin="ETH", is_buy=False, size=10.0, price=3000.0,
            reduce_only=True, time_in_force="Ioc"
        )

        call_args = mock_exchange.order.call_args
        assert call_args.kwargs["order_type"] == {"limit": {"tif": "Ioc"}}
        assert call_args.kwargs["reduce_only"] is True

    @pytest.mark.asyncio
    async def test_place_limit_order_not_initialized(self, service):
        """Test place_limit_order raises when not initialized."""
        with pytest.raises(RuntimeError, match="Exchange API not initialized"):
            await service.place_limit_order(
                coin="BTC", is_buy=True, size=0.5, price=50000.0
            )

    @pytest.mark.asyncio
    @patch('src.services.hyperliquid_service.Info')
    @patch('src.services.hyperliquid_service.Exchange')
    @patch('src.services.hyperliquid_service.Account')
    async def test_place_limit_order_api_failure(
        self, mock_account, mock_exchange_class, mock_info_class, service, mock_settings
    ):
        """Test place_limit_order handles API failures."""
        mock_exchange = Mock()
        mock_exchange.order.side_effect = Exception("Network error")

        mock_info_class.return_value = Mock()
        mock_exchange_class.return_value = mock_exchange
        mock_account.from_key.return_value = Mock()

        service.initialize()

        with pytest.raises(Exception, match="Network error"):
            await service.place_limit_order(
                coin="BTC", is_buy=True, size=0.5, price=50000.0
            )

    # ===================================================================
    # cancel_order() tests (async)
    # ===================================================================

    @pytest.mark.asyncio
    @patch('src.services.hyperliquid_service.Info')
    @patch('src.services.hyperliquid_service.Exchange')
    @patch('src.services.hyperliquid_service.Account')
    async def test_cancel_order_success(
        self, mock_account, mock_exchange_class, mock_info_class, service, mock_settings
    ):
        """Test successfully canceling an order."""
        mock_exchange = Mock()
        mock_exchange.cancel.return_value = {
            "status": "ok",
            "response": {"data": {"statuses": ["success"]}}
        }

        mock_info_class.return_value = Mock()
        mock_exchange_class.return_value = mock_exchange
        mock_account.from_key.return_value = Mock()

        service.initialize()
        result = await service.cancel_order(coin="BTC", order_id=12345)

        assert result["status"] == "ok"
        mock_exchange.cancel.assert_called_once_with(name="BTC", oid=12345)

    @pytest.mark.asyncio
    async def test_cancel_order_not_initialized(self, service):
        """Test cancel_order raises when not initialized."""
        with pytest.raises(RuntimeError, match="Exchange API not initialized"):
            await service.cancel_order(coin="BTC", order_id=12345)

    @pytest.mark.asyncio
    @patch('src.services.hyperliquid_service.Info')
    @patch('src.services.hyperliquid_service.Exchange')
    @patch('src.services.hyperliquid_service.Account')
    async def test_cancel_order_api_failure(
        self, mock_account, mock_exchange_class, mock_info_class, service, mock_settings
    ):
        """Test cancel_order handles API failures."""
        mock_exchange = Mock()
        mock_exchange.cancel.side_effect = Exception("Order not found")

        mock_info_class.return_value = Mock()
        mock_exchange_class.return_value = mock_exchange
        mock_account.from_key.return_value = Mock()

        service.initialize()

        with pytest.raises(Exception, match="Order not found"):
            await service.cancel_order(coin="BTC", order_id=99999)

    # ===================================================================
    # get_open_orders() tests (async)
    # ===================================================================

    @pytest.mark.asyncio
    @patch('src.services.hyperliquid_service.Info')
    async def test_get_open_orders_success(
        self, mock_info_class, service, mock_settings
    ):
        """Test successfully getting open orders."""
        mock_info = Mock()
        mock_info.open_orders.return_value = [
            {"coin": "BTC", "oid": 123},
            {"coin": "ETH", "oid": 124}
        ]
        mock_info_class.return_value = mock_info

        mock_settings.HYPERLIQUID_WALLET_ADDRESS = "0x1234567890abcdef"
        mock_settings.HYPERLIQUID_SECRET_KEY = None

        service.initialize()
        orders = await service.get_open_orders()

        assert len(orders) == 2
        assert orders[0]["coin"] == "BTC"
        mock_info.open_orders.assert_called_once_with("0x1234567890abcdef")

    @pytest.mark.asyncio
    async def test_get_open_orders_not_initialized(self, service):
        """Test get_open_orders raises when not initialized."""
        with pytest.raises(RuntimeError, match="Service not initialized"):
            await service.get_open_orders()

    @pytest.mark.asyncio
    @patch('src.services.hyperliquid_service.Info')
    async def test_get_open_orders_no_wallet_address(
        self, mock_info_class, service, mock_settings
    ):
        """Test get_open_orders raises when wallet address not configured."""
        mock_info_class.return_value = Mock()
        mock_settings.HYPERLIQUID_WALLET_ADDRESS = None
        mock_settings.HYPERLIQUID_SECRET_KEY = None

        service.initialize()

        with pytest.raises(RuntimeError, match="Wallet address not configured"):
            await service.get_open_orders()

    @pytest.mark.asyncio
    @patch('src.services.hyperliquid_service.Info')
    async def test_get_open_orders_api_failure(
        self, mock_info_class, service, mock_settings
    ):
        """Test get_open_orders handles API failures."""
        mock_info = Mock()
        mock_info.open_orders.side_effect = Exception("API Error")
        mock_info_class.return_value = mock_info

        service.initialize()

        with pytest.raises(Exception, match="API Error"):
            await service.get_open_orders()
