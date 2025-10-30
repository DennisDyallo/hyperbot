#!/usr/bin/env python3
"""
Discover all available methods on Hyperliquid Info API client.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger, settings
from src.services import hyperliquid_service


def main():
    """Discover API methods."""
    try:
        hyperliquid_service.initialize()
        info = hyperliquid_service.get_info_client()

        print("=" * 80)
        print("HYPERLIQUID INFO API METHODS:")
        print("=" * 80)

        methods = [m for m in dir(info) if not m.startswith('_')]
        for method in sorted(methods):
            attr = getattr(info, method)
            if callable(attr):
                print(f"  • {method}()")
                # Try to get docstring
                if hasattr(attr, '__doc__') and attr.__doc__:
                    doc = attr.__doc__.strip().split('\n')[0]
                    print(f"    → {doc}")

        # Try spot balance query
        print("\n" + "=" * 80)
        print("TESTING SPOT BALANCE QUERY:")
        print("=" * 80)

        # Try user_spot_state or spot_user_state
        for method_name in ['user_spot_state', 'spot_user_state', 'spot_clearinghouse_state', 'all_assets']:
            if hasattr(info, method_name):
                print(f"\n✓ Found method: {method_name}()")
                try:
                    result = getattr(info, method_name)(settings.HYPERLIQUID_WALLET_ADDRESS)
                    print(f"Result: {result}")
                except Exception as e:
                    print(f"Error calling {method_name}: {e}")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
