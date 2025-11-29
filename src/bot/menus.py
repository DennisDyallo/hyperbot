"""
Interactive menu builders for Telegram bot.

Provides reusable menu components and navigation.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_main_menu() -> InlineKeyboardMarkup:
    """
    Build the main menu with all bot features.

    Returns inline keyboard with organized buttons.
    """
    keyboard = [
        # Information row
        [
            InlineKeyboardButton("📊 Account", callback_data="menu_account"),
            InlineKeyboardButton("📈 Positions", callback_data="menu_positions"),
        ],
        # Orders row
        [
            InlineKeyboardButton("📋 Orders", callback_data="menu_orders"),
        ],
        # Trading row
        [
            InlineKeyboardButton("💰 Market Order", callback_data="menu_market"),
            InlineKeyboardButton("🎯 Close Position", callback_data="menu_close"),
        ],
        # Advanced row
        [
            InlineKeyboardButton("⚖️ Rebalance", callback_data="menu_rebalance"),
            InlineKeyboardButton("📊 Scale Order", callback_data="menu_scale"),
        ],
        # Utility row
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="menu_help"),
            InlineKeyboardButton("⚙️ Status", callback_data="menu_status"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_back_button() -> InlineKeyboardMarkup:
    """Build a simple back to main menu button."""
    keyboard = [[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]]
    return InlineKeyboardMarkup(keyboard)


def build_with_back(buttons: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    """
    Add a back button to existing button layout.

    Args:
        buttons: List of button rows

    Returns:
        InlineKeyboardMarkup with back button added
    """
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


def build_positions_menu(positions: list[dict]) -> InlineKeyboardMarkup:
    """
    Build menu showing all positions for selection.

    Args:
        positions: List of position dictionaries

    Returns:
        InlineKeyboardMarkup with position buttons
    """
    keyboard = []

    for pos_data in positions[:10]:  # Limit to 10 positions
        p = pos_data["position"]
        coin = p["coin"]
        size = p["size"]
        pnl = p["unrealized_pnl"]

        # Format display
        side_emoji = "🟢" if size > 0 else "🔴"
        pnl_emoji = "📈" if pnl >= 0 else "📉"

        label = f"{side_emoji} {coin} {pnl_emoji} ${pnl:.2f}"
        callback = f"select_position:{coin}"

        keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

    if not keyboard:
        keyboard.append([InlineKeyboardButton("❌ No Positions", callback_data="noop")])

    # Add back button
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])

    return InlineKeyboardMarkup(keyboard)


def build_coin_selection_menu(top_coins: list[str] = None) -> InlineKeyboardMarkup:  # type: ignore
    """
    Build menu for selecting a coin.

    Args:
        top_coins: Optional list of coin symbols to show. Defaults to common ones.

    Returns:
        InlineKeyboardMarkup with coin buttons
    """
    if top_coins is None:
        top_coins = ["BTC", "ETH", "SOL", "ARB", "AVAX", "MATIC"]

    keyboard = []

    # Create rows of 3 coins each
    for i in range(0, len(top_coins), 3):
        row = [
            InlineKeyboardButton(coin, callback_data=f"select_coin:{coin}")
            for coin in top_coins[i : i + 3]
        ]
        keyboard.append(row)

    # Add custom input option and back button
    keyboard.append([InlineKeyboardButton("✏️ Enter Custom", callback_data="custom_coin")])
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])

    return InlineKeyboardMarkup(keyboard)


def build_buy_sell_menu(coin: str) -> InlineKeyboardMarkup:
    """
    Build buy/sell selection menu for a coin.

    Args:
        coin: Coin symbol

    Returns:
        InlineKeyboardMarkup with buy/sell buttons
    """
    keyboard = [
        [
            InlineKeyboardButton(f"🟢 Buy {coin}", callback_data=f"side_buy:{coin}"),
            InlineKeyboardButton(f"🔴 Sell {coin}", callback_data=f"side_sell:{coin}"),
        ],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_confirm_cancel(action: str, data: str = "") -> InlineKeyboardMarkup:
    """
    Build confirm/cancel buttons.

    Args:
        action: Action type (e.g., 'market', 'close', 'scale')
        data: Additional data to pass (e.g., coin:size:price)

    Returns:
        InlineKeyboardMarkup with confirm/cancel buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}:{data}"),
            InlineKeyboardButton("❌ Cancel", callback_data="menu_main"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_quick_amounts_menu() -> InlineKeyboardMarkup:
    """
    Build quick amount selection menu (for USD).

    Returns:
        InlineKeyboardMarkup with preset USD amounts
    """
    keyboard = [
        [
            InlineKeyboardButton("$10", callback_data="amount:10"),
            InlineKeyboardButton("$25", callback_data="amount:25"),
            InlineKeyboardButton("$50", callback_data="amount:50"),
        ],
        [
            InlineKeyboardButton("$100", callback_data="amount:100"),
            InlineKeyboardButton("$250", callback_data="amount:250"),
            InlineKeyboardButton("$500", callback_data="amount:500"),
        ],
        [InlineKeyboardButton("✏️ Enter Custom", callback_data="custom_amount")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_rebalance_menu() -> InlineKeyboardMarkup:
    """Build rebalance strategy selection menu."""
    keyboard = [
        [InlineKeyboardButton("⚖️ Equal Weight", callback_data="rebalance_equal")],
        [InlineKeyboardButton("📊 Custom Weights", callback_data="rebalance_custom")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_scale_order_menu() -> InlineKeyboardMarkup:
    """Build scale order configuration menu."""
    keyboard = [
        [InlineKeyboardButton("📊 Start Scale Order", callback_data="scale_start")],
        [InlineKeyboardButton("ℹ️ What is a Scale Order?", callback_data="scale_info")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_num_orders_menu() -> InlineKeyboardMarkup:
    """Build number of orders selection for scale orders."""
    keyboard = [
        [
            InlineKeyboardButton("3", callback_data="num_orders:3"),
            InlineKeyboardButton("5", callback_data="num_orders:5"),
            InlineKeyboardButton("10", callback_data="num_orders:10"),
        ],
        [
            InlineKeyboardButton("15", callback_data="num_orders:15"),
            InlineKeyboardButton("20", callback_data="num_orders:20"),
        ],
        [InlineKeyboardButton("✏️ Enter Custom (2-20)", callback_data="custom_num_orders")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")],
    ]
    return InlineKeyboardMarkup(keyboard)
