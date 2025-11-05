#!/usr/bin/env python3
"""
Test script to verify scale order wizard dependencies.

Run this to check if the wizard will work before starting the bot.
"""
import sys

def test_imports():
    """Test all required imports."""
    print("Testing imports...")
    try:
        from src.bot.handlers.scale_orders import ScaleOrderWizard, scale_order_conversation
        from src.services.market_data_service import market_data_service
        from src.services.scale_order_service import scale_order_service
        from src.services.hyperliquid_service import hyperliquid_service
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hyperliquid():
    """Test Hyperliquid service initialization."""
    print("\nTesting Hyperliquid service...")
    try:
        from src.services.hyperliquid_service import hyperliquid_service

        if not hyperliquid_service._initialized:
            hyperliquid_service.initialize()

        print("✅ Hyperliquid service initialized")
        return True
    except Exception as e:
        print(f"❌ Hyperliquid error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_data():
    """Test market data service."""
    print("\nTesting market data service...")
    try:
        from src.services.market_data_service import market_data_service

        # Try to get BTC price
        btc_price = market_data_service.get_price("BTC")
        print(f"✅ BTC price: ${btc_price:,.2f}")

        # Try to get ETH price
        eth_price = market_data_service.get_price("ETH")
        print(f"✅ ETH price: ${eth_price:,.2f}")

        return True
    except Exception as e:
        print(f"❌ Market data error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_handler():
    """Test conversation handler setup."""
    print("\nTesting conversation handler...")
    try:
        from src.bot.handlers.scale_orders import scale_order_conversation

        # Check entry points
        entry_points = scale_order_conversation.entry_points
        print(f"✅ Entry points: {len(entry_points)} handlers")

        # Check states
        states = scale_order_conversation.states
        print(f"✅ States: {len(states)} states defined")

        # Check fallbacks
        fallbacks = scale_order_conversation.fallbacks
        print(f"✅ Fallbacks: {len(fallbacks)} handlers")

        return True
    except Exception as e:
        print(f"❌ Conversation handler error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Scale Order Wizard Diagnostic Test")
    print("=" * 60)

    results = {
        "Imports": test_imports(),
        "Hyperliquid Service": test_hyperliquid(),
        "Market Data Service": test_market_data(),
        "Conversation Handler": test_conversation_handler(),
    }

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25} {status}")

    print("=" * 60)

    if all(results.values()):
        print("\n✅ All tests passed! The wizard should work.")
        print("\nTo test the wizard:")
        print("1. Restart the bot: uv run python -m src.bot.main")
        print("2. In Telegram, send: /scale")
        print("3. When prompted, enter: BTC")
        print("4. You should see inline keyboard buttons!")
        return 0
    else:
        print("\n❌ Some tests failed. Fix errors above before using wizard.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
