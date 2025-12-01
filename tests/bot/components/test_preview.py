"""Tests for preview components."""

import pytest

from src.bot.components.preview import (
    PreviewBuilder,
    PreviewData,
    build_order_preview,
)


class TestPreviewData:
    """Test PreviewData dataclass."""

    def test_preview_data_required_fields(self) -> None:
        """Test creating preview data with required fields only."""
        data = PreviewData(
            coin="BTC",
            side="BUY",
            amount_usd=1000.0,
            leverage=5,
            entry_price=50000.0,
            margin_required=200.0,
            margin_available=5000.0,
            buying_power_used_pct=4.0,
            liquidation_price=45000.0,
            liquidation_distance_pct=10.0,
        )

        assert data.coin == "BTC"
        assert data.side == "BUY"
        assert data.leverage == 5

    def test_preview_data_with_optional_fields(self) -> None:
        """Test preview data with optional fields."""
        data = PreviewData(
            coin="ETH",
            side="SELL",
            amount_usd=500.0,
            leverage=3,
            entry_price=3000.0,
            margin_required=166.67,
            margin_available=2000.0,
            buying_power_used_pct=8.3,
            liquidation_price=3300.0,
            liquidation_distance_pct=10.0,
            size_coin=0.167,
            has_stop_loss=True,
            warnings=["High volatility"],
        )

        assert data.size_coin == 0.167
        assert data.has_stop_loss is True
        assert len(data.warnings) == 1


class TestPreviewBuilderQuick:
    """Test PreviewBuilder.build_quick_preview()."""

    def test_buy_order_quick_preview(self) -> None:
        """Test quick preview for buy order."""
        data = PreviewData(
            coin="BTC",
            side="BUY",
            amount_usd=1000.0,
            leverage=5,
            entry_price=50000.0,
            margin_required=200.0,
            margin_available=5000.0,
            buying_power_used_pct=4.0,
            liquidation_price=45000.0,
            liquidation_distance_pct=10.0,
        )

        result = PreviewBuilder.build_quick_preview(data)

        assert "Order Preview" in result
        assert "BTC" in result
        assert "BUY" in result
        assert "🟢" in result  # Buy emoji
        assert "$1,000.00" in result
        assert "5x" in result
        assert "$200.00" in result
        assert "$45,000.00" in result

    def test_sell_order_quick_preview(self) -> None:
        """Test quick preview for sell order."""
        data = PreviewData(
            coin="ETH",
            side="SELL",
            amount_usd=500.0,
            leverage=3,
            entry_price=3000.0,
            margin_required=166.67,
            margin_available=2000.0,
            buying_power_used_pct=8.3,
            liquidation_price=3300.0,
            liquidation_distance_pct=10.0,
        )

        result = PreviewBuilder.build_quick_preview(data)

        assert "ETH" in result
        assert "SELL" in result
        assert "🔴" in result  # Sell emoji

    def test_quick_preview_extreme_risk(self) -> None:
        """Test quick preview shows extreme risk warning."""
        data = PreviewData(
            coin="SOL",
            side="BUY",
            amount_usd=100.0,
            leverage=20,
            entry_price=100.0,
            margin_required=5.0,
            margin_available=1000.0,
            buying_power_used_pct=0.5,
            liquidation_price=99.0,
            liquidation_distance_pct=1.0,  # Very risky
        )

        result = PreviewBuilder.build_quick_preview(data)

        assert "EXTREME" in result or "CRITICAL" in result
        assert "💀" in result or "🔴" in result

    def test_quick_preview_safe_risk(self) -> None:
        """Test quick preview shows safe risk level."""
        data = PreviewData(
            coin="BTC",
            side="BUY",
            amount_usd=100.0,
            leverage=1,
            entry_price=50000.0,
            margin_required=100.0,
            margin_available=10000.0,
            buying_power_used_pct=1.0,
            liquidation_price=25000.0,
            liquidation_distance_pct=50.0,  # Very safe
        )

        result = PreviewBuilder.build_quick_preview(data)

        assert "SAFE" in result or "LOW" in result
        assert "🟢" in result


class TestPreviewBuilderFull:
    """Test PreviewBuilder.build_full_preview()."""

    def test_full_preview_structure(self) -> None:
        """Test full preview has all sections."""
        data = PreviewData(
            coin="BTC",
            side="BUY",
            amount_usd=1000.0,
            leverage=5,
            entry_price=50000.0,
            margin_required=200.0,
            margin_available=5000.0,
            buying_power_used_pct=4.0,
            liquidation_price=45000.0,
            liquidation_distance_pct=10.0,
        )

        result = PreviewBuilder.build_full_preview(data)

        # Check header
        assert "Complete Order Analysis" in result
        assert "BTC" in result
        assert "BUY" in result

        # Check cards
        assert "CAPITAL IMPACT" in result
        assert "RISK ASSESSMENT" in result

        # Check values
        assert "$1,000.00" in result
        assert "5x" in result

    def test_full_preview_with_position_size(self) -> None:
        """Test full preview includes position size when provided."""
        data = PreviewData(
            coin="ETH",
            side="BUY",
            amount_usd=500.0,
            leverage=3,
            entry_price=3000.0,
            margin_required=166.67,
            margin_available=2000.0,
            buying_power_used_pct=8.3,
            liquidation_price=2700.0,
            liquidation_distance_pct=10.0,
            size_coin=0.167,
        )

        result = PreviewBuilder.build_full_preview(data)

        assert "Position Size" in result
        assert "0.167" in result or "0.17" in result
        assert "ETH" in result

    def test_full_preview_with_warnings(self) -> None:
        """Test full preview displays warnings."""
        data = PreviewData(
            coin="SOL",
            side="BUY",
            amount_usd=100.0,
            leverage=10,
            entry_price=100.0,
            margin_required=10.0,
            margin_available=1000.0,
            buying_power_used_pct=1.0,
            liquidation_price=90.0,
            liquidation_distance_pct=10.0,
            warnings=["High volatility asset", "Leverage exceeds recommended maximum"],
        )

        result = PreviewBuilder.build_full_preview(data)

        assert "Warnings" in result
        assert "High volatility asset" in result
        assert "Leverage exceeds recommended maximum" in result

    def test_full_preview_no_warnings(self) -> None:
        """Test full preview without warnings section."""
        data = PreviewData(
            coin="BTC",
            side="BUY",
            amount_usd=1000.0,
            leverage=2,
            entry_price=50000.0,
            margin_required=500.0,
            margin_available=5000.0,
            buying_power_used_pct=10.0,
            liquidation_price=25000.0,
            liquidation_distance_pct=50.0,
            warnings=[],
        )

        result = PreviewBuilder.build_full_preview(data)

        assert "Warnings" not in result

    def test_full_preview_with_stop_loss(self) -> None:
        """Test full preview considers stop-loss in risk."""
        data = PreviewData(
            coin="BTC",
            side="BUY",
            amount_usd=1000.0,
            leverage=5,
            entry_price=50000.0,
            margin_required=200.0,
            margin_available=5000.0,
            buying_power_used_pct=4.0,
            liquidation_price=45000.0,
            liquidation_distance_pct=10.0,
            has_stop_loss=True,
        )

        result = PreviewBuilder.build_full_preview(data)

        # Should show risk assessment with stop-loss considered
        assert "RISK ASSESSMENT" in result


class TestBuildOrderPreview:
    """Test build_order_preview convenience function."""

    def test_build_quick_tier(self) -> None:
        """Test building quick tier preview."""
        data = PreviewData(
            coin="BTC",
            side="BUY",
            amount_usd=1000.0,
            leverage=5,
            entry_price=50000.0,
            margin_required=200.0,
            margin_available=5000.0,
            buying_power_used_pct=4.0,
            liquidation_price=45000.0,
            liquidation_distance_pct=10.0,
        )

        result = build_order_preview(data, tier="quick")

        assert "Order Preview" in result
        assert "Complete Order Analysis" not in result

    def test_build_full_tier(self) -> None:
        """Test building full tier preview."""
        data = PreviewData(
            coin="BTC",
            side="BUY",
            amount_usd=1000.0,
            leverage=5,
            entry_price=50000.0,
            margin_required=200.0,
            margin_available=5000.0,
            buying_power_used_pct=4.0,
            liquidation_price=45000.0,
            liquidation_distance_pct=10.0,
        )

        result = build_order_preview(data, tier="full")

        assert "Complete Order Analysis" in result

    def test_build_invalid_tier(self) -> None:
        """Test building with invalid tier raises error."""
        data = PreviewData(
            coin="BTC",
            side="BUY",
            amount_usd=1000.0,
            leverage=5,
            entry_price=50000.0,
            margin_required=200.0,
            margin_available=5000.0,
            buying_power_used_pct=4.0,
            liquidation_price=45000.0,
            liquidation_distance_pct=10.0,
        )

        with pytest.raises(ValueError, match="Invalid tier"):
            build_order_preview(data, tier="invalid")
