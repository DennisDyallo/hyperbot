#!/usr/bin/env python3
"""
Test order operations on Hyperliquid testnet using the same use cases as the bot.

Tests the following workflow:
1. Place small $20 market buy order on BTC (via PlaceOrderUseCase)
2. Close the position (via ClosePositionUseCase)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger
from src.services import hyperliquid_service
from src.use_cases.trading import (
    ClosePositionRequest,
    ClosePositionUseCase,
    PlaceOrderRequest,
    PlaceOrderUseCase,
)


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
    # Round to 5 decimal places (typical for BTC)
    return round(size, 5)


async def main():
    """Run order operations test."""
    logger.info("=" * 80)
    logger.info("TESTING ORDER OPERATIONS (Using Bot Use Cases)")
    logger.info("=" * 80)

    try:
        # Initialize services
        hyperliquid_service.initialize()

        # Get current BTC price
        logger.info("\n1. Getting current BTC price...")
        btc_price = get_btc_price()
        logger.info(f"   BTC Price: ${btc_price:,.2f}")

        # Calculate order size
        market_order_size = calculate_order_size(20, btc_price)
        logger.info(f"   Market order size: {market_order_size} BTC (~$20)")

        # Step 1: Place market buy order using PlaceOrderUseCase (same as bot)
        logger.info("\n2. Placing market BUY order via PlaceOrderUseCase (SAME AS BOT)...")
        place_order_use_case = PlaceOrderUseCase()
        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=True,
            coin_size=market_order_size,
            is_market=True,
            slippage=0.05,  # 5% slippage
            reduce_only=False,
        )

        response = await place_order_use_case.execute(request)
        logger.info(f"   ✓ Market order placed: {response.status}")
        logger.info(
            f"   Coin: {response.coin}, Size: {response.size}, Price: ${response.price:,.2f}"
        )
        logger.info(f"   USD Value: ${response.usd_value:,.2f}")

        # Wait a moment for order to process
        logger.info("\n3. Waiting 2 seconds for order to process...")
        await asyncio.sleep(2)

        # Step 2: Get current BTC position
        logger.info("\n4. Checking BTC position...")
        from src.services import position_service

        btc_position = position_service.get_position("BTC")

        if btc_position:
            position_size = abs(float(btc_position["position"]["size"]))
            position_value = float(btc_position["position"]["position_value"])
            logger.info(f"   ✓ Current BTC position: {position_size} BTC (${position_value:,.2f})")

            # Close position using ClosePositionUseCase (same as bot)
            logger.info("\n5. Closing BTC position via ClosePositionUseCase (SAME AS BOT)...")
            close_position_use_case = ClosePositionUseCase()
            close_request = ClosePositionRequest(
                coin="BTC",
                slippage=0.05,
            )

            close_response = await close_position_use_case.execute(close_request)
            logger.info(f"   ✓ Close position result: {close_response.status}")
            logger.info(
                f"   Size closed: {close_response.size_closed}, USD value: ${close_response.usd_value:.2f}"
            )
        else:
            logger.warning("   ✗ No BTC position found (market buy may not have filled yet)")

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
    sys.exit(asyncio.run(main()))
