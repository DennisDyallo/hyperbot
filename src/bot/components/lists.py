"""Sortable list components for displaying positions and orders.

This module provides flexible list building with sorting, grouping, and formatting
capabilities for positions, orders, and other collections.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class SortOption(str, Enum):
    """Available sort options for lists."""

    RISK = "risk"
    SIZE = "size"
    PNL = "pnl"
    NAME = "name"


class SortableList(Generic[T]):
    """Build sortable lists with grouping and priority handling.

    Generic list builder that can sort and group items based on custom functions.
    Useful for positions, orders, and any other collections that need dynamic sorting.

    Example:
        >>> positions = [...]
        >>> sortable = SortableList(positions, SortOption.RISK)
        >>> sortable.register_sort(SortOption.RISK, lambda p: p['liq_distance'])
        >>> sorted_items = sortable.sort_by(SortOption.RISK)
    """

    def __init__(self, items: list[T], default_sort: SortOption = SortOption.RISK) -> None:
        """Initialize sortable list.

        Args:
            items: List of items to manage
            default_sort: Default sort option
        """
        self.items = items
        self.current_sort = default_sort
        self.sort_functions: dict[SortOption, tuple[Callable[[T], Any], bool]] = {}

    def register_sort(
        self, option: SortOption, key_func: Callable[[T], Any], reverse: bool = False
    ) -> SortableList[T]:
        """Register a sort function for an option.

        Args:
            option: Sort option to register
            key_func: Function to extract sort key from item
            reverse: Whether to reverse sort order

        Returns:
            Self for method chaining
        """
        self.sort_functions[option] = (key_func, reverse)
        return self

    def sort_by(self, option: SortOption) -> list[T]:
        """Sort items by registered option.

        Args:
            option: Sort option to use

        Returns:
            Sorted list of items (original list unchanged)
        """
        if option not in self.sort_functions:
            return self.items.copy()

        key_func, reverse = self.sort_functions[option]
        return sorted(self.items, key=key_func, reverse=reverse)

    def group_by_priority(
        self,
        priority_func: Callable[[T], bool],
        high_label: str = "⚠️ NEEDS ATTENTION",
        low_label: str = "✅ SAFE",
    ) -> tuple[list[T], list[T], str, str]:
        """Group items into high/low priority.

        Args:
            priority_func: Function returning True for high-priority items
            high_label: Label for high-priority group
            low_label: Label for low-priority group

        Returns:
            Tuple of (high_priority_items, low_priority_items, high_label, low_label)

        Example:
            >>> high, low, h_label, l_label = sortable.group_by_priority(
            ...     lambda p: p['liq_distance'] < 10
            ... )
        """
        high = [item for item in self.items if priority_func(item)]
        low = [item for item in self.items if not priority_func(item)]

        return high, low, high_label, low_label


# Preset list builders for common use cases


def build_position_list_text(
    positions: list[dict], sort_by: SortOption = SortOption.RISK, show_empty_message: bool = True
) -> str:
    """Build formatted position list with sorting.

    Creates a text representation of positions with consistent formatting
    and optional sort controls display.

    Args:
        positions: List of position dictionaries
        sort_by: Sort option to use
        show_empty_message: Whether to show message when list is empty

    Returns:
        Formatted position list text

    Example:
        >>> positions = [
        ...     {"coin": "BTC", "pnl": 100, "liq_distance": 15},
        ...     {"coin": "ETH", "pnl": -50, "liq_distance": 5}
        ... ]
        >>> text = build_position_list_text(positions, SortOption.RISK)
    """
    if not positions:
        return "📭 No open positions" if show_empty_message else ""

    # Create sortable list
    sortable = SortableList(positions, default_sort=sort_by)

    # Register sort functions
    sortable.register_sort(
        SortOption.RISK,
        lambda p: p.get("liquidation_distance_pct", 100),  # Ascending (closest first)
        reverse=False,
    )
    sortable.register_sort(
        SortOption.SIZE,
        lambda p: abs(p.get("position_value", 0)),  # Descending (largest first)
        reverse=True,
    )
    sortable.register_sort(
        SortOption.PNL,
        lambda p: p.get("unrealized_pnl", 0),  # Descending (most profit first)
        reverse=True,
    )
    sortable.register_sort(
        SortOption.NAME,
        lambda p: p.get("coin", ""),  # Alphabetical
        reverse=False,
    )

    # Get sorted positions
    sorted_positions = sortable.sort_by(sort_by)

    # Build list text
    lines = [f"📊 **Positions** (sorted by {sort_by.value})\n"]

    for pos in sorted_positions:
        coin = pos.get("coin", "UNKNOWN")
        side = pos.get("side", "UNKNOWN")
        pnl = pos.get("unrealized_pnl", 0)
        pnl_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"

        lines.append(f"{pnl_emoji} {coin} {side}")

    return "\n".join(lines)


def build_order_list_text(
    orders: list[dict], sort_by: SortOption = SortOption.NAME, show_empty_message: bool = True
) -> str:
    """Build formatted order list with sorting.

    Creates a text representation of pending orders with consistent formatting.

    Args:
        orders: List of order dictionaries
        sort_by: Sort option to use
        show_empty_message: Whether to show message when list is empty

    Returns:
        Formatted order list text
    """
    if not orders:
        return "📭 No pending orders" if show_empty_message else ""

    # Create sortable list
    sortable = SortableList(orders, default_sort=sort_by)

    # Register sort functions
    sortable.register_sort(
        SortOption.NAME,
        lambda o: o.get("coin", ""),  # Alphabetical
        reverse=False,
    )
    sortable.register_sort(
        SortOption.SIZE,
        lambda o: abs(o.get("orig_sz", 0)),  # Descending
        reverse=True,
    )

    # Get sorted orders
    sorted_orders = sortable.sort_by(sort_by)

    # Build list text
    lines = [f"📋 **Pending Orders** (sorted by {sort_by.value})\n"]

    for order in sorted_orders:
        coin = order.get("coin", "UNKNOWN")
        side = order.get("side", "UNKNOWN")
        order_type = order.get("order_type", "UNKNOWN")
        side_emoji = "🟢" if side == "BUY" else "🔴"

        lines.append(f"{side_emoji} {coin} {side} ({order_type})")

    return "\n".join(lines)
