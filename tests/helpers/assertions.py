"""
Common assertion helpers.

Provides reusable assertion functions to reduce boilerplate and improve test readability.
"""

from typing import Any
from unittest.mock import Mock

import pytest


def assert_float_approx(
    actual: float,
    expected: float,
    precision: float = 0.01,
    msg: str = None,  # type: ignore
) -> None:
    """
    Assert that two floats are approximately equal.

    Wrapper around pytest.approx for consistency across tests.

    Args:
        actual: Actual value
        expected: Expected value
        precision: Absolute precision (default 0.01)
        msg: Optional custom assertion message

    Example:
        >>> assert_float_approx(100.005, 100.0, precision=0.01)  # Passes
        >>> assert_float_approx(100.05, 100.0, precision=0.01)   # Fails
    """
    if msg:
        assert actual == pytest.approx(expected, abs=precision), msg
    else:
        assert actual == pytest.approx(expected, abs=precision), (
            f"Expected {expected} ± {precision}, got {actual}"
        )


def assert_telegram_message_contains(mock_reply: Mock, *keywords: str, call_index: int = 0) -> None:
    """
    Assert that a Telegram reply message contains all specified keywords.

    Works with both reply_text and edit_message_text calls.

    Args:
        mock_reply: Mock object for reply_text or edit_message_text
        *keywords: Keywords that should all appear in the message
        call_index: Which call to check (default 0 = first call)

    Example:
        >>> mock_update.message.reply_text = AsyncMock()
        >>> await handler(update, context)
        >>> assert_telegram_message_contains(
        ...     mock_update.message.reply_text,
        ...     "Success", "BTC", "0.5"
        ... )
    """
    assert mock_reply.called, "Mock was never called"

    # Get the message text from call args
    call_args = mock_reply.call_args_list[call_index]

    # Message could be first positional arg or 'text' kwarg
    if call_args.args:
        message_text = call_args.args[0]
    elif "text" in call_args.kwargs:
        message_text = call_args.kwargs["text"]
    else:
        raise AssertionError("Could not find message text in call args")

    # Check all keywords are present
    missing = [kw for kw in keywords if kw not in message_text]

    assert not missing, f"Message missing keywords: {missing}\nMessage was: {message_text}"


def assert_service_called_with_params(
    mock_service: Mock, method: str, **expected_params: Any
) -> None:
    """
    Assert that a service method was called with expected parameters.

    Args:
        mock_service: Mock service object
        method: Method name to check
        **expected_params: Expected parameter values

    Example:
        >>> assert_service_called_with_params(
        ...     mock_order_service,
        ...     'place_market_order',
        ...     coin="BTC",
        ...     is_buy=True,
        ...     size=0.5,
        ...     slippage=0.05
        ... )
    """
    method_mock = getattr(mock_service, method)

    assert method_mock.called, f"{method} was never called"

    call_kwargs = method_mock.call_args.kwargs

    for param_name, expected_value in expected_params.items():
        assert param_name in call_kwargs, f"Parameter '{param_name}' not found in call kwargs"

        actual_value = call_kwargs[param_name]

        # Handle float comparisons
        if isinstance(expected_value, float) and isinstance(actual_value, float):
            assert_float_approx(actual_value, expected_value)
        else:
            assert actual_value == expected_value, (
                f"Parameter '{param_name}': expected {expected_value}, got {actual_value}"
            )


def assert_mock_called_n_times(mock: Mock, n: int, msg: str = None) -> None:  # type: ignore
    """
    Assert that a mock was called exactly n times.

    Args:
        mock: Mock object to check
        n: Expected number of calls
        msg: Optional custom message

    Example:
        >>> assert_mock_called_n_times(mock_service.method, 3)
    """
    actual_calls = mock.call_count
    if msg:
        assert actual_calls == n, msg
    else:
        assert actual_calls == n, f"Expected {n} calls, got {actual_calls}"


def assert_dict_contains(data: dict, **expected_items: Any) -> None:
    """
    Assert that a dictionary contains all expected key-value pairs.

    Args:
        data: Dictionary to check
        **expected_items: Expected key-value pairs

    Example:
        >>> summary = {"total": 10000, "pnl": 150}
        >>> assert_dict_contains(summary, total=10000, pnl=150)
    """
    for key, expected_value in expected_items.items():
        assert key in data, f"Key '{key}' not found in data"

        actual_value = data[key]

        if isinstance(expected_value, float) and isinstance(actual_value, float):
            assert_float_approx(actual_value, expected_value)
        else:
            assert actual_value == expected_value, (
                f"Key '{key}': expected {expected_value}, got {actual_value}"
            )


def assert_response_success(response: Any, expected_status: str = "success") -> None:
    """
    Assert that a use case response indicates success.

    Args:
        response: Response object from use case
        expected_status: Expected status value (default "success")

    Example:
        >>> response = await use_case.execute(request)
        >>> assert_response_success(response)
    """
    assert hasattr(response, "status"), "Response missing 'status' attribute"
    assert response.status == expected_status, (
        f"Expected status '{expected_status}', got '{response.status}'"
    )


def assert_list_length(items: list, expected_length: int, msg: str = None) -> None:  # type: ignore
    """
    Assert that a list has the expected length.

    Args:
        items: List to check
        expected_length: Expected length
        msg: Optional custom message

    Example:
        >>> assert_list_length(positions, 3, "Should have 3 positions")
    """
    actual_length = len(items)
    if msg:
        assert actual_length == expected_length, msg
    else:
        assert actual_length == expected_length, (
            f"Expected list length {expected_length}, got {actual_length}"
        )


def assert_no_exceptions_raised(func, *args, **kwargs) -> Any:
    """
    Assert that calling a function does not raise any exceptions.

    Args:
        func: Function to call
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Return value of the function

    Example:
        >>> result = assert_no_exceptions_raised(service.method, arg1, arg2)
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        raise AssertionError(f"Unexpected exception raised: {type(e).__name__}: {e}") from e


def assert_all_elements_match(items: list[Any], condition) -> None:
    """
    Assert that all elements in a list match a condition.

    Args:
        items: List of items to check
        condition: Callable that returns True if item matches condition

    Example:
        >>> positions = [pos1, pos2, pos3]
        >>> assert_all_elements_match(
        ...     positions,
        ...     lambda p: float(p["position"]["size"]) > 0
        ... )
    """
    for i, item in enumerate(items):
        assert condition(item), f"Item at index {i} does not match condition: {item}"


# Convenience assertion for common patterns


def assert_error_message_contains(error: Exception, *keywords: str) -> None:
    """
    Assert that an exception message contains all keywords.

    Args:
        error: Exception to check
        *keywords: Keywords that should appear in error message

    Example:
        >>> with pytest.raises(ValueError) as exc_info:
        ...     raise ValueError("Invalid coin BTC")
        >>> assert_error_message_contains(exc_info.value, "Invalid", "coin")
    """
    error_msg = str(error)
    missing = [kw for kw in keywords if kw not in error_msg]

    assert not missing, f"Error message missing keywords: {missing}\nError was: {error_msg}"
