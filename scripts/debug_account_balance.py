#!/usr/bin/env python3
"""
Debug script to inspect raw Hyperliquid API responses for account balance.
Helps identify why balances aren't showing up correctly.
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger, settings
from src.services import hyperliquid_service


def main():
    """Debug account balance API response."""
    logger.info("=" * 80)
    logger.info("Account Balance Debug Script")
    logger.info("=" * 80)

    # Initialize service
    try:
        hyperliquid_service.initialize()
        info = hyperliquid_service.get_info_client()
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        return 1

    logger.info(f"Wallet Address: {settings.HYPERLIQUID_WALLET_ADDRESS}")
    logger.info(f"Testnet: {settings.HYPERLIQUID_TESTNET}")
    logger.info("")

    # Get raw user_state response
    try:
        logger.info("Fetching raw user_state from Hyperliquid API...")
        user_state = info.user_state(settings.HYPERLIQUID_WALLET_ADDRESS)

        logger.info("\n" + "=" * 80)
        logger.info("RAW API RESPONSE:")
        logger.info("=" * 80)
        print(json.dumps(user_state, indent=2))

        logger.info("\n" + "=" * 80)
        logger.info("ANALYSIS:")
        logger.info("=" * 80)

        # Analyze specific fields
        if "marginSummary" in user_state:
            logger.info("\n📊 Margin Summary:")
            for key, value in user_state["marginSummary"].items():
                logger.info(f"  {key}: {value}")
        else:
            logger.warning("❌ No 'marginSummary' in response")

        if "crossMarginSummary" in user_state:
            logger.info("\n📊 Cross Margin Summary:")
            for key, value in user_state["crossMarginSummary"].items():
                logger.info(f"  {key}: {value}")

        if "withdrawable" in user_state:
            logger.info(f"\n💰 Withdrawable: {user_state['withdrawable']}")
        else:
            logger.warning("❌ No 'withdrawable' field")

        if "assetPositions" in user_state:
            logger.info(f"\n📈 Asset Positions: {len(user_state['assetPositions'])} positions")
            for i, asset_pos in enumerate(user_state["assetPositions"]):
                logger.info(f"\n  Position {i+1}:")
                print(json.dumps(asset_pos, indent=4))
        else:
            logger.warning("❌ No 'assetPositions' in response")

        # Check for spot balance fields
        logger.info("\n" + "=" * 80)
        logger.info("CHECKING FOR SPOT BALANCE FIELDS:")
        logger.info("=" * 80)

        for key in user_state.keys():
            if "spot" in key.lower() or "balance" in key.lower():
                logger.info(f"✓ Found key: {key}")
                logger.info(f"  Value: {user_state[key]}")

        # List all top-level keys
        logger.info("\n" + "=" * 80)
        logger.info("ALL TOP-LEVEL KEYS IN RESPONSE:")
        logger.info("=" * 80)
        for key in user_state.keys():
            logger.info(f"  - {key}")

    except Exception as e:
        logger.error(f"Failed to fetch user_state: {e}")
        import traceback
        traceback.print_exc()
        return 1

    logger.info("\n" + "=" * 80)
    logger.info("Debug script complete!")
    logger.info("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
