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

from .buttons import (
    ButtonBuilder,
    build_confirm_cancel_buttons,
    build_navigation_row,
    build_single_action_button,
)
from .cards import (
    InfoCard,
    InfoField,
    build_capital_impact_card,
    build_position_summary_card,
    build_risk_assessment_card,
)
from .flows import OrderFlowOrchestrator, OrderFlowState, PositionDisplay
from .formatters import (
    format_coin_size,
    format_currency,
    format_percentage,
    format_pnl,
    format_timestamp,
)
from .lists import (
    SortableList,
    SortOption,
    build_order_list_text,
    build_position_list_text,
)
from .loading import LoadingMessage
from .preview import PreviewBuilder, PreviewData, build_order_preview
from .risk import (
    RiskLevel,
    calculate_risk_level,
    format_risk_indicator,
    get_risk_emoji,
)

__all__ = [
    # Level 1: Formatters
    "format_coin_size",
    "format_currency",
    "format_percentage",
    "format_pnl",
    "format_timestamp",
    # Level 1: Risk
    "RiskLevel",
    "calculate_risk_level",
    "format_risk_indicator",
    "get_risk_emoji",
    # Level 1: Buttons
    "ButtonBuilder",
    "build_single_action_button",
    "build_confirm_cancel_buttons",
    "build_navigation_row",
    # Level 1: Loading
    "LoadingMessage",
    # Level 2: Cards
    "InfoCard",
    "InfoField",
    "build_capital_impact_card",
    "build_risk_assessment_card",
    "build_position_summary_card",
    # Level 2: Preview
    "PreviewBuilder",
    "PreviewData",
    "build_order_preview",
    # Level 2: Lists
    "SortableList",
    "SortOption",
    "build_position_list_text",
    "build_order_list_text",
    # Level 3: Flows
    "OrderFlowOrchestrator",
    "OrderFlowState",
    "PositionDisplay",
]
