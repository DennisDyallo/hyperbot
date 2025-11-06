"""
Unit tests for AccountService.

Tests account summary field names to catch bugs like the 'account_equity' KeyError.

MIGRATED: Now using tests/helpers for service mocking.
- create_service_with_mocks replaces manual fixture boilerplate
- ServiceMockBuilder provides pre-configured hyperliquid mock
"""
import pytest
from unittest.mock import Mock
from src.services.account_service import AccountService

# Import helpers for cleaner service mocking
from tests.helpers import create_service_with_mocks, ServiceMockBuilder


class TestAccountService:
    """Test AccountService methods."""

    @pytest.fixture
    def service(self):
        """Create AccountService instance with mocked hyperliquid_service."""
        mock_hl = ServiceMockBuilder.hyperliquid_service()
        mock_hl.wallet_address = "0xF67332761483018d2e604A094d7f00cA8230e881"

        return create_service_with_mocks(
            AccountService,
            'src.services.account_service',
            {
                'hyperliquid_service': mock_hl
            }
        )

    @pytest.fixture
    def mock_user_state(self):
        """Mock user_state response from Hyperliquid."""
        return {
            "marginSummary": {
                "accountValue": "10942.576720",
                "totalMarginUsed": "2442.576720",
                "withdrawable": "8500.000000",
                "totalRawUsd": "8500.000000",  # Used for available_balance
                "totalNtlPos": "2442.576720"   # Total notional position value
            },
            "crossMarginSummary": {
                "accountValue": "10942.576720",
                "totalMarginUsed": "2442.576720",
                "withdrawable": "8500.000000"
            },
            "assetPositions": [
                {
                    "position": {
                        "coin": "BTC",
                        "szi": "0.00432",
                        "leverage": {"type": "cross", "value": 2},
                        "entryPx": "104088.0",
                        "positionValue": "449.660416",
                        "unrealizedPnl": "5.25",
                        "returnOnEquity": "0.0117",
                        "liquidationPx": "95000.0"
                    }
                },
                {
                    "position": {
                        "coin": "SOL",
                        "szi": "1.2",
                        "leverage": {"type": "cross", "value": 3},
                        "entryPx": "161.64",
                        "positionValue": "193.968",
                        "unrealizedPnl": "2.15",
                        "returnOnEquity": "0.0111",
                        "liquidationPx": "140.0"
                    }
                }
            ],
            "crossMaintenanceMarginUsed": "50.12"
        }

    def test_get_account_summary_field_names(self, service, mock_user_state):
        """
        Test that get_account_summary returns correct field names.

        Bug Fix: Previously tried to access 'account_equity' which didn't exist.
        """
        mock_info = Mock()
        mock_info.user_state.return_value = mock_user_state
        mock_info.spot_user_state.return_value = {
            "balances": []  # No spot balances for this test
        }
        service.hyperliquid.get_info_client.return_value = mock_info

        summary = service.get_account_summary()

        # Verify all expected fields exist (no KeyError)
        assert "wallet_address" in summary
        assert "total_account_value" in summary
        assert "available_balance" in summary
        assert "margin_used" in summary
        assert "num_perp_positions" in summary
        assert "num_spot_balances" in summary
        assert "total_unrealized_pnl" in summary
        assert "cross_margin_ratio_pct" in summary

        # Verify field names that SHOULD NOT exist (would cause KeyError)
        assert "account_equity" not in summary  # Bug: This was used in bot handler
        assert "total_positions" not in summary  # Bug: This was used in bot handler

    def test_get_account_summary_values(self, service, mock_user_state):
        """Test that account summary calculates values correctly."""
        mock_info = Mock()
        mock_info.user_state.return_value = mock_user_state
        mock_info.spot_user_state.return_value = {
            "balances": []  # No spot balances for this test
        }
        service.hyperliquid.get_info_client.return_value = mock_info

        summary = service.get_account_summary()

        # Check calculated values
        assert summary["total_account_value"] == pytest.approx(10942.58, abs=0.01)
        assert summary["margin_used"] == pytest.approx(2442.58, abs=0.01)
        assert summary["available_balance"] == pytest.approx(8500.0, abs=0.01)
        assert summary["num_perp_positions"] == 2
        assert summary["total_unrealized_pnl"] == pytest.approx(7.40, abs=0.01)  # 5.25 + 2.15

    def test_get_account_summary_no_positions(self, service):
        """Test account summary with no open positions."""
        mock_user_state_no_pos = {
            "marginSummary": {
                "accountValue": "10000.0",
                "totalMarginUsed": "0.0",
                "withdrawable": "10000.0"
            },
            "crossMarginSummary": {
                "accountValue": "10000.0",
                "totalMarginUsed": "0.0"
            },
            "assetPositions": [],
            "crossMaintenanceMarginUsed": "0.0"
        }

        mock_info = Mock()
        mock_info.user_state.return_value = mock_user_state_no_pos
        mock_info.spot_user_state.return_value = {
            "balances": []  # No spot balances for this test
        }
        service.hyperliquid.get_info_client.return_value = mock_info

        summary = service.get_account_summary()

        assert summary["num_perp_positions"] == 0
        assert summary["total_unrealized_pnl"] == 0.0
        assert summary["margin_used"] == 0.0
