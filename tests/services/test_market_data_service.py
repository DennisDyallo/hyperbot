"""
Unit tests for MarketDataService.

Tests market data fetching methods for prices, order books, and metadata.
"""
import pytest
from unittest.mock import Mock, patch
from src.services.market_data_service import MarketDataService


class TestMarketDataService:
    """Test MarketDataService methods."""

    @pytest.fixture
    def mock_hyperliquid_service(self):
        """Mock HyperliquidService."""
        mock_hl = Mock()
        mock_hl.is_initialized.return_value = True
        return mock_hl

    @pytest.fixture
    def service(self, mock_hyperliquid_service):
        """Create MarketDataService instance with mocked dependencies."""
        with patch('src.services.market_data_service.hyperliquid_service', mock_hyperliquid_service):
            svc = MarketDataService()
            # CRITICAL: Explicitly assign mocked dependency
            svc.hyperliquid = mock_hyperliquid_service
            return svc

    # ===================================================================
    # get_all_prices() tests
    # ===================================================================

    def test_get_all_prices_success(self, service, mock_hyperliquid_service):
        """Test successfully fetching all prices."""
        mock_info = Mock()
        mock_info.all_mids.return_value = {
            "BTC": "50000.5",
            "ETH": "3000.25",
            "SOL": "150.75"
        }
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        prices = service.get_all_prices()

        assert len(prices) == 3
        assert prices["BTC"] == 50000.5
        assert prices["ETH"] == 3000.25
        assert prices["SOL"] == 150.75
        # Verify converted to float
        assert isinstance(prices["BTC"], float)

    def test_get_all_prices_empty_market(self, service, mock_hyperliquid_service):
        """Test get_all_prices when market has no pairs."""
        mock_info = Mock()
        mock_info.all_mids.return_value = {}
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        prices = service.get_all_prices()

        assert len(prices) == 0
        assert prices == {}

    def test_get_all_prices_api_failure(self, service, mock_hyperliquid_service):
        """Test get_all_prices handles API failures."""
        mock_info = Mock()
        mock_info.all_mids.side_effect = Exception("API Error")
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        with pytest.raises(Exception, match="API Error"):
            service.get_all_prices()

    def test_get_all_prices_not_initialized(self, service, mock_hyperliquid_service):
        """Test get_all_prices raises when service not initialized."""
        mock_hyperliquid_service.get_info_client.side_effect = RuntimeError("not initialized")

        with pytest.raises(RuntimeError, match="not initialized"):
            service.get_all_prices()

    # ===================================================================
    # get_price() tests
    # ===================================================================

    def test_get_price_success(self, service, mock_hyperliquid_service):
        """Test successfully fetching price for specific coin."""
        mock_info = Mock()
        mock_info.all_mids.return_value = {
            "BTC": "50000.0",
            "ETH": "3000.0"
        }
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        price = service.get_price("BTC")

        assert price == 50000.0
        assert isinstance(price, float)

    def test_get_price_coin_not_found(self, service, mock_hyperliquid_service):
        """Test get_price raises when coin not found."""
        mock_info = Mock()
        mock_info.all_mids.return_value = {
            "BTC": "50000.0",
            "ETH": "3000.0"
        }
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        with pytest.raises(ValueError, match="not found"):
            service.get_price("INVALID")

    def test_get_price_shows_available_coins_on_error(self, service, mock_hyperliquid_service):
        """Test get_price error message includes available coins."""
        mock_info = Mock()
        mock_info.all_mids.return_value = {
            "BTC": "50000.0",
            "ETH": "3000.0",
            "SOL": "150.0"
        }
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        with pytest.raises(ValueError, match="Available coins:"):
            service.get_price("DOGE")

    def test_get_price_api_failure(self, service, mock_hyperliquid_service):
        """Test get_price handles API failures."""
        mock_info = Mock()
        mock_info.all_mids.side_effect = Exception("Network error")
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        with pytest.raises(Exception, match="Network error"):
            service.get_price("BTC")

    # ===================================================================
    # get_market_info() tests
    # ===================================================================

    def test_get_market_info_success(self, service, mock_hyperliquid_service):
        """Test successfully fetching market metadata."""
        mock_info = Mock()
        mock_info.meta.return_value = {
            "universe": [
                {"name": "BTC", "szDecimals": 5},
                {"name": "ETH", "szDecimals": 4}
            ]
        }
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        meta = service.get_market_info()

        assert "universe" in meta
        assert len(meta["universe"]) == 2
        assert meta["universe"][0]["name"] == "BTC"

    def test_get_market_info_empty_universe(self, service, mock_hyperliquid_service):
        """Test get_market_info with empty universe."""
        mock_info = Mock()
        mock_info.meta.return_value = {"universe": []}
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        meta = service.get_market_info()

        assert meta["universe"] == []

    def test_get_market_info_api_failure(self, service, mock_hyperliquid_service):
        """Test get_market_info handles API failures."""
        mock_info = Mock()
        mock_info.meta.side_effect = Exception("Connection timeout")
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        with pytest.raises(Exception, match="Connection timeout"):
            service.get_market_info()

    # ===================================================================
    # get_order_book() tests
    # ===================================================================

    def test_get_order_book_success(self, service, mock_hyperliquid_service):
        """Test successfully fetching order book."""
        mock_info = Mock()
        mock_info.l2_snapshot.return_value = {
            "coin": "BTC",
            "time": 1234567890,
            "levels": [
                [
                    {"px": "50000.0", "sz": "1.5", "n": 3},
                    {"px": "49999.0", "sz": "2.0", "n": 5}
                ],
                [
                    {"px": "50001.0", "sz": "1.2", "n": 2},
                    {"px": "50002.0", "sz": "0.8", "n": 1}
                ]
            ]
        }
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        book = service.get_order_book("BTC")

        assert book["coin"] == "BTC"
        assert "levels" in book
        assert len(book["levels"]) == 2
        mock_info.l2_snapshot.assert_called_once_with("BTC")

    def test_get_order_book_empty_coin(self, service, mock_hyperliquid_service):
        """Test get_order_book raises with empty coin symbol."""
        with pytest.raises(ValueError, match="Coin symbol is required"):
            service.get_order_book("")

    def test_get_order_book_none_coin(self, service, mock_hyperliquid_service):
        """Test get_order_book raises with None coin symbol."""
        with pytest.raises(ValueError, match="Coin symbol is required"):
            service.get_order_book(None)

    def test_get_order_book_api_failure(self, service, mock_hyperliquid_service):
        """Test get_order_book handles API failures."""
        mock_info = Mock()
        mock_info.l2_snapshot.side_effect = Exception("Invalid coin")
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        with pytest.raises(Exception, match="Invalid coin"):
            service.get_order_book("INVALID")

    # ===================================================================
    # get_asset_metadata() tests
    # ===================================================================

    def test_get_asset_metadata_success(self, service, mock_hyperliquid_service):
        """Test successfully fetching asset metadata."""
        mock_info = Mock()
        mock_info.meta.return_value = {
            "universe": [
                {"name": "BTC", "szDecimals": 5, "maxLeverage": 50},
                {"name": "ETH", "szDecimals": 4, "maxLeverage": 50}
            ]
        }
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        meta = service.get_asset_metadata("BTC")

        assert meta is not None
        assert meta["name"] == "BTC"
        assert meta["szDecimals"] == 5
        assert meta["maxLeverage"] == 50

    def test_get_asset_metadata_not_found(self, service, mock_hyperliquid_service):
        """Test get_asset_metadata returns None when asset not found."""
        mock_info = Mock()
        mock_info.meta.return_value = {
            "universe": [
                {"name": "BTC", "szDecimals": 5},
                {"name": "ETH", "szDecimals": 4}
            ]
        }
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        meta = service.get_asset_metadata("DOGE")

        assert meta is None

    def test_get_asset_metadata_empty_universe(self, service, mock_hyperliquid_service):
        """Test get_asset_metadata returns None with empty universe."""
        mock_info = Mock()
        mock_info.meta.return_value = {"universe": []}
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        meta = service.get_asset_metadata("BTC")

        assert meta is None

    def test_get_asset_metadata_case_sensitive(self, service, mock_hyperliquid_service):
        """Test get_asset_metadata is case-sensitive."""
        mock_info = Mock()
        mock_info.meta.return_value = {
            "universe": [
                {"name": "BTC", "szDecimals": 5}
            ]
        }
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        # Should not find lowercase
        meta = service.get_asset_metadata("btc")
        assert meta is None

        # Should find uppercase
        meta = service.get_asset_metadata("BTC")
        assert meta is not None

    def test_get_asset_metadata_api_failure(self, service, mock_hyperliquid_service):
        """Test get_asset_metadata handles API failures."""
        mock_info = Mock()
        mock_info.meta.side_effect = Exception("API Error")
        mock_hyperliquid_service.get_info_client.return_value = mock_info

        with pytest.raises(Exception, match="API Error"):
            service.get_asset_metadata("BTC")
