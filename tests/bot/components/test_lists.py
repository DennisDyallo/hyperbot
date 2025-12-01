"""Tests for list components."""

from src.bot.components.lists import (
    SortableList,
    SortOption,
    build_order_list_text,
    build_position_list_text,
)


class TestSortOption:
    """Test SortOption enum."""

    def test_sort_options_exist(self) -> None:
        """Test all sort options are defined."""
        assert SortOption.RISK == "risk"
        assert SortOption.SIZE == "size"
        assert SortOption.PNL == "pnl"
        assert SortOption.NAME == "name"


class TestSortableList:
    """Test SortableList generic component."""

    def test_initialize_empty_list(self) -> None:
        """Test initializing with empty list."""
        sortable: SortableList[dict] = SortableList([], SortOption.RISK)

        assert len(sortable.items) == 0
        assert sortable.current_sort == SortOption.RISK

    def test_initialize_with_items(self) -> None:
        """Test initializing with items."""
        items = [{"value": 1}, {"value": 2}]
        sortable = SortableList(items)

        assert len(sortable.items) == 2

    def test_register_sort_function(self) -> None:
        """Test registering sort function."""
        items = [{"value": 3}, {"value": 1}, {"value": 2}]
        sortable = SortableList(items)

        sortable.register_sort(SortOption.SIZE, lambda x: x["value"])

        assert SortOption.SIZE in sortable.sort_functions

    def test_sort_by_registered_function(self) -> None:
        """Test sorting by registered function."""
        items = [{"value": 3}, {"value": 1}, {"value": 2}]
        sortable = SortableList(items)

        sortable.register_sort(SortOption.SIZE, lambda x: x["value"])
        sorted_items = sortable.sort_by(SortOption.SIZE)

        assert sorted_items[0]["value"] == 1
        assert sorted_items[1]["value"] == 2
        assert sorted_items[2]["value"] == 3

    def test_sort_by_reverse(self) -> None:
        """Test sorting in reverse order."""
        items = [{"value": 1}, {"value": 3}, {"value": 2}]
        sortable = SortableList(items)

        sortable.register_sort(SortOption.SIZE, lambda x: x["value"], reverse=True)
        sorted_items = sortable.sort_by(SortOption.SIZE)

        assert sorted_items[0]["value"] == 3
        assert sorted_items[1]["value"] == 2
        assert sorted_items[2]["value"] == 1

    def test_sort_by_unregistered_option(self) -> None:
        """Test sorting by unregistered option returns original list."""
        items = [{"value": 3}, {"value": 1}]
        sortable = SortableList(items)

        sorted_items = sortable.sort_by(SortOption.RISK)

        # Should return copy of original list
        assert len(sorted_items) == 2
        assert sorted_items[0]["value"] == 3

    def test_method_chaining(self) -> None:
        """Test method chaining for fluent API."""
        items = [{"value": 1}]
        sortable = SortableList(items)

        result = sortable.register_sort(SortOption.SIZE, lambda x: x["value"]).register_sort(
            SortOption.NAME, lambda x: x["value"]
        )

        assert result is sortable
        assert len(sortable.sort_functions) == 2

    def test_group_by_priority(self) -> None:
        """Test grouping items by priority function."""
        items = [{"risk": "high"}, {"risk": "low"}, {"risk": "high"}, {"risk": "low"}]
        sortable = SortableList(items)

        high, low, h_label, l_label = sortable.group_by_priority(lambda x: x["risk"] == "high")

        assert len(high) == 2
        assert len(low) == 2
        assert h_label == "⚠️ NEEDS ATTENTION"
        assert l_label == "✅ SAFE"

    def test_group_by_priority_custom_labels(self) -> None:
        """Test grouping with custom labels."""
        items = [{"value": 10}, {"value": 5}]
        sortable = SortableList(items)

        high, low, h_label, l_label = sortable.group_by_priority(
            lambda x: x["value"] > 7, high_label="BIG", low_label="SMALL"
        )

        assert h_label == "BIG"
        assert l_label == "SMALL"


class TestBuildPositionListText:
    """Test build_position_list_text preset."""

    def test_empty_positions(self) -> None:
        """Test empty position list."""
        result = build_position_list_text([])

        assert "No open positions" in result
        assert "📭" in result

    def test_empty_positions_no_message(self) -> None:
        """Test empty positions without message."""
        result = build_position_list_text([], show_empty_message=False)

        assert result == ""

    def test_single_position(self) -> None:
        """Test single position."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "unrealized_pnl": 100.0,
                "position_value": 1000.0,
                "liquidation_distance_pct": 15.0,
            }
        ]

        result = build_position_list_text(positions)

        assert "Positions" in result
        assert "BTC" in result
        assert "LONG" in result
        assert "🟢" in result  # Profitable

    def test_multiple_positions(self) -> None:
        """Test multiple positions."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "unrealized_pnl": 100.0,
                "position_value": 1000.0,
                "liquidation_distance_pct": 20.0,
            },
            {
                "coin": "ETH",
                "side": "SHORT",
                "unrealized_pnl": -50.0,
                "position_value": -500.0,
                "liquidation_distance_pct": 10.0,
            },
        ]

        result = build_position_list_text(positions)

        assert "BTC" in result
        assert "ETH" in result
        assert "LONG" in result
        assert "SHORT" in result

    def test_sort_by_risk(self) -> None:
        """Test sorting positions by risk."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "unrealized_pnl": 0,
                "position_value": 1000.0,
                "liquidation_distance_pct": 20.0,  # Less risky
            },
            {
                "coin": "ETH",
                "side": "LONG",
                "unrealized_pnl": 0,
                "position_value": 1000.0,
                "liquidation_distance_pct": 5.0,  # More risky
            },
        ]

        result = build_position_list_text(positions, sort_by=SortOption.RISK)

        # ETH should appear first (closer to liquidation)
        assert "sorted by risk" in result

    def test_sort_by_size(self) -> None:
        """Test sorting positions by size."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "unrealized_pnl": 0,
                "position_value": 500.0,  # Smaller
                "liquidation_distance_pct": 10.0,
            },
            {
                "coin": "ETH",
                "side": "LONG",
                "unrealized_pnl": 0,
                "position_value": 1500.0,  # Larger
                "liquidation_distance_pct": 10.0,
            },
        ]

        result = build_position_list_text(positions, sort_by=SortOption.SIZE)

        assert "sorted by size" in result

    def test_sort_by_pnl(self) -> None:
        """Test sorting positions by PnL."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "unrealized_pnl": 50.0,
                "position_value": 1000.0,
                "liquidation_distance_pct": 10.0,
            },
            {
                "coin": "ETH",
                "side": "LONG",
                "unrealized_pnl": 200.0,  # Higher PnL
                "position_value": 1000.0,
                "liquidation_distance_pct": 10.0,
            },
        ]

        result = build_position_list_text(positions, sort_by=SortOption.PNL)

        assert "sorted by pnl" in result

    def test_sort_by_name(self) -> None:
        """Test sorting positions alphabetically."""
        positions = [
            {
                "coin": "SOL",
                "side": "LONG",
                "unrealized_pnl": 0,
                "position_value": 100,
                "liquidation_distance_pct": 10,
            },
            {
                "coin": "BTC",
                "side": "LONG",
                "unrealized_pnl": 0,
                "position_value": 100,
                "liquidation_distance_pct": 10,
            },
            {
                "coin": "ETH",
                "side": "LONG",
                "unrealized_pnl": 0,
                "position_value": 100,
                "liquidation_distance_pct": 10,
            },
        ]

        result = build_position_list_text(positions, sort_by=SortOption.NAME)

        assert "sorted by name" in result

    def test_position_pnl_emoji_positive(self) -> None:
        """Test position with positive PnL shows green emoji."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "unrealized_pnl": 100.0,
                "position_value": 1000.0,
                "liquidation_distance_pct": 15.0,
            }
        ]

        result = build_position_list_text(positions)

        assert "🟢" in result

    def test_position_pnl_emoji_negative(self) -> None:
        """Test position with negative PnL shows red emoji."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "unrealized_pnl": -50.0,
                "position_value": 1000.0,
                "liquidation_distance_pct": 15.0,
            }
        ]

        result = build_position_list_text(positions)

        assert "🔴" in result

    def test_position_pnl_emoji_neutral(self) -> None:
        """Test position at breakeven shows neutral emoji."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "unrealized_pnl": 0.0,
                "position_value": 1000.0,
                "liquidation_distance_pct": 15.0,
            }
        ]

        result = build_position_list_text(positions)

        assert "⚪" in result


class TestBuildOrderListText:
    """Test build_order_list_text preset."""

    def test_empty_orders(self) -> None:
        """Test empty order list."""
        result = build_order_list_text([])

        assert "No pending orders" in result
        assert "📭" in result

    def test_empty_orders_no_message(self) -> None:
        """Test empty orders without message."""
        result = build_order_list_text([], show_empty_message=False)

        assert result == ""

    def test_single_order(self) -> None:
        """Test single order."""
        orders = [{"coin": "BTC", "side": "BUY", "order_type": "LIMIT", "orig_sz": 0.01}]

        result = build_order_list_text(orders)

        assert "Pending Orders" in result
        assert "BTC" in result
        assert "BUY" in result
        assert "LIMIT" in result
        assert "🟢" in result  # Buy emoji

    def test_multiple_orders(self) -> None:
        """Test multiple orders."""
        orders = [
            {"coin": "BTC", "side": "BUY", "order_type": "LIMIT", "orig_sz": 0.01},
            {"coin": "ETH", "side": "SELL", "order_type": "STOP", "orig_sz": 0.5},
        ]

        result = build_order_list_text(orders)

        assert "BTC" in result
        assert "ETH" in result
        assert "BUY" in result
        assert "SELL" in result

    def test_order_side_emoji_buy(self) -> None:
        """Test buy order shows green emoji."""
        orders = [{"coin": "BTC", "side": "BUY", "order_type": "LIMIT", "orig_sz": 0.01}]

        result = build_order_list_text(orders)

        assert "🟢" in result

    def test_order_side_emoji_sell(self) -> None:
        """Test sell order shows red emoji."""
        orders = [{"coin": "BTC", "side": "SELL", "order_type": "LIMIT", "orig_sz": 0.01}]

        result = build_order_list_text(orders)

        assert "🔴" in result

    def test_sort_orders_by_name(self) -> None:
        """Test sorting orders alphabetically."""
        orders = [
            {"coin": "SOL", "side": "BUY", "order_type": "LIMIT", "orig_sz": 1},
            {"coin": "BTC", "side": "BUY", "order_type": "LIMIT", "orig_sz": 1},
            {"coin": "ETH", "side": "BUY", "order_type": "LIMIT", "orig_sz": 1},
        ]

        result = build_order_list_text(orders, sort_by=SortOption.NAME)

        assert "sorted by name" in result

    def test_sort_orders_by_size(self) -> None:
        """Test sorting orders by size."""
        orders = [
            {"coin": "BTC", "side": "BUY", "order_type": "LIMIT", "orig_sz": 0.01},
            {"coin": "ETH", "side": "BUY", "order_type": "LIMIT", "orig_sz": 1.5},
        ]

        result = build_order_list_text(orders, sort_by=SortOption.SIZE)

        assert "sorted by size" in result
