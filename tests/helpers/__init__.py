"""
Test helpers and utilities.

This package provides reusable test fixtures, mock factories, and assertion helpers
to reduce code duplication and enforce consistent testing patterns across the test suite.

Architecture:
- service_mocks.py: Service mocking factory implementing CLAUDE.md patterns
- telegram_mocks.py: Telegram Update/Context/CallbackQuery factories
- mock_data.py: Fluent builders for test data structures
- assertions.py: Common assertion helpers
- patching.py: Context manager helpers for patching
"""

from .service_mocks import create_service_with_mocks, ServiceMockBuilder
from .telegram_mocks import TelegramMockFactory, UpdateBuilder, ContextBuilder
from .mock_data import (
    PositionBuilder,
    AccountSummaryBuilder,
    OrderResponseBuilder,
    MarketDataBuilder
)
from .assertions import (
    assert_float_approx,
    assert_telegram_message_contains,
    assert_service_called_with_params
)
from .patching import patch_services

__all__ = [
    # Service mocking
    'create_service_with_mocks',
    'ServiceMockBuilder',

    # Telegram mocking
    'TelegramMockFactory',
    'UpdateBuilder',
    'ContextBuilder',

    # Data builders
    'PositionBuilder',
    'AccountSummaryBuilder',
    'OrderResponseBuilder',
    'MarketDataBuilder',

    # Assertions
    'assert_float_approx',
    'assert_telegram_message_contains',
    'assert_service_called_with_params',

    # Patching
    'patch_services',
]
