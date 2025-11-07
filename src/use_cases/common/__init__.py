"""
Common utilities shared across all use cases.

This package contains centralized utilities for:
- Response parsing (Hyperliquid API responses)
- USD/Coin conversion
- Validation logic
"""

from src.use_cases.common.response_parser import (
    check_response_success,
    extract_order_id_from_response,
    parse_hyperliquid_response,
)
from src.use_cases.common.usd_converter import USDConverter
from src.use_cases.common.validators import (
    OrderValidator,
    PortfolioValidator,
    ValidationError,
)

__all__ = [
    # Response parsing
    "parse_hyperliquid_response",
    "extract_order_id_from_response",
    "check_response_success",
    # USD conversion
    "USDConverter",
    # Validation
    "ValidationError",
    "OrderValidator",
    "PortfolioValidator",
]
