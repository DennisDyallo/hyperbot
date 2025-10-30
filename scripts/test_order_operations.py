#!/usr/bin/env python3
"""
Test order operations on Hyperliquid testnet.

Tests the following workflow:
1. Place small $20 limit buy order on BTC
2. Place small $20 market buy order on BTC
3. Place small sell BTC order to close position
4. List all open orders
5. Cancel all orders
"""
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger
from src.services import hyperliquid_service, order_service


def get_btc_price() -> float:
    """Get current BTC price from market data."""
    info = hyperliquid_service.get_info_client()
    all_mids = info.all_mids()

    # Find BTC price
    for coin, price in all_mids.items():
        if coin.upper() == "BTC":
            return float(price)

    raise RuntimeError("Could not find BTC price")


def calculate_order_size(usd_amount: float, btc_price: float) -> float:
    """Calculate BTC order size for given USD amount."""
    size = usd_amount / btc_price
    # Round to 4 decimal places (typical for BTC)
    return round(size, 4)


def main():
    """Run order operations test."""
    logger.info("=" * 80)
    logger.info("TESTING ORDER OPERATIONS")
    logger.info("=" * 80)

    try:
        # Initialize services
        hyperliquid_service.initialize()

        # Get current BTC price
        logger.info("\n1. Getting current BTC price...")
        btc_price = get_btc_price()
        logger.info(f"   BTC Price: ${btc_price:,.2f}")

        # Calculate order sizes
        limit_order_size = calculate_order_size(20, btc_price)
        market_order_size = calculate_order_size(20, btc_price)
        logger.info(f"   Limit order size: {limit_order_size} BTC (~$20)")
        logger.info(f"   Market order size: {market_order_size} BTC (~$20)")

        # Step 1: Place limit buy order (far below market to avoid fill)
        logger.info("\n2. Placing limit buy order (20% below market)...")
        limit_price = round(btc_price * 0.80, 2)  # 20% below market
        logger.info(f"   Limit price: ${limit_price:,.2f}")

        limit_result = order_service.place_limit_order(
            coin="BTC",
            is_buy=True,
            size=limit_order_size,
            limit_price=limit_price,
            time_in_force="Gtc"
        )
        logger.info(f"   ✓ Limit order placed: {limit_result.get('status')}")
        logger.info(f"   Result: {limit_result.get('result')}")

        # Step 2: Place market buy order
        logger.info("\n3. Placing market buy order...")
        market_result = order_service.place_market_order(
            coin="BTC",
            is_buy=True,
            size=market_order_size,
            slippage=0.05  # 5% slippage
        )
        logger.info(f"   ✓ Market order placed: {market_result.get('status')}")
        logger.info(f"   Result: {market_result.get('result')}")

        # Step 3: List open orders
        logger.info("\n4. Listing open orders...")
        open_orders = order_service.list_open_orders()
        logger.info(f"   Open orders: {len(open_orders)}")
        for i, order in enumerate(open_orders, 1):
            logger.info(f"   Order {i}: {order.get('coin')} - {order.get('side')} {order.get('sz')} @ {order.get('limitPx', 'MARKET')}")

        # Step 4: Get current BTC position to determine sell size
        logger.info("\n5. Checking BTC position for sell order...")
        from src.services import position_service
        btc_position = position_service.get_position("BTC")

        if btc_position:
            position_size = abs(float(btc_position['position']['size']))
            logger.info(f"   Current BTC position: {position_size} BTC")

            # Place sell order to close position
            logger.info("\n6. Placing market sell order to close position...")
            sell_result = order_service.place_market_order(
                coin="BTC",
                is_buy=False,
                size=position_size,
                slippage=0.05
            )
            logger.info(f"   ✓ Sell order placed: {sell_result.get('status')}")
            logger.info(f"   Result: {sell_result.get('result')}")
        else:
            logger.warning("   No BTC position found (market buy may not have filled yet)")

        # Step 5: List open orders again
        logger.info("\n7. Listing open orders (after sell)...")
        open_orders_2 = order_service.list_open_orders()
        logger.info(f"   Open orders: {len(open_orders_2)}")
        for i, order in enumerate(open_orders_2, 1):
            logger.info(f"   Order {i}: {order.get('coin')} - {order.get('side')} {order.get('sz')} @ {order.get('limitPx', 'MARKET')}")

        # Step 6: Cancel all orders
        logger.info("\n8. Canceling all open orders...")
        cancel_result = order_service.cancel_all_orders()
        logger.info(f"   ✓ Cancel result: {cancel_result.get('status')}")
        logger.info(f"   Result: {cancel_result.get('result')}")

        # Final check
        logger.info("\n9. Final check - listing open orders...")
        final_orders = order_service.list_open_orders()
        logger.info(f"   Remaining open orders: {len(final_orders)}")

        logger.info("\n" + "=" * 80)
        logger.info("✓ TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
