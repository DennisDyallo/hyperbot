"""
Button building utilities for consistent Telegram inline keyboard layouts.

Provides a fluent API for building button layouts with proper styling,
ordering, and accessibility.
"""

from typing import Final

from telegram import InlineKeyboardButton

# Button layout constants
MAX_BUTTONS_PER_ROW: Final[int] = 4
BUTTON_STYLES: Final[dict[str, str]] = {
    "primary": "✅",  # Confirm, submit, buy/sell
    "secondary": "📊",  # View details, info
    "danger": "❌",  # Cancel, close, delete
    "back": "🔙",  # Navigation back
    "info": "ℹ️",  # Help, info
    "settings": "⚙️",  # Change settings
}


class ButtonBuilder:
    """
    Fluent interface for building Telegram inline keyboard button layouts.

    Ensures consistent button styling, ordering, and layout patterns across
    all bot interactions.

    Example:
        >>> builder = ButtonBuilder()
        >>> builder.action("Buy $1,000 BTC", "confirm_buy", style="primary")
        >>> builder.action("Full Details", "show_details", style="secondary")
        >>> builder.cancel()
        >>> buttons = builder.build()
    """

    def __init__(self) -> None:
        """Initialize an empty button builder."""
        self._rows: list[list[InlineKeyboardButton]] = []
        self._current_row: list[InlineKeyboardButton] = []

    def action(
        self,
        label: str,
        callback_data: str,
        style: str = "primary",
        full_width: bool = False,
    ) -> "ButtonBuilder":
        """
        Add an action button.

        Args:
            label: The button text (emoji will be prepended based on style).
            callback_data: The callback data for the button.
            style: Button style from BUTTON_STYLES (default: "primary").
            full_width: If True, button takes full row width.

        Returns:
            Self for method chaining.
        """
        # Get emoji for style (if not already in label)
        emoji = BUTTON_STYLES.get(style, "")
        button_text = f"{emoji} {label}" if emoji and not label.startswith(emoji) else label

        button = InlineKeyboardButton(text=button_text, callback_data=callback_data)

        if full_width:
            # Flush current row and add button as new row
            self._flush_row()
            self._rows.append([button])
        else:
            self._current_row.append(button)
            # Auto-flush if we hit max buttons per row
            if len(self._current_row) >= MAX_BUTTONS_PER_ROW:
                self._flush_row()

        return self

    def cancel(self, label: str = "Cancel", callback_data: str = "cancel") -> "ButtonBuilder":
        """
        Add a cancel button (always full width, bottom of layout).

        Args:
            label: Button text (default: "Cancel").
            callback_data: Callback data (default: "cancel").

        Returns:
            Self for method chaining.
        """
        self._flush_row()
        button = InlineKeyboardButton(
            text=f"{BUTTON_STYLES['danger']} {label}",
            callback_data=callback_data,
        )
        self._rows.append([button])
        return self

    def back(
        self,
        label: str = "Back",
        callback_data: str = "back",
        with_cancel: bool = False,
    ) -> "ButtonBuilder":
        """
        Add a back navigation button.

        Args:
            label: Button text (default: "Back").
            callback_data: Callback data (default: "back").
            with_cancel: If True, add cancel button next to back.

        Returns:
            Self for method chaining.
        """
        self._flush_row()
        back_button = InlineKeyboardButton(
            text=f"{BUTTON_STYLES['back']} {label}",
            callback_data=callback_data,
        )

        if with_cancel:
            cancel_button = InlineKeyboardButton(
                text=f"{BUTTON_STYLES['danger']} Cancel",
                callback_data="cancel",
            )
            self._rows.append([back_button, cancel_button])
        else:
            self._rows.append([back_button])

        return self

    def row_break(self) -> "ButtonBuilder":
        """
        Force a new row for subsequent buttons.

        Returns:
            Self for method chaining.
        """
        self._flush_row()
        return self

    def build(self) -> list[list[InlineKeyboardButton]]:
        """
        Build the final button layout.

        Returns:
            List of button rows for InlineKeyboardMarkup.
        """
        # Flush any remaining buttons
        self._flush_row()
        return self._rows

    def _flush_row(self) -> None:
        """Flush current row to rows list if not empty."""
        if self._current_row:
            self._rows.append(self._current_row)
            self._current_row = []


def build_single_action_button(
    label: str,
    callback_data: str,
    style: str = "primary",
) -> list[list[InlineKeyboardButton]]:
    """
    Build a single full-width action button.

    Convenience function for simple single-button layouts.

    Args:
        label: Button text.
        callback_data: Callback data.
        style: Button style (default: "primary").

    Returns:
        Button layout for InlineKeyboardMarkup.

    Example:
        >>> buttons = build_single_action_button("Buy $1,000 BTC", "confirm")
        >>> # Returns: [[InlineKeyboardButton("✅ Buy $1,000 BTC", ...)]]
    """
    return ButtonBuilder().action(label, callback_data, style, full_width=True).build()


def build_confirm_cancel_buttons(
    confirm_label: str,
    confirm_callback: str,
    cancel_label: str = "Cancel",
    cancel_callback: str = "cancel",
) -> list[list[InlineKeyboardButton]]:
    """
    Build standard confirm/cancel button pair.

    Args:
        confirm_label: Confirm button text.
        confirm_callback: Confirm callback data.
        cancel_label: Cancel button text (default: "Cancel").
        cancel_callback: Cancel callback data (default: "cancel").

    Returns:
        Button layout with two buttons side by side.

    Example:
        >>> buttons = build_confirm_cancel_buttons("Buy", "buy:BTC")
        >>> # Returns confirm and cancel buttons in one row
    """
    builder = ButtonBuilder()
    builder.action(confirm_label, confirm_callback, style="primary")
    builder.action(cancel_label, cancel_callback, style="danger")
    return builder.build()


def build_navigation_row(
    back_callback: str = "back",
    cancel_callback: str = "cancel",
) -> list[list[InlineKeyboardButton]]:
    """
    Build standard back/cancel navigation row.

    Args:
        back_callback: Back button callback (default: "back").
        cancel_callback: Cancel button callback (default: "cancel").

    Returns:
        Button layout with back and cancel buttons.

    Example:
        >>> buttons = build_navigation_row()
        >>> # Returns [🔙 Back] [❌ Cancel] in one row
    """
    back_button = InlineKeyboardButton(
        text=f"{BUTTON_STYLES['back']} Back",
        callback_data=back_callback,
    )
    cancel_button = InlineKeyboardButton(
        text=f"{BUTTON_STYLES['danger']} Cancel",
        callback_data=cancel_callback,
    )
    return [[back_button, cancel_button]]
