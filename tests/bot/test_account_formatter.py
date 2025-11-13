"""
Unit tests for account health message formatter.

Tests the formatting logic following the UX design in docs/preliminary-ux-plan.md.
"""

import pytest

from src.bot.formatters.account import format_account_health_message
from src.bot.formatters.progress_bar import build_progress_bar, get_risk_emoji
from src.use_cases.portfolio.risk_analysis import PositionRiskDetail, RiskAnalysisResponse


class TestProgressBar:
    """Test progress bar utility functions."""

    def test_build_progress_bar_zero_percent(self):
        """Test progress bar at 0%."""
        bar = build_progress_bar(0)
        assert bar == "□□□□□□□□□□"
        assert len(bar) == 10

    def test_build_progress_bar_fifty_percent(self):
        """Test progress bar at 50%."""
        bar = build_progress_bar(50)
        assert bar == "■■■■■□□□□□"
        assert bar.count("■") == 5
        assert bar.count("□") == 5

    def test_build_progress_bar_hundred_percent(self):
        """Test progress bar at 100%."""
        bar = build_progress_bar(100)
        assert bar == "■■■■■■■■■■"
        assert len(bar) == 10

    def test_build_progress_bar_custom_length(self):
        """Test progress bar with custom length."""
        bar = build_progress_bar(50, length=5)
        assert bar == "■■□□□"
        assert len(bar) == 5

    def test_build_progress_bar_fractional_percentage(self):
        """Test progress bar with fractional percentage."""
        bar = build_progress_bar(75.5)  # Should round to 7/10
        assert bar == "■■■■■■■□□□"
        assert bar.count("■") == 7

    def test_get_risk_emoji_all_levels(self):
        """Test risk emoji mapping for all levels."""
        assert get_risk_emoji("SAFE") == "✅"
        assert get_risk_emoji("LOW") == "💚"
        assert get_risk_emoji("MODERATE") == "💛"
        assert get_risk_emoji("HIGH") == "🟠"
        assert get_risk_emoji("CRITICAL") == "🔴"

    def test_get_risk_emoji_unknown_level(self):
        """Test risk emoji with unknown level."""
        assert get_risk_emoji("UNKNOWN") == "❓"
        assert get_risk_emoji("") == "❓"


class TestAccountFormatter:
    """Test account health message formatter."""

    @pytest.fixture
    def safe_account_data(self):
        """Create mock data for safe account (health 70-100)."""
        return RiskAnalysisResponse(
            account_value=12456.78,
            perps_value=10000.00,
            spot_value=2456.78,
            available_margin=9350.0,
            total_margin_used=850.0,
            margin_utilization_pct=6.8,  # (850 / 12456.78) * 100
            cross_margin_ratio_pct=18.5,
            portfolio_health_score=92,
            overall_risk_level="SAFE",
            critical_positions=0,
            high_risk_positions=0,
            moderate_risk_positions=1,
            low_risk_positions=1,
            safe_positions=1,
            positions=[
                PositionRiskDetail(
                    coin="BTC",
                    size=1.0,
                    side="LONG",
                    entry_price=50000.0,
                    current_price=55000.0,
                    leverage=2,
                    leverage_type="cross",
                    liquidation_price=45000.0,
                    liquidation_distance_pct=50.0,
                    health_score=95,
                    risk_level="SAFE",
                    warnings=[],
                ),
                PositionRiskDetail(
                    coin="ETH",
                    size=10.0,
                    side="LONG",
                    entry_price=2000.0,
                    current_price=2100.0,
                    leverage=3,
                    leverage_type="cross",
                    liquidation_price=1800.0,
                    liquidation_distance_pct=40.0,
                    health_score=85,
                    risk_level="LOW",
                    warnings=[],
                ),
                PositionRiskDetail(
                    coin="SOL",
                    size=100.0,
                    side="LONG",
                    entry_price=100.0,
                    current_price=105.0,
                    leverage=2,
                    leverage_type="cross",
                    liquidation_price=95.0,
                    liquidation_distance_pct=35.0,
                    health_score=75,
                    risk_level="MODERATE",
                    warnings=[],
                ),
            ],
            portfolio_warnings=[],
        )

    @pytest.fixture
    def critical_account_data(self):
        """Create mock data for critical account (health 0-39)."""
        return RiskAnalysisResponse(
            account_value=12456.78,
            perps_value=11000.00,
            spot_value=1456.78,
            available_margin=400.0,
            total_margin_used=9800.0,
            margin_utilization_pct=78.7,  # (9800 / 12456.78) * 100
            cross_margin_ratio_pct=92.3,
            portfolio_health_score=12,
            overall_risk_level="CRITICAL",
            critical_positions=2,
            high_risk_positions=2,
            moderate_risk_positions=1,
            low_risk_positions=0,
            safe_positions=0,
            positions=[
                PositionRiskDetail(
                    coin="BTC",
                    size=2.0,
                    side="LONG",
                    entry_price=50000.0,
                    current_price=48500.0,
                    leverage=15,
                    leverage_type="cross",
                    liquidation_price=48000.0,
                    liquidation_distance_pct=5.2,
                    health_score=10,
                    risk_level="CRITICAL",
                    warnings=["< 8% from liquidation"],
                ),
                PositionRiskDetail(
                    coin="ETH",
                    size=20.0,
                    side="LONG",
                    entry_price=2000.0,
                    current_price=1950.0,
                    leverage=12,
                    leverage_type="cross",
                    liquidation_price=1900.0,
                    liquidation_distance_pct=7.8,
                    health_score=15,
                    risk_level="CRITICAL",
                    warnings=["High leverage (12x)"],
                ),
                PositionRiskDetail(
                    coin="SOL",
                    size=200.0,
                    side="LONG",
                    entry_price=100.0,
                    current_price=99.0,
                    leverage=8,
                    leverage_type="cross",
                    liquidation_price=98.0,
                    liquidation_distance_pct=15.0,
                    health_score=35,
                    risk_level="HIGH",
                    warnings=[],
                ),
                PositionRiskDetail(
                    coin="AVAX",
                    size=500.0,
                    side="LONG",
                    entry_price=35.0,
                    current_price=34.0,
                    leverage=6,
                    leverage_type="cross",
                    liquidation_price=32.0,
                    liquidation_distance_pct=22.0,
                    health_score=45,
                    risk_level="HIGH",
                    warnings=[],
                ),
                PositionRiskDetail(
                    coin="ARB",
                    size=1000.0,
                    side="LONG",
                    entry_price=1.5,
                    current_price=1.45,
                    leverage=4,
                    leverage_type="cross",
                    liquidation_price=1.2,
                    liquidation_distance_pct=35.0,
                    health_score=60,
                    risk_level="MODERATE",
                    warnings=[],
                ),
            ],
            portfolio_warnings=[
                "Close or reduce BTC & ETH immediately",
                "Add margin to increase safety buffer",
                "Lower leverage on all positions",
            ],
        )

    def test_format_safe_account(self, safe_account_data):
        """Test formatting of safe account (health 70-100)."""
        message = format_account_health_message(safe_account_data)

        # Verify HTML format
        assert "<b>" in message
        assert "<code>" in message

        # Verify health score section
        assert "Health Score: 92/100" in message
        assert "SAFE" in message
        assert "✅" in message

        # Verify progress bar present
        assert "■" in message
        assert "□" in message

        # Verify no critical alert banner
        assert "CRITICAL ALERT" not in message
        assert "🚨" not in message

        # Verify account values
        assert "$12,456.78" in message

        # Verify margin ratio
        assert "18.5%" in message

        # Verify position risk distribution
        assert "3 Active Position(s)" in message
        assert "Safe: 1 position(s)" in message
        assert "Low: 1 position(s)" in message
        assert "Moderate: 1 position(s)" in message

        # Verify footer
        assert "Auto-refreshes every 30s" in message
        assert "Last updated:" in message

    def test_format_critical_account(self, critical_account_data):
        """Test formatting of critical account (health 0-39)."""
        message = format_account_health_message(critical_account_data)

        # Verify critical alert banner present
        assert "🚨" in message
        assert "CRITICAL ALERT" in message
        assert "Cross Margin Ratio: <b>92.3%</b>" in message
        assert "Liquidation occurs at 100%!" in message

        # Verify critical positions listed in alert
        assert "2 position(s) at CRITICAL risk" in message
        assert "BTC: 5.2% from liquidation" in message
        assert "ETH: 7.8% from liquidation" in message

        # Verify immediate action guidance
        assert "Immediate action required:" in message
        assert "Close positions or add margin NOW" in message

        # Verify health score section
        assert "Health Score: 12/100" in message
        assert "CRITICAL" in message
        assert "🔴" in message

        # Verify critical margin ratio warning
        assert "92.3%" in message
        assert "DANGER: Liquidation at 100%!" in message

        # Verify position risk distribution
        assert "5 Active Position(s)" in message
        assert "Critical: <b>2 position(s)</b>" in message  # Emphasized
        assert "High: 2 position(s)" in message

        # Verify critical positions detailed
        assert "Critical Positions:" in message
        assert "BTC - 15x leverage" in message
        assert "ETH - 12x leverage" in message

        # Verify recommendations
        assert "Recommendations:" in message
        assert "Close or reduce BTC & ETH immediately" in message

    def test_critical_banner_shown_on_margin_threshold(self, safe_account_data):
        """Test critical banner appears when margin ratio ≥ 50%."""
        # Modify safe account to have 50% margin ratio (threshold)
        safe_account_data.cross_margin_ratio_pct = 50.0

        message = format_account_health_message(safe_account_data)

        # Should show critical banner at 50% threshold
        assert "CRITICAL ALERT" in message
        assert "Cross Margin Ratio: <b>50.0%</b>" in message

    def test_critical_banner_not_shown_below_threshold(self, safe_account_data):
        """Test critical banner NOT shown when margin < 50%."""
        # Safe account has 18.5% margin ratio
        message = format_account_health_message(safe_account_data)

        # Should NOT show critical banner
        assert "CRITICAL ALERT" not in message

    def test_margin_warning_at_seventy_percent(self, safe_account_data):
        """Test margin warning shown at 70% ratio."""
        safe_account_data.cross_margin_ratio_pct = 75.0

        message = format_account_health_message(safe_account_data)

        # Should show danger warning at ≥70%
        assert "DANGER: Liquidation at 100%!" in message

    def test_margin_warning_at_fifty_percent(self, safe_account_data):
        """Test margin warning shown at 50-69% ratio."""
        safe_account_data.cross_margin_ratio_pct = 55.0

        message = format_account_health_message(safe_account_data)

        # Should show approaching warning at 50-69%
        assert "Warning: Approaching danger zone (70%)" in message

    def test_progress_bars_rendered(self, safe_account_data):
        """Test that progress bars are rendered correctly."""
        message = format_account_health_message(safe_account_data)

        # Count progress bar characters
        filled_count = message.count("■")
        empty_count = message.count("□")

        # Should have at least 2 progress bars (health + margin)
        assert filled_count >= 2
        assert empty_count >= 2

        # Total should be 20 (2 bars × 10 chars each)
        assert filled_count + empty_count == 20

    def test_healthy_account_message(self, safe_account_data):
        """Test 'Your account is healthy!' message for safe accounts."""
        # Ensure no warnings
        safe_account_data.portfolio_warnings = []
        safe_account_data.critical_positions = 0
        safe_account_data.high_risk_positions = 0

        message = format_account_health_message(safe_account_data)

        assert "Your account is healthy!" in message

    def test_no_healthy_message_with_warnings(self, safe_account_data):
        """Test healthy message NOT shown when warnings exist."""
        safe_account_data.portfolio_warnings = ["Some warning"]

        message = format_account_health_message(safe_account_data)

        assert "Your account is healthy!" not in message
        assert "Recommendations:" in message

    def test_perps_spot_breakdown(self, safe_account_data):
        """Test that Perps/Spot breakdown is displayed."""
        message = format_account_health_message(safe_account_data)

        # Verify breakdown is shown
        assert "Perps:" in message
        assert "Spot:" in message
        assert "$10,000.00" in message  # Perps value
        assert "$2,456.78" in message  # Spot value
        assert "$12,456.78" in message  # Total value
