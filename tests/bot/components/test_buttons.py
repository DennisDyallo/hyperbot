"""Tests for button building utilities."""

from telegram import InlineKeyboardMarkup

from src.bot.components.buttons import (
    ButtonBuilder,
    build_action_button,
    build_confirm_cancel_buttons,
    build_navigation_row,
    build_single_action_button,
)


def _rows(markup: InlineKeyboardMarkup) -> list[list]:
    """Helper to extract rows from InlineKeyboardMarkup for assertions."""

    return markup.inline_keyboard


class TestButtonBuilder:
    """Test ButtonBuilder fluent interface."""

    def test_single_action_button(self) -> None:
        """Test building a single action button."""
        builder = ButtonBuilder()
        builder.action("Buy BTC", "buy_btc")
        buttons = _rows(builder.build())

        assert len(buttons) == 1
        assert len(buttons[0]) == 1
        assert buttons[0][0].text == "✅ Buy BTC"
        assert buttons[0][0].callback_data == "buy_btc"

    def test_multiple_actions_same_row(self) -> None:
        """Test multiple actions in the same row."""
        builder = ButtonBuilder()
        builder.action("Yes", "yes")
        builder.action("No", "no")
        buttons = _rows(builder.build())

        assert len(buttons) == 1
        assert len(buttons[0]) == 2
        assert buttons[0][0].text == "✅ Yes"
        assert buttons[0][1].text == "✅ No"

    def test_full_width_action(self) -> None:
        """Test full-width action button."""
        builder = ButtonBuilder()
        builder.action("Buy $1,000 BTC", "buy", full_width=True)
        buttons = _rows(builder.build())

        assert len(buttons) == 1
        assert len(buttons[0]) == 1

    def test_cancel_button(self) -> None:
        """Test cancel button is added."""
        builder = ButtonBuilder()
        builder.action("Confirm", "confirm")
        builder.cancel()
        buttons = _rows(builder.build())

        assert len(buttons) == 2
        assert buttons[1][0].text == "❌ Cancel"
        assert buttons[1][0].callback_data == "cancel"

    def test_back_button(self) -> None:
        """Test back navigation button."""
        builder = ButtonBuilder()
        builder.back()
        buttons = _rows(builder.build())

        assert len(buttons) == 1
        assert buttons[0][0].text == "🔙 Back"
        assert buttons[0][0].callback_data == "back"

    def test_back_with_cancel(self) -> None:
        """Test back button with cancel."""
        builder = ButtonBuilder()
        builder.back(with_cancel=True)
        buttons = _rows(builder.build())

        assert len(buttons) == 1
        assert len(buttons[0]) == 2
        assert buttons[0][0].text == "🔙 Back"
        assert buttons[0][1].text == "❌ Cancel"

    def test_row_break(self) -> None:
        """Test forcing a new row."""
        builder = ButtonBuilder()
        builder.action("One", "one")
        builder.row_break()
        builder.action("Two", "two")
        buttons = _rows(builder.build())

        assert len(buttons) == 2
        assert len(buttons[0]) == 1
        assert len(buttons[1]) == 1

    def test_max_buttons_per_row_auto_wrap(self) -> None:
        """Test automatic wrapping at max buttons per row."""
        builder = ButtonBuilder()
        builder.action("1", "1")
        builder.action("2", "2")
        builder.action("3", "3")
        builder.action("4", "4")
        builder.action("5", "5")  # Should wrap to new row
        buttons = _rows(builder.build())

        assert len(buttons) == 2
        assert len(buttons[0]) == 4  # Max per row
        assert len(buttons[1]) == 1

    def test_different_button_styles(self) -> None:
        """Test different button styles."""
        builder = ButtonBuilder()
        builder.action("Primary", "pri", style="primary")
        builder.action("Secondary", "sec", style="secondary")
        builder.action("Danger", "dan", style="danger")
        buttons = _rows(builder.build())

        assert "✅" in buttons[0][0].text
        assert "📊" in buttons[0][1].text
        assert "❌" in buttons[0][2].text

    def test_custom_labels(self) -> None:
        """Test custom labels for cancel and back."""
        builder = ButtonBuilder()
        builder.cancel(label="Abort", callback_data="abort")
        buttons = _rows(builder.build())

        assert buttons[0][0].text == "❌ Abort"
        assert buttons[0][0].callback_data == "abort"

    def test_emoji_not_duplicated(self) -> None:
        """Test emoji is not duplicated if already in label."""
        builder = ButtonBuilder()
        builder.action("✅ Already has emoji", "test", style="primary")
        buttons = _rows(builder.build())

        # Should not have double emoji
        assert buttons[0][0].text == "✅ Already has emoji"

    def test_method_chaining(self) -> None:
        """Test fluent interface allows method chaining."""
        buttons = (
            ButtonBuilder()
            .action("Confirm", "confirm")
            .action("Details", "details", style="secondary")
            .back(with_cancel=True)
            .build()
        )

        rows = _rows(buttons)

        assert len(rows) == 2  # One row of actions, one row of nav
        assert len(rows[0]) == 2  # Confirm + Details
        assert len(rows[1]) == 2  # Back + Cancel


class TestBuildSingleActionButton:
    """Test convenience function for single action button."""

    def test_build_action_button_helper(self) -> None:
        """Test standalone action button helper returns styled button."""
        button = build_action_button("Confirm", "confirm:123")

        assert button.text.startswith("✅ Confirm")
        assert button.callback_data == "confirm:123"

    def test_build_action_button_custom_style(self) -> None:
        """Test helper respects alternate styles."""
        button = build_action_button("Warn", "warn", style="warning")

        assert button.text.startswith("⚠️ Warn")
        assert button.callback_data == "warn"

    def test_creates_single_button(self) -> None:
        """Test creates a single full-width button."""
        buttons = _rows(build_single_action_button("Buy BTC", "buy_btc"))

        assert len(buttons) == 1
        assert len(buttons[0]) == 1
        assert buttons[0][0].text == "✅ Buy BTC"

    def test_respects_style(self) -> None:
        """Test style parameter is respected."""
        buttons = _rows(build_single_action_button("Cancel", "cancel", style="danger"))

        assert "❌" in buttons[0][0].text


class TestBuildConfirmCancelButtons:
    """Test confirm/cancel button pair."""

    def test_creates_two_buttons(self) -> None:
        """Test creates confirm and cancel buttons."""
        buttons = _rows(build_confirm_cancel_buttons("Confirm", "confirm"))

        assert len(buttons) == 1
        assert len(buttons[0]) == 2

    def test_custom_labels(self) -> None:
        """Test custom labels are used."""
        buttons = _rows(
            build_confirm_cancel_buttons(
                "Buy", "buy:BTC", cancel_label="Abort", cancel_callback="abort"
            )
        )

        assert "Buy" in buttons[0][0].text
        assert "Abort" in buttons[0][1].text
        assert buttons[0][0].callback_data == "buy:BTC"
        assert buttons[0][1].callback_data == "abort"


class TestBuildNavigationRow:
    """Test navigation row builder."""

    def test_creates_back_and_cancel(self) -> None:
        """Test creates back and cancel buttons."""
        buttons = build_navigation_row()

        assert len(buttons) == 1
        assert len(buttons[0]) == 2
        assert "🔙 Back" in buttons[0][0].text
        assert "❌ Cancel" in buttons[0][1].text

    def test_custom_callbacks(self) -> None:
        """Test custom callback data."""
        buttons = build_navigation_row(back_callback="prev", cancel_callback="exit")

        assert buttons[0][0].callback_data == "prev"
        assert buttons[0][1].callback_data == "exit"
