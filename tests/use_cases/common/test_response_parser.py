"""
Unit tests for response_parser utility.

Tests centralized Hyperliquid response parsing logic.
"""
import pytest
from src.use_cases.common.response_parser import (
    parse_hyperliquid_response,
    extract_order_id_from_response,
    check_response_success,
)


class TestParseHyperliquidResponse:
    """Test parse_hyperliquid_response function."""

    def test_success_with_filled_status(self):
        """Test successful response with filled status."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{"filled": {"totalSz": "0.01", "avgPx": "50000"}}]
                }
            }
        }
        # Should not raise
        parse_hyperliquid_response(result, "Test operation")

    def test_success_with_resting_status(self):
        """Test successful response with resting status (limit order)."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{"resting": {"oid": 12345}}]
                }
            }
        }
        # Should not raise
        parse_hyperliquid_response(result, "Place limit order")

    def test_top_level_error(self):
        """Test response with top-level error."""
        result = {
            "status": "error",
            "error": "Network timeout"
        }
        with pytest.raises(RuntimeError, match="Test operation failed: Network timeout"):
            parse_hyperliquid_response(result, "Test operation")

    def test_validation_error_in_status(self):
        """Test response with validation error in statuses."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{"error": "Insufficient margin"}]
                }
            }
        }
        with pytest.raises(ValueError, match="Test operation failed: Insufficient margin"):
            parse_hyperliquid_response(result, "Test operation")

    def test_empty_statuses(self):
        """Test response with empty statuses array."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": []
                }
            }
        }
        # Should not raise (empty statuses is OK)
        parse_hyperliquid_response(result, "Test operation")

    def test_missing_response_data(self):
        """Test response with missing response/data."""
        result = {
            "status": "ok"
        }
        # Should not raise (missing data is OK, just no statuses to check)
        parse_hyperliquid_response(result, "Test operation")

    def test_multiple_statuses_all_success(self):
        """Test response with multiple successful statuses."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [
                        {"filled": {"totalSz": "0.01"}},
                        {"resting": {"oid": 12345}},
                    ]
                }
            }
        }
        # Should not raise
        parse_hyperliquid_response(result, "Multiple orders")

    def test_multiple_statuses_one_error(self):
        """Test response with multiple statuses where one has error."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [
                        {"filled": {"totalSz": "0.01"}},
                        {"error": "Order 2 failed"},
                    ]
                }
            }
        }
        with pytest.raises(ValueError, match="Multiple orders failed: Order 2 failed"):
            parse_hyperliquid_response(result, "Multiple orders")


class TestExtractOrderIdFromResponse:
    """Test extract_order_id_from_response function."""

    def test_extract_from_resting_order(self):
        """Test extracting order ID from resting order."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{"resting": {"oid": 12345}}]
                }
            }
        }
        order_id = extract_order_id_from_response(result)
        assert order_id == 12345

    def test_extract_from_filled_order(self):
        """Test extracting from filled order (returns 0)."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{"filled": {"totalSz": "0.01"}}]
                }
            }
        }
        order_id = extract_order_id_from_response(result)
        assert order_id == 0

    def test_extract_with_no_statuses(self):
        """Test extraction fails when no statuses."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": []
                }
            }
        }
        with pytest.raises(ValueError, match="No statuses in response"):
            extract_order_id_from_response(result)

    def test_extract_with_missing_oid(self):
        """Test extraction fails when no order ID available."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{"error": "Order failed"}]
                }
            }
        }
        with pytest.raises(ValueError, match="Could not extract order ID"):
            extract_order_id_from_response(result)


class TestCheckResponseSuccess:
    """Test check_response_success function."""

    def test_success_returns_true(self):
        """Test successful response returns True."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{"filled": {}}]
                }
            }
        }
        assert check_response_success(result) is True

    def test_error_returns_false(self):
        """Test error response returns False."""
        result = {
            "status": "error",
            "error": "Failed"
        }
        assert check_response_success(result) is False

    def test_validation_error_returns_false(self):
        """Test validation error returns False."""
        result = {
            "status": "ok",
            "response": {
                "data": {
                    "statuses": [{"error": "Invalid"}]
                }
            }
        }
        assert check_response_success(result) is False
