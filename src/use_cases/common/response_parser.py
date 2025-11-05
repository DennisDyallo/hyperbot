"""
Centralized response parser for Hyperliquid API responses.

This module provides a single source of truth for parsing Hyperliquid API responses
and handling errors. It eliminates duplicate code that previously existed in
position_service.py and order_service.py.
"""
from typing import Dict, Any


def parse_hyperliquid_response(result: Dict[str, Any], operation: str) -> None:
    """
    Parse Hyperliquid API response and raise exception if operation failed.

    Hyperliquid returns 'status: ok' even when operations fail. The actual
    success/failure is nested in response.data.statuses array.

    This function consolidates duplicate response parsing logic that was
    previously in both position_service.py and order_service.py.

    Args:
        result: The response from Hyperliquid API
        operation: Description of the operation (for error messages)

    Raises:
        RuntimeError: If the operation failed according to Hyperliquid (API error)
        ValueError: If the operation failed due to validation errors (user error)

    Examples:
        >>> # Success case
        >>> result = {"status": "ok", "response": {"data": {"statuses": [{"filled": {...}}]}}}
        >>> parse_hyperliquid_response(result, "Place order")  # No exception

        >>> # Error case
        >>> result = {"status": "ok", "response": {"data": {"statuses": [{"error": "Insufficient margin"}]}}}
        >>> parse_hyperliquid_response(result, "Place order")  # Raises ValueError

        >>> # API error
        >>> result = {"status": "error", "error": "Network timeout"}
        >>> parse_hyperliquid_response(result, "Place order")  # Raises RuntimeError
    """
    # Check top-level status
    if result.get("status") != "ok":
        error_msg = result.get("error", "Unknown error")
        raise RuntimeError(f"{operation} failed: {error_msg}")

    # Check nested statuses for errors
    response = result.get("response", {})
    data = response.get("data", {})
    statuses = data.get("statuses", [])

    for status in statuses:
        # Check for error field (validation errors)
        if "error" in status:
            raise ValueError(f"{operation} failed: {status['error']}")

        # Check for resting field (order placed but not filled - limit orders)
        if "resting" in status:
            # This is OK - limit orders will rest in the order book
            continue

        # Check for filled field (order filled immediately - market orders or filled limit orders)
        if "filled" in status:
            # Success case
            continue


def extract_order_id_from_response(result: Dict[str, Any]) -> int:
    """
    Extract order ID from Hyperliquid response.

    Args:
        result: The response from Hyperliquid API

    Returns:
        Order ID

    Raises:
        ValueError: If order ID cannot be extracted

    Examples:
        >>> result = {"status": "ok", "response": {"data": {"statuses": [{"resting": {"oid": 12345}}]}}}
        >>> extract_order_id_from_response(result)
        12345
    """
    response = result.get("response", {})
    data = response.get("data", {})
    statuses = data.get("statuses", [])

    if not statuses:
        raise ValueError("No statuses in response")

    status = statuses[0]

    # Check for resting order (limit order placed)
    if "resting" in status:
        oid = status["resting"].get("oid")
        if oid is not None:
            return oid

    # Check for filled order (market order executed)
    if "filled" in status:
        # For filled orders, we might not have an order ID in the traditional sense
        # but we can return 0 to indicate it was filled immediately
        return 0

    raise ValueError("Could not extract order ID from response")


def check_response_success(result: Dict[str, Any]) -> bool:
    """
    Check if Hyperliquid response indicates success.

    This is a non-throwing version of parse_hyperliquid_response() for cases
    where you want to check success without exception handling.

    Args:
        result: The response from Hyperliquid API

    Returns:
        True if successful, False otherwise

    Examples:
        >>> result = {"status": "ok", "response": {"data": {"statuses": [{"filled": {...}}]}}}
        >>> check_response_success(result)
        True

        >>> result = {"status": "ok", "response": {"data": {"statuses": [{"error": "Failed"}]}}}
        >>> check_response_success(result)
        False
    """
    try:
        parse_hyperliquid_response(result, "Check")
        return True
    except (ValueError, RuntimeError):
        return False
