#!/usr/bin/env python3
"""
Test error handling for Hyperliquid responses.

Verifies that the API properly detects and raises exceptions for
failed operations (e.g., invalid tick size, insufficient balance, etc.)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger
from src.services import hyperliquid_service
from src.use_cases.trading import PlaceOrderRequest, PlaceOrderUseCase


async def test_invalid_tick_size():
    """Test that invalid tick size raises RuntimeError (use case wraps ValueError)."""
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

        # Calculate size that meets $10 minimum
        size = round(15 / invalid_price, 4)  # ~$15 order to ensure above $10 minimum

        logger.info(f"\nAttempting limit order with invalid price: ${invalid_price}")
        logger.info(f"Order size: {size} BTC (~$15)")
        logger.info("Expected: RuntimeError should be raised (use case wraps service errors)")

        # Use PlaceOrderUseCase (same as bot)
        place_order_use_case = PlaceOrderUseCase()
        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=True,
            coin_size=size,
            is_market=False,
            limit_price=invalid_price,
        )

        response = await place_order_use_case.execute(request)

        # If we get here, error handling FAILED
        logger.error("❌ TEST FAILED: No exception was raised!")
        logger.error(f"Result: {response}")
        return False

    except RuntimeError as e:
        # This is the expected behavior - use case wraps errors in RuntimeError
        if "tick size" in str(e).lower():
            logger.info("\n✅ TEST PASSED: RuntimeError raised with tick size error as expected")
            logger.info(f"Error message: {e}")
            return True
        else:
            logger.error(f"\n❌ TEST FAILED: RuntimeError but wrong message: {e}")
            return False

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: Wrong exception type: {type(e).__name__}")
        logger.error(f"Error: {e}")
        return False


async def test_successful_market_order():
    """Test that successful orders don't raise exceptions."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: Successful Market Order (No Exception)")
    logger.info("=" * 80)

    try:
        # Get current BTC price
        info = hyperliquid_service.get_info_client()
        all_mids = info.all_mids()
        btc_price = float(all_mids.get("BTC", 100000))

        # Calculate small size ($20 to meet minimum order value)
        size = round(20 / btc_price, 4)

        logger.info(f"\nPlacing small market buy order: {size} BTC (~$20)")
        logger.info("Expected: Should complete without exception")

        # Use PlaceOrderUseCase (same as bot)
        place_order_use_case = PlaceOrderUseCase()
        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=True,
            coin_size=size,
            is_market=True,
            slippage=0.05,
        )

        response = await place_order_use_case.execute(request)

        # Check that we got success status
        if response.status == "success":
            logger.info("\n✅ TEST PASSED: Order placed successfully")
            logger.info(
                f"Result: {response.coin} {response.side} {response.size} @ ${response.price}"
            )
            return True
        else:
            logger.error("\n❌ TEST FAILED: Status is not 'success'")
            logger.error(f"Result: {response}")
            return False

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: Unexpected exception: {type(e).__name__}")
        logger.error(f"Error: {e}")
        return False


async def main():
    """Run all error handling tests."""
    try:
        # Initialize services
        hyperliquid_service.initialize()

        # Run tests
        results = []

        # Test 1: Invalid tick size should raise ValueError
        results.append(("Invalid Tick Size", await test_invalid_tick_size()))

        # Test 2: Valid order should not raise exception
        results.append(("Successful Order", await test_successful_market_order()))

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
    sys.exit(asyncio.run(main()))
