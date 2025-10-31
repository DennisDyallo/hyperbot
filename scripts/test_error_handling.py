#!/usr/bin/env python3
"""
Test error handling for Hyperliquid responses.

Verifies that the API properly detects and raises exceptions for
failed operations (e.g., invalid tick size, insufficient balance, etc.)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger
from src.services import hyperliquid_service, order_service


def test_invalid_tick_size():
    """Test that invalid tick size raises ValueError."""
    logger.info("=" * 80)
    logger.info("TEST: Invalid Tick Size Error Handling")
    logger.info("=" * 80)

    try:
        # Get current BTC price
        info = hyperliquid_service.get_info_client()
        all_mids = info.all_mids()
        btc_price = float(all_mids.get("BTC", 100000))

        # Try to place limit order with price NOT divisible by tick size
        # Use an odd decimal that will fail tick size validation
        invalid_price = round(btc_price * 0.80, 3)  # 3 decimals will fail

        logger.info(f"\nAttempting limit order with invalid price: ${invalid_price}")
        logger.info("Expected: ValueError should be raised")

        result = order_service.place_limit_order(
            coin="BTC",
            is_buy=True,
            size=0.0001,  # Small size
            limit_price=invalid_price,
            time_in_force="Gtc",
        )

        # If we get here, error handling FAILED
        logger.error("❌ TEST FAILED: No exception was raised!")
        logger.error(f"Result: {result}")
        return False

    except ValueError as e:
        # This is the expected behavior
        logger.info(f"\n✅ TEST PASSED: ValueError raised as expected")
        logger.info(f"Error message: {e}")
        return True

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: Wrong exception type: {type(e).__name__}")
        logger.error(f"Error: {e}")
        return False


def test_successful_market_order():
    """Test that successful orders don't raise exceptions."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Successful Market Order (No Exception)")
    logger.info("=" * 80)

    try:
        # Get current BTC price
        info = hyperliquid_service.get_info_client()
        all_mids = info.all_mids()
        btc_price = float(all_mids.get("BTC", 100000))

        # Calculate small size ($10)
        size = round(10 / btc_price, 4)

        logger.info(f"\nPlacing small market buy order: {size} BTC (~$10)")
        logger.info("Expected: Should complete without exception")

        result = order_service.place_market_order(
            coin="BTC", is_buy=True, size=size, slippage=0.05
        )

        # Check that we got success status
        if result.get("status") == "success":
            logger.info(f"\n✅ TEST PASSED: Order placed successfully")
            logger.info(f"Result: {result['result']}")
            return True
        else:
            logger.error(f"\n❌ TEST FAILED: Status is not 'success'")
            logger.error(f"Result: {result}")
            return False

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: Unexpected exception: {type(e).__name__}")
        logger.error(f"Error: {e}")
        return False


def main():
    """Run all error handling tests."""
    try:
        # Initialize services
        hyperliquid_service.initialize()

        # Run tests
        results = []

        # Test 1: Invalid tick size should raise ValueError
        results.append(("Invalid Tick Size", test_invalid_tick_size()))

        # Test 2: Valid order should not raise exception
        results.append(("Successful Order", test_successful_market_order()))

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status}: {test_name}")

        logger.info(f"\nResults: {passed}/{total} tests passed")

        if passed == total:
            logger.info("\n🎉 ALL TESTS PASSED!")
            return 0
        else:
            logger.error(f"\n❌ {total - passed} TEST(S) FAILED")
            return 1

    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
