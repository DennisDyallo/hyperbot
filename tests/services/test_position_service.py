"""
Unit tests for PositionService.

Tests position closing to catch bugs like the 'size' vs 'size_closed' KeyError.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.position_service import PositionService


class TestPositionService:
    """Test PositionService methods."""

    @pytest.fixture
    def mock_hyperliquid_service(self):
        """Mock HyperliquidService."""
        mock_hl = Mock()
        mock_hl.is_initialized.return_value = True
        return mock_hl

    @pytest.fixture
    def mock_account_service(self):
        """Mock AccountService."""
        return Mock()

    @pytest.fixture
    def service(self, mock_hyperliquid_service, mock_account_service):
        """Create PositionService instance with mocked dependencies."""
        with patch('src.services.position_service.hyperliquid_service', mock_hyperliquid_service):
            with patch('src.services.position_service.account_service', mock_account_service):
                svc = PositionService()
                # Explicitly set the mocked dependencies
                svc.hyperliquid = mock_hyperliquid_service
                svc.account = mock_account_service
                return svc

    @pytest.fixture
    def mock_close_position_response(self):
        """Mock close_position API response from Hyperliquid."""
        return {
            "status": "ok",
            "response": {
                "type": "order",
                "data": {
                    "statuses": [
                        {
                            "filled": {
                                "totalSz": "1.26",
                                "avgPx": "161.64",
                                "oid": 42279993822
                            }
                        }
                    ]
                }
            }
        }

    def test_close_position_returns_size_closed_field(
        self, service, mock_hyperliquid_service, mock_close_position_response
    ):
        """
        Test that close_position returns 'size_closed' field, not 'size'.

        Bug Fix: Previously returned 'size' which caused KeyError in bot handler.
        """
        # Setup mocks
        mock_exchange = Mock()
        mock_exchange.market_close.return_value = mock_close_position_response
        mock_hyperliquid_service.get_exchange_client.return_value = mock_exchange

        # Mock get_position to return a position with nested structure
        service.get_position = Mock(return_value={
            "position": {
                "coin": "SOL",
                "size": 1.26
            }
        })

        result = service.close_position("SOL")

        # Verify correct field name
        assert "size_closed" in result
        assert "size" not in result  # Bug: This was accessed in bot handler

        # Verify value
        assert result["size_closed"] == pytest.approx(1.26, abs=0.01)

    def test_close_position_success_fields(
        self, service, mock_hyperliquid_service, mock_close_position_response
    ):
        """Test that close_position returns all required fields."""
        mock_exchange = Mock()
        mock_exchange.market_close.return_value = mock_close_position_response
        mock_hyperliquid_service.get_exchange_client.return_value = mock_exchange

        # Mock get_position
        service.get_position = Mock(return_value={
            "position": {
                "coin": "SOL",
                "size": 1.26
            }
        })

        result = service.close_position("SOL")

        # Required fields
        assert result["status"] == "success"
        assert result["coin"] == "SOL"
        assert "size_closed" in result
        assert "result" in result

    def test_close_position_negative_size(
        self, service, mock_hyperliquid_service
    ):
        """Test closing short positions (negative size)."""
        response = {
            "status": "ok",
            "response": {
                "type": "order",
                "data": {
                    "statuses": [
                        {
                            "filled": {
                                "totalSz": "-0.5",  # Short position
                                "avgPx": "161.64",
                                "oid": 42279993822
                            }
                        }
                    ]
                }
            }
        }

        mock_exchange = Mock()
        mock_exchange.market_close.return_value = response
        mock_hyperliquid_service.get_exchange_client.return_value = mock_exchange

        # Mock get_position
        service.get_position = Mock(return_value={
            "position": {
                "coin": "SOL",
                "size": -0.5
            }
        })

        result = service.close_position("SOL")

        # Should return the absolute value (position_service converts to positive)
        assert result["size_closed"] == pytest.approx(0.5, abs=0.01)

    def test_close_position_with_slippage(
        self, service, mock_hyperliquid_service, mock_close_position_response
    ):
        """Test closing position with custom slippage."""
        mock_exchange = Mock()
        mock_exchange.market_close.return_value = mock_close_position_response
        mock_hyperliquid_service.get_exchange_client.return_value = mock_exchange

        # Mock get_position
        service.get_position = Mock(return_value={
            "position": {
                "coin": "SOL",
                "size": 1.26
            }
        })

        result = service.close_position("SOL", slippage=10.0)

        # Verify slippage was passed correctly
        mock_exchange.market_close.assert_called_once()
        call_args = mock_exchange.market_close.call_args
        assert "slippage" in call_args[1] or len(call_args[0]) >= 2

        assert result["status"] == "success"

    def test_close_position_api_error(self, service, mock_hyperliquid_service):
        """Test close_position handles API errors."""
        mock_exchange = Mock()
        mock_exchange.market_close.side_effect = Exception("API Error")
        mock_hyperliquid_service.get_exchange_client.return_value = mock_exchange

        # Mock get_position
        service.get_position = Mock(return_value={
            "position": {
                "coin": "SOL",
                "size": 1.26
            }
        })

        with pytest.raises(Exception):
            service.close_position("SOL")

    def test_list_positions_returns_correct_format(self, service, mock_account_service):
        """Test that list_positions returns positions in correct format."""
        # Mock account service - list_positions looks for "positions" key
        mock_account_service.get_account_info.return_value = {
            "perps_account_value": 10000,
            "positions": [
                {
                    "coin": "BTC",
                    "size": 0.00432,
                    "entry_price": 104088.0,
                    "position_value": 449.66,
                    "unrealized_pnl": 5.25
                }
            ]
        }

        positions = service.list_positions()

        assert len(positions) == 1
        assert positions[0]["coin"] == "BTC"
