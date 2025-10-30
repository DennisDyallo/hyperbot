#!/usr/bin/env python3
"""
Manual test script for Hyperliquid service.
Tests connection and basic API functionality.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger, settings
from src.services import hyperliquid_service


def main():
    """Run Hyperliquid service tests."""
    logger.info("=" * 60)
    logger.info("Hyperliquid Service Test")
    logger.info("=" * 60)

    # Display configuration
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Testnet: {settings.HYPERLIQUID_TESTNET}")
    logger.info(f"Wallet Address: {settings.HYPERLIQUID_WALLET_ADDRESS or 'Not configured'}")
    logger.info("")

    # Initialize service
    try:
        logger.info("Initializing Hyperliquid service...")
        hyperliquid_service.initialize()
        logger.info("✓ Service initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize service: {e}")
        return 1

    logger.info("")

    # Run health check
    try:
        logger.info("Running health check...")
        health = hyperliquid_service.health_check()

        logger.info(f"Status: {health['status']}")
        logger.info(f"Info API: {'✓' if health['info_api'] else '✗'}")
        logger.info(f"Exchange API: {'✓' if health.get('exchange_api') else '✗'}")

        if health.get("available_pairs"):
            logger.info(f"Available trading pairs: {health['available_pairs']}")

        if health.get("account_value"):
            logger.info(f"Account value: ${health['account_value']}")

        if health.get("info_api_error"):
            logger.error(f"Info API error: {health['info_api_error']}")

        if health.get("exchange_api_error"):
            logger.error(f"Exchange API error: {health['exchange_api_error']}")

    except Exception as e:
        logger.error(f"✗ Health check failed: {e}")
        return 1

    logger.info("")

    # Test Info API - Get market data
    if health["info_api"]:
        try:
            logger.info("Testing Info API - Fetching market data...")
            info = hyperliquid_service.get_info_client()

            # Get all mid prices
            mids = info.all_mids()
            logger.info(f"✓ Fetched {len(mids)} market prices")

            # Show a few examples
            logger.info("Sample prices:")
            for i, (coin, price) in enumerate(list(mids.items())[:5]):
                logger.info(f"  {coin}: ${float(price):,.2f}")

        except Exception as e:
            logger.error(f"✗ Info API test failed: {e}")

    logger.info("")

    # Test Exchange API - Get account info
    if health.get("exchange_api") and settings.HYPERLIQUID_WALLET_ADDRESS:
        try:
            logger.info("Testing Exchange API - Fetching account info...")
            info = hyperliquid_service.get_info_client()

            user_state = info.user_state(settings.HYPERLIQUID_WALLET_ADDRESS)

            # Display account summary
            margin_summary = user_state.get("marginSummary", {})
            logger.info(f"Account Value: ${float(margin_summary.get('accountValue', 0)):,.2f}")
            logger.info(f"Total Margin Used: ${float(margin_summary.get('totalMarginUsed', 0)):,.2f}")
            logger.info(f"Total Raw USD: ${float(margin_summary.get('totalRawUsd', 0)):,.2f}")

            # Display positions
            positions = user_state.get("assetPositions", [])
            logger.info(f"Open Positions: {len(positions)}")

            if positions:
                logger.info("Positions:")
                for pos in positions:
                    p = pos.get("position", {})
                    coin = p.get("coin", "Unknown")
                    size = p.get("szi", "0")
                    entry = p.get("entryPx", "0")
                    pnl = p.get("unrealizedPnl", "0")
                    logger.info(f"  {coin}: size={size}, entry=${float(entry):,.2f}, PnL=${float(pnl):,.2f}")

            logger.info("✓ Exchange API test successful")

        except Exception as e:
            logger.error(f"✗ Exchange API test failed: {e}")

    logger.info("")
    logger.info("=" * 60)
    logger.info("Test complete!")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
