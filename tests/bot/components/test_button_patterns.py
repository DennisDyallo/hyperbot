"""
Tests for ButtonBuilder pattern methods.

Validates the new wizard-friendly pattern methods that replace menu.py functions.
"""

from src.bot.components.buttons import ButtonBuilder


class TestCoinSelection:
    """Test coin selection pattern."""

    def test_coin_selection_default(self) -> None:
        """Test coin selection with default coins."""
        builder = ButtonBuilder()
        markup = builder.coin_selection().build()

        buttons = markup.inline_keyboard

        # Should have 2 rows of 3 coins + custom row
        assert len(buttons) == 3
        assert len(buttons[0]) == 3  # First row: BTC, ETH, SOL
        assert len(buttons[1]) == 3  # Second row: ARB, AVAX, MATIC
        assert len(buttons[2]) == 1  # Custom input

        # Check first coin
        assert buttons[0][0].text == "BTC"
        assert buttons[0][0].callback_data == "select_coin:BTC"

        # Check custom button
        assert "Custom" in buttons[2][0].text
        assert buttons[2][0].callback_data == "custom_coin"

    def test_coin_selection_custom_list(self) -> None:
        """Test coin selection with custom coin list."""
        builder = ButtonBuilder()
        coins = ["DOGE", "PEPE", "SHIB"]
        markup = builder.coin_selection(coins=coins).build()

        buttons = markup.inline_keyboard

        assert len(buttons) == 2  # 1 row of coins + custom
        assert buttons[0][0].text == "DOGE"
        assert buttons[0][1].text == "PEPE"
        assert buttons[0][2].text == "SHIB"

    def test_coin_selection_custom_per_row(self) -> None:
        """Test coin selection with custom per_row."""
        builder = ButtonBuilder()
        coins = ["BTC", "ETH", "SOL", "ARB"]
        markup = builder.coin_selection(coins=coins, per_row=2).build()

        buttons = markup.inline_keyboard

        # Should have 2 rows of 2 coins + custom
        assert len(buttons) == 3
        assert len(buttons[0]) == 2  # BTC, ETH
        assert len(buttons[1]) == 2  # SOL, ARB

    def test_coin_selection_no_custom(self) -> None:
        """Test coin selection without custom input option."""
        builder = ButtonBuilder()
        markup = builder.coin_selection(add_custom=False).build()

        buttons = markup.inline_keyboard

        # Should only have coin rows, no custom
        assert len(buttons) == 2
        assert all("Custom" not in row[0].text for row in buttons)

    def test_coin_selection_custom_prefix(self) -> None:
        """Test coin selection with custom callback prefix."""
        builder = ButtonBuilder()
        markup = builder.coin_selection(
            coins=["BTC"], callback_prefix="coin", add_custom=False
        ).build()

        buttons = markup.inline_keyboard
        assert buttons[0][0].callback_data == "coin:BTC"


class TestBuySell:
    """Test buy/sell toggle pattern."""

    def test_buy_sell_default(self) -> None:
        """Test buy/sell buttons with default prefix."""
        builder = ButtonBuilder()
        markup = builder.buy_sell("BTC").build()

        buttons = markup.inline_keyboard

        assert len(buttons) == 1  # Single row
        assert len(buttons[0]) == 2  # Buy and Sell

        # Check buy button
        assert "Buy BTC" in buttons[0][0].text
        assert "🟢" in buttons[0][0].text
        assert buttons[0][0].callback_data == "side_buy:BTC"

        # Check sell button
        assert "Sell BTC" in buttons[0][1].text
        assert "🔴" in buttons[0][1].text
        assert buttons[0][1].callback_data == "side_sell:BTC"

    def test_buy_sell_custom_prefix(self) -> None:
        """Test buy/sell buttons with custom callback prefix."""
        builder = ButtonBuilder()
        markup = builder.buy_sell("ETH", callback_prefix="trade").build()

        buttons = markup.inline_keyboard
        assert buttons[0][0].callback_data == "trade_buy:ETH"
        assert buttons[0][1].callback_data == "trade_sell:ETH"

    def test_buy_sell_different_coins(self) -> None:
        """Test buy/sell buttons for different coins."""
        for coin in ["BTC", "ETH", "SOL"]:
            builder = ButtonBuilder()
            markup = builder.buy_sell(coin).build()

            buttons = markup.inline_keyboard
            assert f"Buy {coin}" in buttons[0][0].text
            assert f"Sell {coin}" in buttons[0][1].text


class TestAmountPresets:
    """Test amount preset pattern."""

    def test_amount_presets_default(self) -> None:
        """Test amount presets with default amounts."""
        builder = ButtonBuilder()
        markup = builder.amount_presets().build()

        buttons = markup.inline_keyboard

        # Should have 2 rows of 3 amounts + custom
        assert len(buttons) == 3
        assert len(buttons[0]) == 3  # $10, $25, $50
        assert len(buttons[1]) == 3  # $100, $250, $500
        assert len(buttons[2]) == 1  # Custom input

        # Check first amount
        assert buttons[0][0].text == "$10"
        assert buttons[0][0].callback_data == "amount:10"

        # Check custom button
        assert "Custom" in buttons[2][0].text
        assert buttons[2][0].callback_data == "custom_amount"

    def test_amount_presets_custom_list(self) -> None:
        """Test amount presets with custom amounts."""
        builder = ButtonBuilder()
        amounts = [5, 20, 100]
        markup = builder.amount_presets(amounts=amounts).build()

        buttons = markup.inline_keyboard

        assert len(buttons) == 2  # 1 row of amounts + custom
        assert buttons[0][0].text == "$5"
        assert buttons[0][1].text == "$20"
        assert buttons[0][2].text == "$100"

    def test_amount_presets_custom_per_row(self) -> None:
        """Test amount presets with custom per_row."""
        builder = ButtonBuilder()
        amounts = [10, 50, 100, 500]
        markup = builder.amount_presets(amounts=amounts, per_row=2).build()

        buttons = markup.inline_keyboard

        # Should have 2 rows of 2 amounts + custom
        assert len(buttons) == 3
        assert len(buttons[0]) == 2  # $10, $50
        assert len(buttons[1]) == 2  # $100, $500

    def test_amount_presets_no_custom(self) -> None:
        """Test amount presets without custom input option."""
        builder = ButtonBuilder()
        markup = builder.amount_presets(add_custom=False).build()

        buttons = markup.inline_keyboard

        # Should only have amount rows, no custom
        assert len(buttons) == 2
        assert all("Custom" not in row[0].text for row in buttons)

    def test_amount_presets_custom_prefix(self) -> None:
        """Test amount presets with custom callback prefix."""
        builder = ButtonBuilder()
        markup = builder.amount_presets(
            amounts=[100], callback_prefix="usd", add_custom=False
        ).build()

        buttons = markup.inline_keyboard
        assert buttons[0][0].callback_data == "usd:100"


class TestLeverageLevels:
    """Test leverage level selection pattern."""

    def test_leverage_levels_default(self) -> None:
        """Test leverage levels with defaults."""
        builder = ButtonBuilder()
        markup = builder.leverage_levels().build()

        buttons = markup.inline_keyboard

        # Should have 2 rows (1, 3, 5, 10) and (20)
        assert len(buttons) == 2
        assert len(buttons[0]) == 4  # 1x, 3x, 5x, 10x
        assert len(buttons[1]) == 1  # 20x

        # Check first level
        assert buttons[0][0].text == "1x"
        assert buttons[0][0].callback_data == "leverage:1"

        # Check last level
        assert buttons[1][0].text == "20x"
        assert buttons[1][0].callback_data == "leverage:20"

    def test_leverage_levels_custom_list(self) -> None:
        """Test leverage levels with custom levels."""
        builder = ButtonBuilder()
        levels = [1, 5, 10]
        markup = builder.leverage_levels(levels=levels).build()

        buttons = markup.inline_keyboard

        assert len(buttons) == 1  # All fit in one row
        assert len(buttons[0]) == 3
        assert buttons[0][0].text == "1x"
        assert buttons[0][1].text == "5x"
        assert buttons[0][2].text == "10x"

    def test_leverage_levels_with_highlight(self) -> None:
        """Test leverage levels with highlighted recommended level."""
        builder = ButtonBuilder()
        markup = builder.leverage_levels(highlight_level=5).build()

        buttons = markup.inline_keyboard

        # Find the 5x button (should be in first row, index 2)
        button_5x = buttons[0][2]
        assert "5x" in button_5x.text
        assert "✨" in button_5x.text
        assert button_5x.callback_data == "leverage:5"

        # Other buttons should not have highlight
        assert "✨" not in buttons[0][0].text  # 1x
        assert "✨" not in buttons[0][1].text  # 3x

    def test_leverage_levels_custom_per_row(self) -> None:
        """Test leverage levels with custom per_row."""
        builder = ButtonBuilder()
        levels = [1, 3, 5, 10]
        markup = builder.leverage_levels(levels=levels, per_row=2).build()

        buttons = markup.inline_keyboard

        # Should have 2 rows of 2 levels
        assert len(buttons) == 2
        assert len(buttons[0]) == 2  # 1x, 3x
        assert len(buttons[1]) == 2  # 5x, 10x

    def test_leverage_levels_custom_prefix(self) -> None:
        """Test leverage levels with custom callback prefix."""
        builder = ButtonBuilder()
        markup = builder.leverage_levels(levels=[5], callback_prefix="lev").build()

        buttons = markup.inline_keyboard
        assert buttons[0][0].callback_data == "lev:5"


class TestConfirmCancel:
    """Test confirm/cancel button pattern."""

    def test_confirm_cancel_default(self) -> None:
        """Test confirm/cancel with default cancel label."""
        builder = ButtonBuilder()
        markup = builder.confirm_cancel("Buy $1,000 BTC", "confirm_buy").build()

        buttons = markup.inline_keyboard

        assert len(buttons) == 1  # Single row
        assert len(buttons[0]) == 2  # Confirm and Cancel

        # Check confirm button
        assert "Buy $1,000 BTC" in buttons[0][0].text
        assert "✅" in buttons[0][0].text
        assert buttons[0][0].callback_data == "confirm_buy"

        # Check cancel button
        assert "Cancel" in buttons[0][1].text
        assert "❌" in buttons[0][1].text
        assert buttons[0][1].callback_data == "cancel"

    def test_confirm_cancel_custom_labels(self) -> None:
        """Test confirm/cancel with custom labels."""
        builder = ButtonBuilder()
        markup = builder.confirm_cancel("Place Order", "order:place", "Go Back", "back").build()

        buttons = markup.inline_keyboard

        assert "Place Order" in buttons[0][0].text
        assert buttons[0][0].callback_data == "order:place"
        assert "Go Back" in buttons[0][1].text
        assert buttons[0][1].callback_data == "back"

    def test_confirm_cancel_different_actions(self) -> None:
        """Test confirm/cancel for different actions."""
        actions = [
            ("Buy BTC", "buy:BTC"),
            ("Sell ETH", "sell:ETH"),
            ("Close Position", "close:SOL"),
        ]

        for label, callback in actions:
            builder = ButtonBuilder()
            markup = builder.confirm_cancel(label, callback).build()

            buttons = markup.inline_keyboard
            assert label in buttons[0][0].text
            assert buttons[0][0].callback_data == callback


class TestButtonBuilderPatternChaining:
    """Test chaining multiple pattern methods."""

    def test_chain_coin_and_cancel(self) -> None:
        """Test chaining coin selection with cancel button."""
        builder = ButtonBuilder()
        markup = builder.coin_selection(coins=["BTC", "ETH"], add_custom=False).cancel().build()

        buttons = markup.inline_keyboard

        # Should have 1 row of coins + cancel
        assert len(buttons) == 2
        assert len(buttons[0]) == 2  # Coins
        assert len(buttons[1]) == 1  # Cancel
        assert "Cancel" in buttons[1][0].text

    def test_chain_amount_and_back(self) -> None:
        """Test chaining amount presets with back button."""
        builder = ButtonBuilder()
        markup = builder.amount_presets(amounts=[100, 500], add_custom=False).back().build()

        buttons = markup.inline_keyboard

        # Should have 1 row of amounts + back
        assert len(buttons) == 2
        assert "Back" in buttons[1][0].text

    def test_chain_leverage_and_confirm_cancel(self) -> None:
        """Test chaining leverage selection with confirm/cancel."""
        builder = ButtonBuilder()
        markup = (
            builder.leverage_levels(levels=[1, 5, 10])
            .confirm_cancel("Set Leverage", "set_lev")
            .build()
        )

        buttons = markup.inline_keyboard

        # Should have leverage rows + confirm/cancel row
        assert len(buttons) >= 2  # At least leverage row + confirm/cancel
        last_row = buttons[-1]
        assert len(last_row) == 2
        assert "Set Leverage" in last_row[0].text

    def test_chain_buy_sell_amount_confirm(self) -> None:
        """Test full wizard flow: buy/sell -> amount -> confirm."""
        builder = ButtonBuilder()
        markup = (
            builder.buy_sell("BTC")
            .amount_presets(amounts=[100, 500], add_custom=False)
            .confirm_cancel("Place Order", "place")
            .build()
        )

        buttons = markup.inline_keyboard

        # Should have buy/sell row + amount row + confirm/cancel row
        assert len(buttons) >= 3
        assert "Buy BTC" in buttons[0][0].text  # Buy/sell
        assert "$100" in buttons[1][0].text  # Amounts
        assert "Place Order" in buttons[-1][0].text  # Confirm


class TestButtonBuilderPatternIntegration:
    """Integration tests for button pattern methods."""

    def test_pattern_flushes_current_row(self) -> None:
        """Test that pattern methods properly flush current row."""
        builder = ButtonBuilder()
        # Add some actions to current row
        builder.action("Test 1", "test1")
        builder.action("Test 2", "test2")

        # Add pattern method - should flush and create new rows
        markup = builder.coin_selection(coins=["BTC"], add_custom=False).build()

        buttons = markup.inline_keyboard

        # Should have: action row + coin row
        assert len(buttons) == 2
        assert len(buttons[0]) == 2  # Actions
        assert buttons[0][0].text == "✅ Test 1"
        assert len(buttons[1]) == 1  # Coin

    def test_multiple_patterns_in_sequence(self) -> None:
        """Test multiple pattern methods don't interfere."""
        builder = ButtonBuilder()
        markup = (
            builder.coin_selection(coins=["BTC"], add_custom=False)
            .buy_sell("BTC")
            .amount_presets(amounts=[100], add_custom=False)
            .leverage_levels(levels=[5])
            .confirm_cancel("Go", "go")
            .build()
        )

        buttons = markup.inline_keyboard

        # Should have all sections
        assert len(buttons) >= 5
        assert "BTC" in buttons[0][0].text  # Coin
        assert "Buy BTC" in buttons[1][0].text  # Buy/sell
        assert "$100" in buttons[2][0].text  # Amount
        assert "5x" in buttons[3][0].text  # Leverage
        assert "Go" in buttons[-1][0].text  # Confirm
