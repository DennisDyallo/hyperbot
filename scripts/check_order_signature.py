#!/usr/bin/env python3
"""
Check order() method signature to understand spot vs perps.
"""
import sys
import inspect
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services import hyperliquid_service


def main():
    """Check order method signature."""
    try:
        hyperliquid_service.initialize()
        exchange = hyperliquid_service.get_exchange_client()

        # Get method signatures
        for method_name in ['order', 'market_open', 'market_close']:
            if hasattr(exchange, method_name):
                method = getattr(exchange, method_name)
                sig = inspect.signature(method)
                print(f"\n{method_name}{sig}")
                print(f"Docstring: {method.__doc__[:200] if method.__doc__ else 'None'}...")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
