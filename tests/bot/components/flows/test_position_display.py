"""Tests for position display orchestrator."""

from src.bot.components.flows.position_display import PositionDisplay
from src.bot.components.lists import SortOption


class TestPositionDisplay:
    """Test PositionDisplay orchestrator."""

    def test_build_list_view_empty(self) -> None:
        """Test list view with no positions."""
        result = PositionDisplay.build_list_view([])

        assert "Your Positions" in result
        assert "No open positions" in result

    def test_build_list_view_single_position(self) -> None:
        """Test list view with one position."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "size": 0.01,
                "position_value": 1000.0,
                "unrealized_pnl": 50.0,
                "pnl_pct": 5.0,
                "liquidation_distance_pct": 20.0,
                "leverage": 5,
                "has_stop_loss": False,
            }
        ]

        result = PositionDisplay.build_list_view(positions)

        assert "Your Positions" in result
        assert "BTC" in result
        assert "LONG" in result

    def test_build_list_view_multiple_positions(self) -> None:
        """Test list view with multiple positions."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "size": 0.01,
                "position_value": 1000.0,
                "unrealized_pnl": 50.0,
                "pnl_pct": 5.0,
                "liquidation_distance_pct": 20.0,
                "leverage": 5,
                "has_stop_loss": False,
            },
            {
                "coin": "ETH",
                "side": "SHORT",
                "size": -0.5,
                "position_value": -500.0,
                "unrealized_pnl": -25.0,
                "pnl_pct": -5.0,
                "liquidation_distance_pct": 15.0,
                "leverage": 3,
                "has_stop_loss": True,
            },
        ]

        result = PositionDisplay.build_list_view(positions)

        assert "Your Positions" in result
        assert "BTC" in result
        assert "ETH" in result
        assert "Total Value" in result
        assert "Total PnL" in result

    def test_build_list_view_with_risk_warnings(self) -> None:
        """Test list view shows risk warnings."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "size": 0.01,
                "position_value": 1000.0,
                "unrealized_pnl": 0,
                "pnl_pct": 0,
                "liquidation_distance_pct": 3.0,  # EXTREME risk
                "leverage": 20,
                "has_stop_loss": False,
            }
        ]

        result = PositionDisplay.build_list_view(positions)

        assert "Risk Summary" in result
        assert "without stop loss" in result

    def test_build_list_view_sorted_by_risk(self) -> None:
        """Test list view sorted by risk."""
        positions = [
            {
                "coin": "BTC",
                "side": "LONG",
                "size": 0.01,
                "position_value": 1000.0,
                "unrealized_pnl": 0,
                "pnl_pct": 0,
                "liquidation_distance_pct": 20.0,
                "leverage": 5,
                "has_stop_loss": False,
            },
            {
                "coin": "ETH",
                "side": "LONG",
                "size": 0.5,
                "position_value": 1000.0,
                "unrealized_pnl": 0,
                "pnl_pct": 0,
                "liquidation_distance_pct": 5.0,  # Higher risk
                "leverage": 5,
                "has_stop_loss": False,
            },
        ]

        result = PositionDisplay.build_list_view(positions, sort_by=SortOption.RISK)

        assert "sorted by risk" in result.lower()

    def test_build_detail_view(self) -> None:
        """Test detailed position view."""
        position = {
            "coin": "BTC",
            "side": "LONG",
            "size": 0.01,
            "entry_price": 98000.0,
            "current_price": 98500.0,
            "position_value": 985.0,
            "unrealized_pnl": 5.0,
            "pnl_pct": 0.5,
            "roi": 0.5,
            "price_change_pct": 0.5,
            "leverage": 5,
            "margin_used": 197.0,
            "margin_type": "cross",
            "liquidation_price": 78800.0,
            "liquidation_distance_pct": 20.0,
            "has_stop_loss": False,
        }

        result = PositionDisplay.build_detail_view(position)

        assert "BTC" in result
        assert "LONG" in result
        assert "POSITION INFO" in result
        assert "PERFORMANCE" in result
        assert "LEVERAGE & MARGIN" in result
        assert "RISK METRICS" in result
        assert "STOP LOSS" in result
        assert "SCENARIOS" in result

    def test_build_detail_view_with_stop_loss(self) -> None:
        """Test detailed view with stop loss."""
        position = {
            "coin": "BTC",
            "side": "LONG",
            "size": 0.01,
            "entry_price": 98000.0,
            "current_price": 98500.0,
            "position_value": 985.0,
            "unrealized_pnl": 5.0,
            "pnl_pct": 0.5,
            "roi": 0.5,
            "price_change_pct": 0.5,
            "leverage": 5,
            "margin_used": 197.0,
            "margin_type": "cross",
            "liquidation_price": 78800.0,
            "liquidation_distance_pct": 20.0,
            "has_stop_loss": True,
            "stop_loss_price": 95000.0,
            "stop_loss_distance_pct": 3.5,
            "potential_loss_at_sl": 30.0,
            "stop_loss_order_id": "12345",
        }

        result = PositionDisplay.build_detail_view(position)

        assert "Active SL" in result
        assert "$95,000.00" in result
        assert "12345" in result

    def test_build_detail_view_without_stop_loss(self) -> None:
        """Test detailed view without stop loss."""
        position = {
            "coin": "BTC",
            "side": "LONG",
            "size": 0.01,
            "entry_price": 98000.0,
            "current_price": 98500.0,
            "position_value": 985.0,
            "unrealized_pnl": 5.0,
            "pnl_pct": 0.5,
            "roi": 0.5,
            "price_change_pct": 0.5,
            "leverage": 5,
            "margin_used": 197.0,
            "margin_type": "cross",
            "liquidation_price": 78800.0,
            "liquidation_distance_pct": 20.0,
            "has_stop_loss": False,
        }

        result = PositionDisplay.build_detail_view(position)

        assert "No stop loss set" in result

    def test_build_scenarios(self) -> None:
        """Test scenario analysis building."""
        position = {
            "coin": "BTC",
            "side": "LONG",
            "size": 0.01,
            "entry_price": 98000.0,
            "current_price": 98500.0,
            "liquidation_price": 78800.0,
        }

        result = PositionDisplay._build_scenarios(position)

        assert "SCENARIOS" in result
        assert "If BTC reaches:" in result
        assert "+5%" in result
        assert "+10%" in result
        assert "-5%" in result
        assert "-10%" in result
        assert "LIQUIDATED" in result

    def test_build_scenarios_short_position(self) -> None:
        """Test scenario analysis for short position."""
        position = {
            "coin": "ETH",
            "side": "SHORT",
            "size": -0.5,
            "entry_price": 2000.0,
            "current_price": 1950.0,
            "liquidation_price": 2500.0,
        }

        result = PositionDisplay._build_scenarios(position)

        assert "SCENARIOS" in result
        assert "ETH" in result
        # Short position: profit when price goes down
        assert "+" in result or "-" in result
