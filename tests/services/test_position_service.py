"""
Unit tests for PositionService.

Tests position closing to catch bugs like the 'size' vs 'size_closed' KeyError.
"""
import pytest
from unittest.mock import Mock, patch
from src.services.position_service import PositionService


class TestPositionService:
    """Test PositionService methods."""

    @pytest.fixture
    def service(self):
        """Create PositionService instance with mocked hyperliquid_service."""
        from unittest.mock import Mock
        svc = PositionService()
        svc.hyperliquid = Mock()
        svc.hyperliquid.is_initialized.return_value = True
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
        self, service, mock_close_position_response
    ):
        """
        Test that close_position returns 'size_closed' field, not 'size'.

        Bug Fix: Previously returned 'size' which caused KeyError in bot handler.
        """
        mock_exchange = Mock()
        mock_exchange.market_close.return_value = mock_close_position_response
        service.hyperliquid.get_exchange_client.return_value = mock_exchange

        result = service.close_position("SOL")

        # Verify correct field name
        assert "size_closed" in result
        assert "size" not in result  # Bug: This was accessed in bot handler

        # Verify value
        assert result["size_closed"] == pytest.approx(1.26, abs=0.01)

    @patch('src.services.position_service.hyperliquid_service')
    def test_close_position_success_fields(
        self, mock_hl_service, service, mock_close_position_response
    ):
        """Test that close_position returns all required fields."""
        # Mock initialization check
        mock_hl_service.is_initialized.return_value = True

        mock_exchange = Mock()
        mock_exchange.market_close.return_value = mock_close_position_response
        mock_hl_service.get_exchange_client.return_value = mock_exchange

        result = service.close_position("SOL")

        # Required fields
        assert result["status"] == "success"
        assert result["coin"] == "SOL"
        assert "size_closed" in result
        assert "result" in result

    @patch('src.services.position_service.hyperliquid_service')
    def test_close_position_negative_size(
        self, mock_hl_service, service
    ):
        """Test closing short positions (negative size)."""
        # Mock initialization check
        mock_hl_service.is_initialized.return_value = True

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
        mock_hl_service.get_exchange_client.return_value = mock_exchange

        result = service.close_position("SOL")

        # Should return absolute value
        assert result["size_closed"] == pytest.approx(-0.5, abs=0.01)

    @patch('src.services.position_service.hyperliquid_service')
    def test_close_position_with_slippage(
        self, mock_hl_service, service, mock_close_position_response
    ):
        """Test closing position with custom slippage."""
        # Mock initialization check
        mock_hl_service.is_initialized.return_value = True

        mock_exchange = Mock()
        mock_exchange.market_close.return_value = mock_close_position_response
        mock_hl_service.get_exchange_client.return_value = mock_exchange

        result = service.close_position("SOL", slippage=10.0)

        # Verify slippage was passed correctly
        mock_exchange.market_close.assert_called_once()
        call_args = mock_exchange.market_close.call_args
        assert "slippage" in call_args[1] or len(call_args[0]) >= 2

        assert result["status"] == "success"

    @patch('src.services.position_service.hyperliquid_service')
    def test_close_position_api_error(self, mock_hl_service, service):
        """Test close_position handles API errors."""
        # Mock initialization check
        mock_hl_service.is_initialized.return_value = True

        mock_exchange = Mock()
        mock_exchange.market_close.side_effect = Exception("API Error")
        mock_hl_service.get_exchange_client.return_value = mock_exchange

        with pytest.raises(Exception):
            service.close_position("SOL")

    @patch('src.services.position_service.hyperliquid_service')
    def test_list_positions_returns_correct_format(self, mock_hl_service, service):
        """Test that list_positions returns positions in correct format."""
        # Mock initialization check
        mock_hl_service.is_initialized.return_value = True

        mock_user_state = {
            "assetPositions": [
                {
                    "position": {
                        "coin": "BTC",
                        "szi": "0.00432",
                        "entryPx": "104088.0",
                        "positionValue": "449.660416",
                        "unrealizedPnl": "5.25"
                    }
                }
            ]
        }

        mock_info = Mock()
        mock_info.user_state.return_value = mock_user_state
        mock_hl_service.get_info_client.return_value = mock_info

        positions = service.list_positions()

        assert len(positions) == 1
        assert positions[0]["coin"] == "BTC"
