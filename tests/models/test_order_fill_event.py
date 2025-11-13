"""
Unit tests for OrderFillEvent model.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from src.models.order_fill_event import OrderFillEvent


class TestOrderFillEvent:
    """Test OrderFillEvent model."""

    @pytest.fixture
    def sample_fill_data(self):
        """Sample fill data matching Hyperliquid API structure."""
        return {
            "coin": "BTC",
            "px": "50000.0",
            "sz": "0.1",
            "side": "B",
            "time": 1762993854147,
            "startPosition": "0.0",
            "dir": "Open Long",
            "closedPnl": "0.0",
            "hash": "0xabc123",
            "oid": 12345,
            "crossed": True,
            "fee": "2.5",
            "tid": 67890,
            "feeToken": "USDC",
            "twapId": None,
        }

    def test_create_from_api_data(self, sample_fill_data):
        """Test creating OrderFillEvent from API data."""
        fill = OrderFillEvent(**sample_fill_data)

        assert fill.coin == "BTC"
        assert fill.price == Decimal("50000.0")
        assert fill.size == Decimal("0.1")
        assert fill.side == "B"
        assert fill.timestamp_ms == 1762993854147
        assert fill.direction == "Open Long"
        assert fill.order_id == 12345
        assert fill.trade_id == 67890

    def test_decimal_field_parsing(self, sample_fill_data):
        """Test that decimal fields are parsed correctly."""
        fill = OrderFillEvent(**sample_fill_data)

        assert isinstance(fill.price, Decimal)
        assert isinstance(fill.size, Decimal)
        assert isinstance(fill.start_position, Decimal)
        assert isinstance(fill.closed_pnl, Decimal)
        assert isinstance(fill.fee, Decimal)

    def test_timestamp_property(self, sample_fill_data):
        """Test timestamp conversion to datetime."""
        fill = OrderFillEvent(**sample_fill_data)

        timestamp = fill.timestamp

        assert isinstance(timestamp, datetime)
        assert timestamp.tzinfo == UTC
        # 1762993854147 ms = 1762993854.147 s
        expected = datetime.fromtimestamp(1762993854.147, tz=UTC)
        assert timestamp == expected

    def test_side_text_buy(self, sample_fill_data):
        """Test side_text property for buy order."""
        fill = OrderFillEvent(**sample_fill_data)

        assert fill.side_text == "BUY"

    def test_side_text_sell(self, sample_fill_data):
        """Test side_text property for sell order."""
        sample_fill_data["side"] = "S"
        fill = OrderFillEvent(**sample_fill_data)

        assert fill.side_text == "SELL"

    def test_side_emoji_buy(self, sample_fill_data):
        """Test side_emoji for buy order."""
        fill = OrderFillEvent(**sample_fill_data)

        assert fill.side_emoji == "📈"

    def test_side_emoji_sell(self, sample_fill_data):
        """Test side_emoji for sell order."""
        sample_fill_data["side"] = "S"
        fill = OrderFillEvent(**sample_fill_data)

        assert fill.side_emoji == "📉"

    def test_direction_emoji_open_long(self, sample_fill_data):
        """Test direction_emoji for Open Long."""
        sample_fill_data["dir"] = "Open Long"
        fill = OrderFillEvent(**sample_fill_data)

        assert fill.direction_emoji == "🟢"

    def test_direction_emoji_close_long(self, sample_fill_data):
        """Test direction_emoji for Close Long."""
        sample_fill_data["dir"] = "Close Long"
        fill = OrderFillEvent(**sample_fill_data)

        assert fill.direction_emoji == "🔵"

    def test_direction_emoji_open_short(self, sample_fill_data):
        """Test direction_emoji for Open Short."""
        sample_fill_data["dir"] = "Open Short"
        fill = OrderFillEvent(**sample_fill_data)

        assert fill.direction_emoji == "🔴"

    def test_direction_emoji_close_short(self, sample_fill_data):
        """Test direction_emoji for Close Short."""
        sample_fill_data["dir"] = "Close Short"
        fill = OrderFillEvent(**sample_fill_data)

        assert fill.direction_emoji == "🟣"

    def test_total_value(self, sample_fill_data):
        """Test total_value calculation."""
        fill = OrderFillEvent(**sample_fill_data)

        # 0.1 * 50000.0 = 5000.0
        assert fill.total_value == Decimal("5000.0")

    def test_is_opening(self, sample_fill_data):
        """Test is_opening property."""
        sample_fill_data["dir"] = "Open Long"
        fill = OrderFillEvent(**sample_fill_data)
        assert fill.is_opening is True

        sample_fill_data["dir"] = "Close Long"
        fill = OrderFillEvent(**sample_fill_data)
        assert fill.is_opening is False

    def test_is_closing(self, sample_fill_data):
        """Test is_closing property."""
        sample_fill_data["dir"] = "Close Long"
        fill = OrderFillEvent(**sample_fill_data)
        assert fill.is_closing is True

        sample_fill_data["dir"] = "Open Long"
        fill = OrderFillEvent(**sample_fill_data)
        assert fill.is_closing is False

    def test_is_long(self, sample_fill_data):
        """Test is_long property."""
        sample_fill_data["dir"] = "Open Long"
        fill = OrderFillEvent(**sample_fill_data)
        assert fill.is_long is True

        sample_fill_data["dir"] = "Open Short"
        fill = OrderFillEvent(**sample_fill_data)
        assert fill.is_long is False

    def test_is_short(self, sample_fill_data):
        """Test is_short property."""
        sample_fill_data["dir"] = "Open Short"
        fill = OrderFillEvent(**sample_fill_data)
        assert fill.is_short is True

        sample_fill_data["dir"] = "Open Long"
        fill = OrderFillEvent(**sample_fill_data)
        assert fill.is_short is False

    def test_calculate_hash_consistent(self, sample_fill_data):
        """Test that calculate_hash returns consistent results."""
        fill1 = OrderFillEvent(**sample_fill_data)
        fill2 = OrderFillEvent(**sample_fill_data)

        hash1 = fill1.calculate_hash()
        hash2 = fill2.calculate_hash()

        assert hash1 == hash2
        assert len(hash1) == 16  # 16 character hex hash

    def test_calculate_hash_unique_for_different_fills(self, sample_fill_data):
        """Test that different fills produce different hashes."""
        fill1 = OrderFillEvent(**sample_fill_data)

        # Modify trade_id
        sample_fill_data["tid"] = 99999
        fill2 = OrderFillEvent(**sample_fill_data)

        assert fill1.calculate_hash() != fill2.calculate_hash()

    def test_to_notification_text_with_emoji(self, sample_fill_data):
        """Test notification text formatting with emojis."""
        fill = OrderFillEvent(**sample_fill_data)

        text = fill.to_notification_text(include_emoji=True)

        # Check for key elements
        assert "🎯" in text  # Order filled emoji
        assert "**Market Order Filled!**" in text  # crossed=True
        assert "BTC" in text
        assert "BUY 📈" in text
        assert "Open Long 🟢" in text
        assert "0.1" in text
        assert "50,000.0000" in text
        assert "$5,000.00" in text  # Total value
        assert "2.5" in text  # Fee

    def test_to_notification_text_without_emoji(self, sample_fill_data):
        """Test notification text formatting without emojis."""
        fill = OrderFillEvent(**sample_fill_data)

        text = fill.to_notification_text(include_emoji=False)

        # Should not have emojis
        assert "🎯" not in text
        assert "📈" not in text
        assert "🟢" not in text

        # But should still have text
        assert "**Market Order Filled!**" in text
        assert "BTC" in text
        assert "BUY" in text
        assert "Open Long" in text

    def test_to_notification_text_limit_order(self, sample_fill_data):
        """Test notification text for limit order (not crossed)."""
        sample_fill_data["crossed"] = False
        fill = OrderFillEvent(**sample_fill_data)

        text = fill.to_notification_text(include_emoji=True)

        assert "**Limit Order Filled!**" in text

    def test_to_notification_text_with_pnl(self, sample_fill_data):
        """Test notification text includes P&L for closing trades."""
        sample_fill_data["dir"] = "Close Long"
        sample_fill_data["closedPnl"] = "150.50"
        fill = OrderFillEvent(**sample_fill_data)

        text = fill.to_notification_text(include_emoji=True)

        assert "Closed P&L" in text
        assert "150.50" in text
        assert "💰" in text  # Profit emoji

    def test_to_notification_text_with_negative_pnl(self, sample_fill_data):
        """Test notification text includes P&L for losing trades."""
        sample_fill_data["dir"] = "Close Long"
        sample_fill_data["closedPnl"] = "-50.25"
        fill = OrderFillEvent(**sample_fill_data)

        text = fill.to_notification_text(include_emoji=True)

        assert "Closed P&L" in text
        assert "-50.25" in text
        assert "📉" in text  # Loss emoji

    def test_to_notification_text_liquidation(self, sample_fill_data):
        """Test notification text for liquidation fill."""
        sample_fill_data["liquidation"] = True
        fill = OrderFillEvent(**sample_fill_data)

        text = fill.to_notification_text(include_emoji=True)

        assert "⚠️ **LIQUIDATION FILL**" in text

    def test_optional_fields(self, sample_fill_data):
        """Test that optional fields can be None."""
        sample_fill_data["twapId"] = None
        sample_fill_data["builderFee"] = None

        fill = OrderFillEvent(**sample_fill_data)

        assert fill.twap_id is None
        assert fill.builder_fee is None
        assert fill.liquidation is False  # Default

    def test_with_twap_id(self, sample_fill_data):
        """Test fill with TWAP order ID."""
        sample_fill_data["twapId"] = 54321
        fill = OrderFillEvent(**sample_fill_data)

        assert fill.twap_id == 54321

    def test_with_builder_fee(self, sample_fill_data):
        """Test fill with MEV builder fee."""
        sample_fill_data["builderFee"] = "0.001"
        fill = OrderFillEvent(**sample_fill_data)

        assert fill.builder_fee == Decimal("0.001")

    def test_alias_support(self):
        """Test that Pydantic aliases work (API field names)."""
        # Using aliases (as returned by Hyperliquid API)
        # Note: Pydantic field_validator converts strings to Decimal
        # mypy doesn't understand this, so we suppress type errors
        fill1 = OrderFillEvent(
            coin="BTC",
            px="50000",  # type: ignore[arg-type]  # Pydantic converts str to Decimal
            sz="0.1",  # type: ignore[arg-type]
            side="B",
            time=1000,
            startPosition="0",  # type: ignore[arg-type]
            dir="Open Long",
            closedPnl="0",  # type: ignore[arg-type]
            hash="0x123",
            oid=1,
            crossed=True,
            fee="1",  # type: ignore[arg-type]
            tid=2,
            feeToken="USDC",
            twapId=None,
            builderFee=None,
            liquidation=False,
        )

        # Create another fill with same data
        fill2 = OrderFillEvent(
            coin="BTC",
            px="50000",  # type: ignore[arg-type]
            sz="0.1",  # type: ignore[arg-type]
            side="B",
            time=1000,
            startPosition="0",  # type: ignore[arg-type]
            dir="Open Long",
            closedPnl="0",  # type: ignore[arg-type]
            hash="0x123",
            oid=1,
            crossed=True,
            fee="1",  # type: ignore[arg-type]
            tid=2,
            feeToken="USDC",
            twapId=None,
            builderFee=None,
            liquidation=False,
        )

        # Both should produce same hash
        assert fill1.calculate_hash() == fill2.calculate_hash()

        # Verify internal fields are accessible
        assert fill1.price == Decimal("50000")
        assert fill1.size == Decimal("0.1")
        assert fill1.timestamp_ms == 1000
        assert fill1.order_id == 1
        assert fill1.trade_id == 2
