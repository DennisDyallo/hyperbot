"""
Unit tests for bot menu builders.

Tests the menu construction functions that create inline keyboards.

MIGRATION STATUS: ✅ REVIEWED - NO CHANGES NEEDED
- This file tests pure functions (menu builders) with no mocks
- No Telegram Update/Context mocks used
- No service mocks used
- All 16 tests passing (100% coverage on src/bot/menus.py)
- Date: 2025-11-06
"""
import pytest
from telegram import InlineKeyboardButton
from src.bot.menus import (
    build_main_menu,
    build_back_button,
    build_with_back,
    build_positions_menu,
    build_coin_selection_menu,
    build_buy_sell_menu,
    build_confirm_cancel,
    build_quick_amounts_menu,
    build_rebalance_menu,
    build_scale_order_menu,
    build_num_orders_menu
)


class TestBuildMainMenu:
    """Test build_main_menu function."""

    def test_main_menu_structure(self):
        """Test main menu has correct structure."""
        menu = build_main_menu()

        # Should have 4 rows (info, trading, advanced, utility)
        assert len(menu.inline_keyboard) == 4

        # First row: Account, Positions
        assert len(menu.inline_keyboard[0]) == 2
        assert menu.inline_keyboard[0][0].text == "📊 Account"
        assert menu.inline_keyboard[0][0].callback_data == "menu_account"
        assert menu.inline_keyboard[0][1].text == "📈 Positions"
        assert menu.inline_keyboard[0][1].callback_data == "menu_positions"

        # Second row: Market Order, Close Position
        assert len(menu.inline_keyboard[1]) == 2
        assert menu.inline_keyboard[1][0].text == "💰 Market Order"
        assert menu.inline_keyboard[1][0].callback_data == "menu_market"

        # Third row: Rebalance, Scale Order
        assert len(menu.inline_keyboard[2]) == 2
        assert menu.inline_keyboard[2][0].text == "⚖️ Rebalance"
        assert menu.inline_keyboard[2][0].callback_data == "menu_rebalance"

        # Fourth row: Help, Status
        assert len(menu.inline_keyboard[3]) == 2
        assert menu.inline_keyboard[3][0].text == "ℹ️ Help"
        assert menu.inline_keyboard[3][0].callback_data == "menu_help"


class TestBuildBackButton:
    """Test build_back_button function."""

    def test_back_button_structure(self):
        """Test back button has correct structure."""
        menu = build_back_button()

        assert len(menu.inline_keyboard) == 1
        assert len(menu.inline_keyboard[0]) == 1
        assert menu.inline_keyboard[0][0].text == "🏠 Main Menu"
        assert menu.inline_keyboard[0][0].callback_data == "menu_main"


class TestBuildWithBack:
    """Test build_with_back function."""

    def test_adds_back_button_to_empty_list(self):
        """Test adding back button to empty button list."""
        buttons = []
        menu = build_with_back(buttons)

        assert len(menu.inline_keyboard) == 1
        assert menu.inline_keyboard[0][0].text == "🏠 Main Menu"

    def test_adds_back_button_to_existing_buttons(self):
        """Test adding back button to existing buttons."""
        buttons = [
            [InlineKeyboardButton("Button 1", callback_data="btn1")],
            [InlineKeyboardButton("Button 2", callback_data="btn2")]
        ]
        menu = build_with_back(buttons)

        # Should have 3 rows now (2 original + 1 back)
        assert len(menu.inline_keyboard) == 3
        assert menu.inline_keyboard[0][0].text == "Button 1"
        assert menu.inline_keyboard[1][0].text == "Button 2"
        assert menu.inline_keyboard[2][0].text == "🏠 Main Menu"


class TestBuildPositionsMenu:
    """Test build_positions_menu function."""

    def test_positions_menu_with_multiple_positions(self):
        """Test menu with multiple positions."""
        positions = [
            {
                "position": {
                    "coin": "BTC",
                    "size": 0.5,
                    "unrealized_pnl": 125.50
                }
            },
            {
                "position": {
                    "coin": "ETH",
                    "size": -2.5,
                    "unrealized_pnl": -50.25
                }
            }
        ]

        menu = build_positions_menu(positions)

        # Should have 3 rows (2 positions + back button)
        assert len(menu.inline_keyboard) == 3

        # First position (long with profit)
        assert "🟢" in menu.inline_keyboard[0][0].text  # Long position
        assert "BTC" in menu.inline_keyboard[0][0].text
        assert "📈" in menu.inline_keyboard[0][0].text  # Positive PnL
        assert "$125.50" in menu.inline_keyboard[0][0].text
        assert menu.inline_keyboard[0][0].callback_data == "select_position:BTC"

        # Second position (short with loss)
        assert "🔴" in menu.inline_keyboard[1][0].text  # Short position
        assert "ETH" in menu.inline_keyboard[1][0].text
        assert "📉" in menu.inline_keyboard[1][0].text  # Negative PnL
        assert menu.inline_keyboard[1][0].callback_data == "select_position:ETH"

        # Back button
        assert menu.inline_keyboard[2][0].text == "🏠 Main Menu"

    def test_positions_menu_limits_to_10(self):
        """Test menu limits positions to 10."""
        positions = [
            {"position": {"coin": f"COIN{i}", "size": 1.0, "unrealized_pnl": 10.0}}
            for i in range(15)
        ]

        menu = build_positions_menu(positions)

        # Should have 11 rows (10 positions + back button)
        assert len(menu.inline_keyboard) == 11

    def test_positions_menu_empty_list(self):
        """Test menu with no positions."""
        positions = []

        menu = build_positions_menu(positions)

        # Should have 2 rows ("No Positions" + back button)
        assert len(menu.inline_keyboard) == 2
        assert "❌ No Positions" in menu.inline_keyboard[0][0].text
        assert menu.inline_keyboard[0][0].callback_data == "noop"


class TestBuildCoinSelectionMenu:
    """Test build_coin_selection_menu function."""

    def test_coin_menu_with_default_coins(self):
        """Test coin selection with default coins."""
        menu = build_coin_selection_menu()

        # Should have default coins + custom + back = 2 coin rows + 2 extra rows
        assert len(menu.inline_keyboard) == 4

        # First row should have 3 coins
        assert len(menu.inline_keyboard[0]) == 3
        assert menu.inline_keyboard[0][0].text == "BTC"
        assert menu.inline_keyboard[0][0].callback_data == "select_coin:BTC"

        # Second row should have remaining coins
        assert len(menu.inline_keyboard[1]) == 3

        # Custom input option
        assert "✏️ Enter Custom" in menu.inline_keyboard[2][0].text
        assert menu.inline_keyboard[2][0].callback_data == "custom_coin"

        # Back button
        assert menu.inline_keyboard[3][0].text == "🏠 Main Menu"

    def test_coin_menu_with_custom_coins(self):
        """Test coin selection with custom coin list."""
        custom_coins = ["ATOM", "LINK", "UNI"]
        menu = build_coin_selection_menu(custom_coins)

        # Should have 1 coin row + custom + back = 3 rows
        assert len(menu.inline_keyboard) == 3

        # First row should have all 3 custom coins
        assert len(menu.inline_keyboard[0]) == 3
        assert menu.inline_keyboard[0][0].text == "ATOM"
        assert menu.inline_keyboard[0][1].text == "LINK"
        assert menu.inline_keyboard[0][2].text == "UNI"


class TestBuildBuySellMenu:
    """Test build_buy_sell_menu function."""

    def test_buy_sell_menu_structure(self):
        """Test buy/sell menu has correct structure."""
        menu = build_buy_sell_menu("BTC")

        assert len(menu.inline_keyboard) == 2

        # Buy/Sell row
        assert len(menu.inline_keyboard[0]) == 2
        assert "Buy BTC" in menu.inline_keyboard[0][0].text
        assert menu.inline_keyboard[0][0].callback_data == "side_buy:BTC"
        assert "Sell BTC" in menu.inline_keyboard[0][1].text
        assert menu.inline_keyboard[0][1].callback_data == "side_sell:BTC"

        # Back button
        assert menu.inline_keyboard[1][0].text == "🏠 Main Menu"


class TestBuildConfirmCancel:
    """Test build_confirm_cancel function."""

    def test_confirm_cancel_with_action_only(self):
        """Test confirm/cancel with just action."""
        menu = build_confirm_cancel("market")

        assert len(menu.inline_keyboard) == 1
        assert len(menu.inline_keyboard[0]) == 2
        assert "✅ Confirm" in menu.inline_keyboard[0][0].text
        assert menu.inline_keyboard[0][0].callback_data == "confirm_market:"
        assert "❌ Cancel" in menu.inline_keyboard[0][1].text
        assert menu.inline_keyboard[0][1].callback_data == "menu_main"

    def test_confirm_cancel_with_data(self):
        """Test confirm/cancel with action and data."""
        menu = build_confirm_cancel("close", "BTC:0.5")

        assert menu.inline_keyboard[0][0].callback_data == "confirm_close:BTC:0.5"


class TestBuildQuickAmountsMenu:
    """Test build_quick_amounts_menu function."""

    def test_quick_amounts_menu_structure(self):
        """Test quick amounts menu has all preset options."""
        menu = build_quick_amounts_menu()

        # Should have 4 rows (2 amount rows + custom + back)
        assert len(menu.inline_keyboard) == 4

        # First row: $10, $25, $50
        assert len(menu.inline_keyboard[0]) == 3
        assert menu.inline_keyboard[0][0].text == "$10"
        assert menu.inline_keyboard[0][0].callback_data == "amount:10"
        assert menu.inline_keyboard[0][2].text == "$50"

        # Second row: $100, $250, $500
        assert len(menu.inline_keyboard[1]) == 3
        assert menu.inline_keyboard[1][0].text == "$100"
        assert menu.inline_keyboard[1][2].text == "$500"

        # Custom input
        assert "✏️ Enter Custom" in menu.inline_keyboard[2][0].text

        # Back button
        assert menu.inline_keyboard[3][0].text == "🏠 Main Menu"


class TestBuildRebalanceMenu:
    """Test build_rebalance_menu function."""

    def test_rebalance_menu_structure(self):
        """Test rebalance menu has correct options."""
        menu = build_rebalance_menu()

        assert len(menu.inline_keyboard) == 3

        # Equal Weight option
        assert "Equal Weight" in menu.inline_keyboard[0][0].text
        assert menu.inline_keyboard[0][0].callback_data == "rebalance_equal"

        # Custom Weights option
        assert "Custom Weights" in menu.inline_keyboard[1][0].text
        assert menu.inline_keyboard[1][0].callback_data == "rebalance_custom"

        # Back button
        assert menu.inline_keyboard[2][0].text == "🏠 Main Menu"


class TestBuildScaleOrderMenu:
    """Test build_scale_order_menu function."""

    def test_scale_order_menu_structure(self):
        """Test scale order menu has correct options."""
        menu = build_scale_order_menu()

        assert len(menu.inline_keyboard) == 3

        # Start Scale Order option
        assert "Start Scale Order" in menu.inline_keyboard[0][0].text
        assert menu.inline_keyboard[0][0].callback_data == "scale_start"

        # Info option
        assert "What is a Scale Order" in menu.inline_keyboard[1][0].text
        assert menu.inline_keyboard[1][0].callback_data == "scale_info"

        # Back button
        assert menu.inline_keyboard[2][0].text == "🏠 Main Menu"


class TestBuildNumOrdersMenu:
    """Test build_num_orders_menu function."""

    def test_num_orders_menu_structure(self):
        """Test number of orders menu has all options."""
        menu = build_num_orders_menu()

        # Should have 4 rows (2 number rows + custom + back)
        assert len(menu.inline_keyboard) == 4

        # First row: 3, 5, 10
        assert len(menu.inline_keyboard[0]) == 3
        assert menu.inline_keyboard[0][0].text == "3"
        assert menu.inline_keyboard[0][0].callback_data == "num_orders:3"
        assert menu.inline_keyboard[0][1].text == "5"
        assert menu.inline_keyboard[0][2].text == "10"

        # Second row: 15, 20
        assert len(menu.inline_keyboard[1]) == 2
        assert menu.inline_keyboard[1][0].text == "15"
        assert menu.inline_keyboard[1][1].text == "20"

        # Custom input
        assert "Enter Custom" in menu.inline_keyboard[2][0].text
        assert menu.inline_keyboard[2][0].callback_data == "custom_num_orders"

        # Back button
        assert menu.inline_keyboard[3][0].text == "🏠 Main Menu"
