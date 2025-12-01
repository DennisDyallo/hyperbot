"""
Telegram Bot UX Component Library.

This package provides reusable, tested components for building consistent
Telegram bot interactions following the Atomic Design methodology.

Levels:
    - Level 1 (Atomic): formatters, buttons, loading, risk
    - Level 2 (Molecular): cards, preview, lists
    - Level 3 (Organism): flows (complete user journeys)

Design Documentation:
    - docs/TELEGRAM_UX_COMPONENT_LIBRARY.md
    - docs/COMPONENT_IMPLEMENTATION_GUIDE.md
    - docs/UX_DESIGN_SPECIFICATIONS.md
"""

from .formatters import (
    format_coin_size,
    format_currency,
    format_percentage,
    format_pnl,
    format_timestamp,
)
from .risk import (
    RiskLevel,
    calculate_risk_level,
    format_risk_indicator,
    get_risk_emoji,
)

__all__ = [
    # Formatters
    "format_coin_size",
    "format_currency",
    "format_percentage",
    "format_pnl",
    "format_timestamp",
    # Risk
    "RiskLevel",
    "calculate_risk_level",
    "format_risk_indicator",
    "get_risk_emoji",
]
