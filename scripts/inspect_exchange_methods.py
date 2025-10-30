#!/usr/bin/env python3
"""
Inspect Exchange client methods to find spot order support.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger
from src.services import hyperliquid_service


def main():
    """Discover Exchange API methods."""
    try:
        hyperliquid_service.initialize()
        exchange = hyperliquid_service.get_exchange_client()

        print("=" * 80)
        print("HYPERLIQUID EXCHANGE API METHODS:")
        print("=" * 80)

        methods = [m for m in dir(exchange) if not m.startswith('_')]
        for method in sorted(methods):
            attr = getattr(exchange, method)
            if callable(attr):
                print(f"  • {method}()")
                # Try to get docstring
                if hasattr(attr, '__doc__') and attr.__doc__:
                    doc = attr.__doc__.strip().split('\n')[0]
                    print(f"    → {doc}")

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
