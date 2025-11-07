#!/usr/bin/env python3
"""
Test market data service functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger
from src.services import hyperliquid_service, market_data_service


def main():
    """Test market data service."""
    logger.info("=" * 80)
    logger.info("TESTING MARKET DATA SERVICE")
    logger.info("=" * 80)

    try:
        # Initialize services
        hyperliquid_service.initialize()

        # Test 1: Get all prices
        logger.info("\n1. Testing get_all_prices()...")
        prices = market_data_service.get_all_prices()
        logger.info(f"   ✓ Fetched {len(prices)} trading pairs")
        logger.info("   Sample prices:")
        for _i, (coin, price) in enumerate(list(prices.items())[:5]):
            logger.info(f"     - {coin}: ${price:,.2f}")
        if len(prices) > 5:
            logger.info(f"     ... and {len(prices) - 5} more")

        # Test 2: Get specific price
        logger.info("\n2. Testing get_price('BTC')...")
        btc_price = market_data_service.get_price("BTC")
        logger.info(f"   ✓ BTC Price: ${btc_price:,.2f}")

        # Test 3: Get market info
        logger.info("\n3. Testing get_market_info()...")
        market_info = market_data_service.get_market_info()
        universe = market_info.get("universe", [])
        logger.info("   ✓ Market info retrieved")
        logger.info(f"   Total trading pairs: {len(universe)}")
        if universe:
            logger.info("   Sample pair metadata:")
            btc_meta = next((a for a in universe if a.get("name") == "BTC"), None)
            if btc_meta:
                logger.info(f"     - Name: {btc_meta.get('name')}")
                logger.info(f"     - Size Decimals: {btc_meta.get('szDecimals')}")
                logger.info(f"     - Max Leverage: {btc_meta.get('maxLeverage')}")

        # Test 4: Get asset metadata
        logger.info("\n4. Testing get_asset_metadata('BTC')...")
        btc_metadata = market_data_service.get_asset_metadata("BTC")
        if btc_metadata:
            logger.info("   ✓ BTC Metadata:")
            logger.info(f"     - Tick size (szDecimals): {btc_metadata.get('szDecimals')}")
            logger.info(f"     - Max leverage: {btc_metadata.get('maxLeverage')}")
            logger.info(f"     - Only isolated: {btc_metadata.get('onlyIsolated')}")
        else:
            logger.warning("   ⚠ BTC metadata not found")

        # Test 5: Get order book
        logger.info("\n5. Testing get_order_book('BTC')...")
        order_book = market_data_service.get_order_book("BTC")
        logger.info("   ✓ Order book retrieved")
        levels = order_book.get("levels", [[], []])
        if levels and len(levels) >= 2:
            bids = levels[0]
            asks = levels[1]
            logger.info(f"   Bids: {len(bids)} levels")
            if bids:
                logger.info(f"     Best bid: {bids[0].get('px')} @ {bids[0].get('sz')}")
            logger.info(f"   Asks: {len(asks)} levels")
            if asks:
                logger.info(f"     Best ask: {asks[0].get('px')} @ {asks[0].get('sz')}")

        # Test 6: Error handling - invalid coin
        logger.info("\n6. Testing error handling (invalid coin)...")
        try:
            market_data_service.get_price("INVALID_COIN_123")
            logger.error("   ❌ Should have raised ValueError!")
            return 1
        except ValueError as e:
            logger.info(f"   ✓ Correctly raised ValueError: {e}")

        logger.info("\n" + "=" * 80)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
