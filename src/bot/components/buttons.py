"""
Button building utilities for consistent Telegram inline keyboard layouts.

Provides a fluent API for building button layouts with proper styling,
ordering, and accessibility.
"""

from typing import Final

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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

    def build(self) -> InlineKeyboardMarkup:
        """Build the final button layout.

        Returns:
            InlineKeyboardMarkup ready for Telegram API
        """
        # Flush any remaining buttons
        self._flush_row()
        return InlineKeyboardMarkup(self._rows)

    def _flush_row(self) -> None:
        """Flush current row to rows list if not empty."""
        if self._current_row:
            self._rows.append(self._current_row)
            self._current_row = []

    # Pattern methods for common wizard flows

    def coin_selection(
        self,
        coins: list[str] | None = None,
        callback_prefix: str = "select_coin",
        per_row: int = 3,
        add_custom: bool = True,
    ) -> "ButtonBuilder":
        """
        Add coin selection buttons in rows.

        Args:
            coins: List of coin symbols (default: common coins).
            callback_prefix: Prefix for callback data (default: "select_coin").
            per_row: Number of coins per row (default: 3).
            add_custom: If True, add custom input option (default: True).

        Returns:
            Self for method chaining.
        """
        if coins is None:
            coins = ["BTC", "ETH", "SOL", "ARB", "AVAX", "MATIC"]

        self._flush_row()

        # Create rows of coins
        for i in range(0, len(coins), per_row):
            row_coins = coins[i : i + per_row]
            for coin in row_coins:
                button = InlineKeyboardButton(
                    text=coin,
                    callback_data=f"{callback_prefix}:{coin}",
                )
                self._current_row.append(button)
            self._flush_row()

        # Add custom input option if requested
        if add_custom:
            self._flush_row()
            custom_button = InlineKeyboardButton(
                text="✏️ Enter Custom",
                callback_data="custom_coin",
            )
            self._rows.append([custom_button])

        return self

    def buy_sell(
        self,
        coin: str,
        callback_prefix: str = "side",
    ) -> "ButtonBuilder":
        """
        Add buy/sell toggle buttons for a coin.

        Args:
            coin: Coin symbol.
            callback_prefix: Prefix for callback data (default: "side").

        Returns:
            Self for method chaining.
        """
        self._flush_row()

        buy_button = InlineKeyboardButton(
            text=f"🟢 Buy {coin}",
            callback_data=f"{callback_prefix}_buy:{coin}",
        )
        sell_button = InlineKeyboardButton(
            text=f"🔴 Sell {coin}",
            callback_data=f"{callback_prefix}_sell:{coin}",
        )

        self._rows.append([buy_button, sell_button])

        return self

    def amount_presets(
        self,
        amounts: list[int] | None = None,
        callback_prefix: str = "amount",
        per_row: int = 3,
        add_custom: bool = True,
    ) -> "ButtonBuilder":
        """
        Add preset amount buttons in rows.

        Args:
            amounts: List of USD amounts (default: [10, 25, 50, 100, 250, 500]).
            callback_prefix: Prefix for callback data (default: "amount").
            per_row: Number of amounts per row (default: 3).
            add_custom: If True, add custom input option (default: True).

        Returns:
            Self for method chaining.
        """
        if amounts is None:
            amounts = [10, 25, 50, 100, 250, 500]

        self._flush_row()

        # Create rows of amount buttons
        for i in range(0, len(amounts), per_row):
            row_amounts = amounts[i : i + per_row]
            for amount in row_amounts:
                button = InlineKeyboardButton(
                    text=f"${amount}",
                    callback_data=f"{callback_prefix}:{amount}",
                )
                self._current_row.append(button)
            self._flush_row()

        # Add custom input option if requested
        if add_custom:
            self._flush_row()
            custom_button = InlineKeyboardButton(
                text="✏️ Enter Custom",
                callback_data="custom_amount",
            )
            self._rows.append([custom_button])

        return self

    def leverage_levels(
        self,
        levels: list[int] | None = None,
        callback_prefix: str = "leverage",
        per_row: int = 4,
        highlight_level: int | None = None,
    ) -> "ButtonBuilder":
        """
        Add leverage level selection buttons.

        Args:
            levels: List of leverage levels (default: [1, 3, 5, 10, 20]).
            callback_prefix: Prefix for callback data (default: "leverage").
            per_row: Number of levels per row (default: 4).
            highlight_level: Level to highlight with ✨ (default: None).

        Returns:
            Self for method chaining.
        """
        if levels is None:
            levels = [1, 3, 5, 10, 20]

        self._flush_row()

        # Create rows of leverage buttons
        for i in range(0, len(levels), per_row):
            row_levels = levels[i : i + per_row]
            for level in row_levels:
                # Add highlight emoji if this is the recommended level
                text = f"{level}x"
                if highlight_level and level == highlight_level:
                    text = f"✨ {level}x"

                button = InlineKeyboardButton(
                    text=text,
                    callback_data=f"{callback_prefix}:{level}",
                )
                self._current_row.append(button)
            self._flush_row()

        return self

    def confirm_cancel(
        self,
        confirm_label: str,
        confirm_callback: str,
        cancel_label: str = "Cancel",
        cancel_callback: str = "cancel",
    ) -> "ButtonBuilder":
        """
        Add confirm and cancel buttons in a row.

        Args:
            confirm_label: Confirm button text.
            confirm_callback: Confirm callback data.
            cancel_label: Cancel button text (default: "Cancel").
            cancel_callback: Cancel callback data (default: "cancel").

        Returns:
            Self for method chaining.
        """
        self._flush_row()

        confirm_button = InlineKeyboardButton(
            text=f"{BUTTON_STYLES['primary']} {confirm_label}",
            callback_data=confirm_callback,
        )
        cancel_button = InlineKeyboardButton(
            text=f"{BUTTON_STYLES['danger']} {cancel_label}",
            callback_data=cancel_callback,
        )

        self._rows.append([confirm_button, cancel_button])

        return self


def build_single_action_button(
    label: str,
    callback_data: str,
    style: str = "primary",
) -> InlineKeyboardMarkup:
    """Build a single full-width action button.

    Convenience function for simple single-button layouts.

    Args:
        label: Button text.
        callback_data: Callback data.
        style: Button style (default: "primary").

    Returns:
        InlineKeyboardMarkup ready for Telegram API

    Example:
        >>> buttons = build_single_action_button("Buy $1,000 BTC", "confirm")
    """
    return ButtonBuilder().action(label, callback_data, style, full_width=True).build()


def build_confirm_cancel_buttons(
    confirm_label: str,
    confirm_callback: str,
    cancel_label: str = "Cancel",
    cancel_callback: str = "cancel",
) -> InlineKeyboardMarkup:
    """Build standard confirm/cancel button pair.

    Args:
        confirm_label: Confirm button text.
        confirm_callback: Confirm callback data.
        cancel_label: Cancel button text (default: "Cancel").
        cancel_callback: Cancel callback data (default: "cancel").

    Returns:
        InlineKeyboardMarkup with confirm and cancel buttons

    Example:
        >>> buttons = build_confirm_cancel_buttons("Buy", "buy:BTC")
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
