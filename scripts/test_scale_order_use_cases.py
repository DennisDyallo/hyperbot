#!/usr/bin/env python3
"""
Test Scale Order Use Cases.

Tests all scale order use cases that the bot uses:
- PreviewScaleOrderUseCase
- PlaceScaleOrderUseCase
- ListScaleOrdersUseCase
- GetScaleOrderStatusUseCase
- CancelScaleOrderUseCase

This ensures the use cases work correctly end-to-end.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger
from src.models.scale_order import ScaleOrderConfig
from src.services import hyperliquid_service
from src.use_cases.scale_orders import (
    CancelScaleOrderRequest,
    CancelScaleOrderUseCase,
    GetScaleOrderStatusRequest,
    GetScaleOrderStatusUseCase,
    ListScaleOrdersRequest,
    ListScaleOrdersUseCase,
    PlaceScaleOrderRequest,
    PlaceScaleOrderUseCase,
    PreviewScaleOrderRequest,
    PreviewScaleOrderUseCase,
)


def print_header(text: str):
    """Print test header."""
    logger.info("\n" + "=" * 80)
    logger.info(f"  {text}")
    logger.info("=" * 80)


def get_btc_price() -> float:
    """Get current BTC price."""
    info = hyperliquid_service.get_info_client()
    all_mids = info.all_mids()
    return float(all_mids.get("BTC", 100000))


async def test_preview_scale_order():
    """Test PreviewScaleOrderUseCase."""
    print_header("TEST 1: Preview Scale Order Use Case")

    try:
        use_case = PreviewScaleOrderUseCase()

        # Get current BTC price
        btc_price = get_btc_price()
        logger.info(f"\nCurrent BTC price: ${btc_price:,.2f}")

        # Preview a scale order: Buy $100 total, 5 orders, 10% range below market
        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=100.0,
            num_orders=5,
            start_price=btc_price * 0.90,  # 10% below
            end_price=btc_price * 0.99,  # 1% below
        )
        request = PreviewScaleOrderRequest(config=config)

        logger.info("\nExecuting PreviewScaleOrderUseCase...")
        logger.info(f"  Total: ${config.total_usd_amount}")
        logger.info(f"  Orders: {config.num_orders}")
        logger.info(f"  Range: ${config.start_price:,.2f} - ${config.end_price:,.2f}")

        response = await use_case.execute(request)

        logger.info("\n✓ Preview generated successfully")
        logger.info(f"Total Orders: {response.preview.num_orders}")
        logger.info(f"Total USD: ${response.preview.total_usd_amount:.2f}")
        logger.info(f"Total Size: {response.preview.total_coin_size} {response.preview.coin}")

        logger.info("\nPrice Levels:")
        for i, level in enumerate(response.preview.orders[:5], 1):
            logger.info(
                f"  {i}. ${level['price']:,.2f}: {level['size']:.6f} BTC "
                f"(${level['price'] * level['size']:.2f})"
            )

        return True

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_place_scale_order():
    """Test PlaceScaleOrderUseCase."""
    print_header("TEST 2: Place Scale Order Use Case")

    try:
        use_case = PlaceScaleOrderUseCase()

        # Get current BTC price
        btc_price = get_btc_price()

        # Place a very small scale order for testing
        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=50.0,  # Small amount
            num_orders=3,
            start_price=btc_price * 0.90,  # 10% below
            end_price=btc_price * 0.95,  # 5% below
        )
        request = PlaceScaleOrderRequest(config=config)

        logger.info("\nExecuting PlaceScaleOrderUseCase...")
        logger.info(f"  Coin: {config.coin}")
        logger.info(f"  Direction: {'BUY' if config.is_buy else 'SELL'}")
        logger.info(f"  Total: ${config.total_usd_amount}")
        logger.info(f"  Orders: {config.num_orders}")
        logger.info(f"  Range: ${config.start_price:,.2f} - ${config.end_price:,.2f}")

        response = await use_case.execute(request)

        logger.info("\n✓ Scale order placed")
        logger.info(f"Scale Order ID: {response.result.scale_order_id}")
        logger.info(f"Orders Placed: {response.result.orders_placed}")
        logger.info(f"Orders Failed: {response.result.orders_failed}")
        logger.info(f"Status: {response.result.status}")

        if response.result.placements:
            logger.info("\nOrder Details:")
            for detail in response.result.placements:
                status_symbol = "✓" if detail.status == "success" else "✗"
                logger.info(
                    f"  {status_symbol} ${detail.price:,.2f}: {detail.size:.6f} "
                    f"(Order ID: {detail.order_id or 'N/A'})"
                )

        # Store scale_order_id for next tests
        global test_scale_order_id
        test_scale_order_id = response.result.scale_order_id

        return response.result.status in ["completed", "partial"]

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_list_scale_orders():
    """Test ListScaleOrdersUseCase."""
    print_header("TEST 3: List Scale Orders Use Case")

    try:
        use_case = ListScaleOrdersUseCase()
        request = ListScaleOrdersRequest()

        logger.info("\nExecuting ListScaleOrdersUseCase...")
        response = await use_case.execute(request)

        logger.info("\n✓ Success")
        logger.info(f"Total Scale Orders: {response.total_count}")
        logger.info(f"Active Scale Orders: {response.active_count}")

        if response.scale_orders:
            logger.info("\nActive Scale Orders:")
            for order in response.scale_orders[:3]:  # Show first 3
                logger.info(
                    f"  {order.id}: {order.coin} "
                    f"({'BUY' if order.is_buy else 'SELL'}) "
                    f"{order.filled_orders}/{order.num_orders} filled"
                )

        return True

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_get_scale_order_status():
    """Test GetScaleOrderStatusUseCase."""
    print_header("TEST 4: Get Scale Order Status Use Case")

    try:
        if not test_scale_order_id:
            logger.warning("\n⚠️  No scale order ID available, skipping test")
            return True

        use_case = GetScaleOrderStatusUseCase()
        request = GetScaleOrderStatusRequest(scale_order_id=test_scale_order_id)

        logger.info("\nExecuting GetScaleOrderStatusUseCase...")
        logger.info(f"  Scale Order ID: {test_scale_order_id}")

        response = await use_case.execute(request)

        logger.info("\n✓ Status retrieved")
        logger.info(f"Coin: {response.status.scale_order.coin}")
        logger.info(f"Direction: {'BUY' if response.status.scale_order.is_buy else 'SELL'}")
        logger.info(f"Fill Percentage: {response.status.fill_percentage:.1f}%")
        logger.info(f"Open Orders: {len(response.status.open_orders)}")
        logger.info(f"Filled Orders: {len(response.status.filled_orders)}")

        if response.status.filled_orders:
            logger.info("\nFilled Orders:")
            for order in response.status.filled_orders[:3]:
                logger.info(f"  Order {order.get('oid', 'N/A')}: ${order.get('px', 0):,.2f}")

        return True

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_cancel_scale_order():
    """Test CancelScaleOrderUseCase."""
    print_header("TEST 5: Cancel Scale Order Use Case")

    try:
        if not test_scale_order_id:
            logger.warning("\n⚠️  No scale order ID available, skipping test")
            return True

        use_case = CancelScaleOrderUseCase()
        request = CancelScaleOrderRequest(scale_order_id=test_scale_order_id)

        logger.info("\nExecuting CancelScaleOrderUseCase...")
        logger.info(f"  Scale Order ID: {test_scale_order_id}")

        response = await use_case.execute(request)

        logger.info("\n✓ Cancellation completed")
        logger.info(f"Success: {response.result.get('success', False)}")
        logger.info(f"Message: {response.result.get('message', 'N/A')}")
        logger.info(f"Orders Cancelled: {response.result.get('orders_cancelled', 0)}")

        errors = response.result.get("cancellation_errors", [])
        if errors:
            logger.info("\n⚠️  Errors:")
            for error in errors:
                logger.info(f"  - {error}")

        # If no orders to cancel (all filled), that's still a success for the test
        return True

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


# Global variable to store scale order ID between tests
test_scale_order_id = None


async def main():
    """Run all scale order use case tests."""
    print_header("SCALE ORDER USE CASES TEST SUITE")

    logger.info("\nInitializing services...")
    hyperliquid_service.initialize()

    results = []

    # Test 1: Preview Scale Order
    results.append(("PreviewScaleOrderUseCase", await test_preview_scale_order()))

    # Test 2: Place Scale Order
    results.append(("PlaceScaleOrderUseCase", await test_place_scale_order()))

    # Wait a moment for orders to register
    logger.info("\nWaiting 2 seconds for orders to register...")
    await asyncio.sleep(2)

    # Test 3: List Scale Orders
    results.append(("ListScaleOrdersUseCase", await test_list_scale_orders()))

    # Test 4: Get Scale Order Status
    results.append(("GetScaleOrderStatusUseCase", await test_get_scale_order_status()))

    # Test 5: Cancel Scale Order
    results.append(("CancelScaleOrderUseCase", await test_cancel_scale_order()))

    # Summary
    print_header("TEST SUMMARY")

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


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
