"""Tests for card components."""

from src.bot.components.cards import (
    InfoCard,
    InfoField,
    build_capital_impact_card,
    build_position_summary_card,
    build_risk_assessment_card,
)


class TestInfoField:
    """Test InfoField dataclass."""

    def test_info_field_basic(self) -> None:
        """Test basic field creation."""
        field = InfoField(label="Test", value="123")

        assert field.label == "Test"
        assert field.value == "123"
        assert field.emoji == ""

    def test_info_field_with_emoji(self) -> None:
        """Test field with emoji."""
        field = InfoField(label="Test", value="123", emoji="🎯")

        assert field.emoji == "🎯"


class TestInfoCard:
    """Test InfoCard component."""

    def test_empty_card(self) -> None:
        """Test rendering empty card."""
        card = InfoCard("Test Card")
        result = card.render()

        assert "Test Card" in result
        assert "━" in result

    def test_card_with_emoji_title(self) -> None:
        """Test card with emoji in title."""
        card = InfoCard("Test Card", "🎯")
        result = card.render()

        assert "🎯 Test Card" in result

    def test_add_single_field(self) -> None:
        """Test adding single field."""
        card = InfoCard("Test")
        card.add_field("Label", "Value")
        result = card.render()

        assert "Label: Value" in result

    def test_add_multiple_fields(self) -> None:
        """Test adding multiple fields."""
        card = InfoCard("Test")
        card.add_field("Field 1", "Value 1")
        card.add_field("Field 2", "Value 2")
        card.add_field("Field 3", "Value 3")

        result = card.render()

        assert "Field 1: Value 1" in result
        assert "Field 2: Value 2" in result
        assert "Field 3: Value 3" in result

    def test_field_with_emoji(self) -> None:
        """Test field with emoji prefix."""
        card = InfoCard("Test")
        card.add_field("Label", "Value", "🟢")
        result = card.render()

        assert "🟢 Label: Value" in result

    def test_method_chaining(self) -> None:
        """Test method chaining for fluent API."""
        card = InfoCard("Test").add_field("A", "1").add_field("B", "2")

        result = card.render()

        assert "A: 1" in result
        assert "B: 2" in result

    def test_render_without_separator(self) -> None:
        """Test rendering without separator lines."""
        card = InfoCard("Test")
        card.add_field("Label", "Value")
        result = card.render(include_separator=False)

        assert "━" not in result
        assert "**Test**" in result
        assert "Label: Value" in result

    def test_render_with_separator(self) -> None:
        """Test rendering with separator lines."""
        card = InfoCard("Test")
        result = card.render(include_separator=True)

        # Should have separator before and after title
        assert result.count("━") >= 2


class TestCapitalImpactCard:
    """Test build_capital_impact_card preset."""

    def test_basic_capital_card(self) -> None:
        """Test basic capital impact card."""
        card = build_capital_impact_card(
            margin_required=200.0, margin_available=5200.0, buying_power_used_pct=3.8
        )

        result = card.render()

        assert "CAPITAL IMPACT" in result
        assert "💰" in result
        assert "$200.00" in result
        assert "$5,200.00" in result
        assert "3.8%" in result

    def test_capital_card_high_usage(self) -> None:
        """Test capital card with high buying power usage."""
        card = build_capital_impact_card(
            margin_required=4500.0, margin_available=5000.0, buying_power_used_pct=90.0
        )

        result = card.render()

        assert "$4,500.00" in result
        assert "$5,000.00" in result
        assert "90.0%" in result

    def test_capital_card_zero_margin(self) -> None:
        """Test capital card with zero margin required."""
        card = build_capital_impact_card(
            margin_required=0.0, margin_available=1000.0, buying_power_used_pct=0.0
        )

        result = card.render()

        assert "$0.00" in result
        assert "$1,000.00" in result


class TestRiskAssessmentCard:
    """Test build_risk_assessment_card preset."""

    def test_basic_risk_card(self) -> None:
        """Test basic risk assessment card."""
        card = build_risk_assessment_card(
            entry_price=50000.0,
            liquidation_price=45000.0,
            liquidation_distance_pct=10.0,
            leverage=5,
        )

        result = card.render()

        assert "RISK ASSESSMENT" in result
        assert "⚠️" in result
        assert "$50,000.00" in result
        assert "$45,000.00" in result
        assert "10.0% drop" in result

    def test_risk_card_with_stop_loss(self) -> None:
        """Test risk card with stop-loss protection."""
        card = build_risk_assessment_card(
            entry_price=50000.0,
            liquidation_price=45000.0,
            liquidation_distance_pct=10.0,
            leverage=5,
            has_stop_loss=True,
        )

        result = card.render()

        # Risk should be calculated with stop-loss consideration
        assert "RISK ASSESSMENT" in result

    def test_risk_card_extreme_risk(self) -> None:
        """Test risk card with extreme risk level."""
        card = build_risk_assessment_card(
            entry_price=50000.0,
            liquidation_price=49500.0,
            liquidation_distance_pct=1.0,  # Very close to liquidation
            leverage=20,
        )

        result = card.render()

        assert "EXTREME" in result or "CRITICAL" in result
        assert "💀" in result or "🔴" in result

    def test_risk_card_safe_level(self) -> None:
        """Test risk card with safe risk level."""
        card = build_risk_assessment_card(
            entry_price=50000.0,
            liquidation_price=25000.0,
            liquidation_distance_pct=50.0,  # Far from liquidation
            leverage=1,
        )

        result = card.render()

        assert "SAFE" in result or "LOW" in result
        assert "🟢" in result


class TestPositionSummaryCard:
    """Test build_position_summary_card preset."""

    def test_long_position_profitable(self) -> None:
        """Test long position with profit."""
        card = build_position_summary_card(
            coin="BTC",
            side="LONG",
            entry_price=50000.0,
            position_value=1000.0,
            unrealized_pnl=100.0,
            unrealized_pnl_pct=10.0,
        )

        result = card.render()

        assert "BTC LONG" in result
        assert "🟢" in result  # Long side emoji
        assert "$50,000.00" in result
        assert "$1,000.00" in result
        assert "$100.00" in result
        assert "+10.0%" in result

    def test_short_position_losing(self) -> None:
        """Test short position with loss."""
        card = build_position_summary_card(
            coin="ETH",
            side="SHORT",
            entry_price=3000.0,
            position_value=-1500.0,  # Negative for short
            unrealized_pnl=-75.0,
            unrealized_pnl_pct=-5.0,
        )

        result = card.render()

        assert "ETH SHORT" in result
        assert "🔴" in result  # Short side emoji
        assert "$3,000.00" in result
        assert "$1,500.00" in result  # Absolute value
        assert "-$75.00" in result
        assert "-5.0%" in result

    def test_position_breakeven(self) -> None:
        """Test position at breakeven."""
        card = build_position_summary_card(
            coin="SOL",
            side="LONG",
            entry_price=100.0,
            position_value=500.0,
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0,
        )

        result = card.render()

        assert "SOL LONG" in result
        assert "$0.00" in result
        assert "⚪" in result  # Neutral PnL emoji
