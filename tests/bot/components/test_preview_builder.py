"""
Tests for preview message builders.

Tests pure functions that build formatted preview messages for order confirmations.
"""

import pytest

from src.bot.components.preview_builder import (
    build_leverage_selection_message,
    build_order_preview,
    build_quick_order_preview,
)


class TestBuildOrderPreview:
    """Tests for build_order_preview function."""

    def test_basic_market_order_preview(self):
        """Test basic market order preview without leverage."""
        preview = build_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            coin_size=0.01015,
            price=98500.0,
        )

        assert "BTC" in preview
        assert "BUY" in preview
        assert "$1,000.00" in preview
        assert "0.01015" in preview
        assert "98,500.00" in preview
        assert "Market order will execute at best available price" in preview
        assert "🟢" in preview  # Buy emoji

    def test_sell_order_preview(self):
        """Test sell order uses correct emoji."""
        preview = build_order_preview(
            coin="ETH",
            side="SELL",
            usd_amount=500.0,
            coin_size=0.25,
            price=2000.0,
        )

        assert "SELL" in preview
        assert "🔴" in preview  # Sell emoji

    def test_leveraged_order_preview(self):
        """Test order preview with leverage information."""
        preview = build_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            coin_size=0.01015,
            price=98500.0,
            leverage=5,
            margin_required=200.0,
            liquidation_price=78800.0,
            risk_level="MODERATE",
        )

        assert "5x" in preview
        assert "$200.00" in preview  # Margin required
        assert "78,800.00" in preview  # Liquidation price
        assert "MODERATE" in preview
        assert "🟡" in preview  # Moderate risk emoji

    def test_limit_order_preview(self):
        """Test limit order shows price difference."""
        preview = build_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            coin_size=0.01036,
            price=98500.0,  # Current price
            order_type="Limit",
            limit_price=96530.0,  # 2% below
        )

        assert "Limit" in preview
        assert "96,530.00" in preview  # Limit price
        assert "98,500.00" in preview  # Current price
        assert "-2.00%" in preview  # Percentage difference
        assert "Limit order will only fill" in preview

    def test_risk_levels(self):
        """Test all risk levels show correct emojis."""
        risk_levels = {
            "LOW": "🟢",
            "MODERATE": "🟡",
            "HIGH": "🟠",
            "EXTREME": "🔴",
        }

        for level, emoji in risk_levels.items():
            preview = build_order_preview(
                coin="BTC",
                side="BUY",
                usd_amount=1000.0,
                coin_size=0.01,
                price=100000.0,
                leverage=5,
                risk_level=level,
            )

            assert level in preview
            assert emoji in preview

    def test_testnet_environment_indicator(self, monkeypatch):
        """Test environment indicator shows testnet."""
        from src.config import settings

        monkeypatch.setattr(settings, "HYPERLIQUID_TESTNET", True)

        preview = build_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            coin_size=0.01,
            price=100000.0,
        )

        assert "🧪 Testnet" in preview

    def test_mainnet_environment_indicator(self, monkeypatch):
        """Test environment indicator shows mainnet."""
        from src.config import settings

        monkeypatch.setattr(settings, "HYPERLIQUID_TESTNET", False)

        preview = build_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            coin_size=0.01,
            price=100000.0,
        )

        assert "🚀 Mainnet" in preview


class TestBuildQuickOrderPreview:
    """Tests for build_quick_order_preview function (mobile-optimized)."""

    def test_quick_preview_is_compact(self):
        """Test quick preview is more compact than full preview."""
        quick = build_quick_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            price=98500.0,
        )

        full = build_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            coin_size=0.01,
            price=98500.0,
        )

        # Quick preview should be significantly shorter
        assert len(quick) < len(full) * 0.6

    def test_quick_preview_with_leverage(self):
        """Test quick preview includes leverage info."""
        preview = build_quick_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            price=98500.0,
            leverage=5,
            margin_required=200.0,
            margin_available=5200.0,
            liquidation_price=78800.0,
            risk_level="MODERATE",
        )

        assert "5x" in preview
        assert "$200.00" in preview
        assert "$5,200.00" in preview
        assert "78,800" in preview  # Compact format
        assert "MODERATE" in preview
        assert "📋 Order Preview" in preview

    def test_quick_preview_market_vs_limit(self):
        """Test quick preview shows @ market or @ price."""
        market_preview = build_quick_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            price=98500.0,
            order_type="Market",
        )

        limit_preview = build_quick_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            price=98500.0,
            order_type="Limit",
            limit_price=96530.0,
        )

        assert "@ market" in market_preview
        assert "@ $96,530" in limit_preview


class TestBuildLeverageSelectionMessage:
    """Tests for build_leverage_selection_message function."""

    def test_default_leverage_levels(self):
        """Test default leverage levels are displayed."""
        message = build_leverage_selection_message(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            available_margin=5200.0,
        )

        # Check all default levels present
        for lev in [1, 3, 5, 10, 20]:
            assert f"{lev}x" in message

        # Check buying power calculations
        assert "$5,200.00" in message  # 1x
        assert "$15,600.00" in message  # 3x
        assert "$26,000.00" in message  # 5x
        assert "$52,000.00" in message  # 10x
        assert "$104,000.00" in message  # 20x

    def test_custom_leverage_levels(self):
        """Test custom leverage levels."""
        message = build_leverage_selection_message(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            available_margin=5000.0,
            leverage_levels=[1, 2, 5],
        )

        assert "1x" in message
        assert "2x" in message
        assert "5x" in message
        assert "10x" not in message

    def test_recommended_leverage_highlighted(self):
        """Test recommended leverage gets sparkle emoji."""
        message = build_leverage_selection_message(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            available_margin=5000.0,
            recommended_leverage=3,
        )

        # Check that 3x has the sparkle emoji
        lines = message.split("\n")
        for line in lines:
            if line.startswith("3x"):
                assert "✨" in line
                break
        else:
            pytest.fail("3x leverage line not found")

    def test_risk_labels_correct(self):
        """Test risk labels match leverage levels."""
        message = build_leverage_selection_message(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            available_margin=5000.0,
        )

        assert "Conservative" in message  # 1x
        assert "Balanced" in message  # 3x
        assert "Moderate risk" in message  # 5x
        assert "Risky" in message  # 10x
        assert "Extreme risk" in message  # 20x

    def test_contextual_tip_with_recommendation(self):
        """Test tip shows when leverage is recommended."""
        message = build_leverage_selection_message(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            available_margin=5000.0,
            recommended_leverage=5,
        )

        assert "💡" in message
        assert "5x balances opportunity and safety" in message

    def test_no_tip_without_recommendation(self):
        """Test no tip shown when no recommendation provided."""
        message = build_leverage_selection_message(
            coin="BTC",
            side="BUY",
            usd_amount=1000.0,
            available_margin=5000.0,
            recommended_leverage=None,
        )

        assert "💡" not in message
        assert "balances opportunity" not in message


class TestPreviewBuilderIntegration:
    """Integration tests for preview builders."""

    def test_preview_builders_consistent_formatting(self):
        """Test all builders use consistent formatting for amounts."""
        # All should use format_usd_amount and format_coin_amount
        full_preview = build_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1234.56,
            coin_size=0.0123456,
            price=100000.0,
        )

        quick_preview = build_quick_order_preview(
            coin="BTC",
            side="BUY",
            usd_amount=1234.56,
            price=100000.0,
        )

        leverage_msg = build_leverage_selection_message(
            coin="BTC",
            side="BUY",
            usd_amount=1234.56,
            available_margin=5000.0,
        )

        # All should format USD consistently
        for preview in [full_preview, quick_preview, leverage_msg]:
            assert "$1,234.56" in preview

    def test_all_builders_return_strings(self):
        """Test all builders return string types."""
        builders = [
            build_order_preview(
                coin="BTC", side="BUY", usd_amount=1000.0, coin_size=0.01, price=100000.0
            ),
            build_quick_order_preview(coin="BTC", side="BUY", usd_amount=1000.0, price=100000.0),
            build_leverage_selection_message(
                coin="BTC", side="BUY", usd_amount=1000.0, available_margin=5000.0
            ),
        ]

        for result in builders:
            assert isinstance(result, str)
            assert len(result) > 0
