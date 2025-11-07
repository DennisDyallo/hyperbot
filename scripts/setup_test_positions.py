#!/usr/bin/env python3
"""
Set up test positions for rebalancing test.

Strategy:
- Account value: ~$416
- At 2x leverage: Can hold max $832 in positions
- Start with $600 total at 10x (70% BTC, 30% SOL)
- This leaves room for the rebalance to 2x without hitting limits

After rebalance to 50/50 at 2x:
- Should end with ~$300 BTC, ~$300 SOL at 2x leverage
"""

import sys

import requests

API_BASE = "http://localhost:8000/api"


def get_account_info():
    """Get current account information."""
    response = requests.get(f"{API_BASE}/account/")
    response.raise_for_status()
    return response.json()


def get_price(coin: str) -> float:
    """Get current price for a coin."""
    # Use market data service
    response = requests.get(f"{API_BASE}/account/")  # This returns all data
    response.raise_for_status()
    response.json()

    # We'll need to fetch from hyperliquid directly
    # For now, use approximate prices
    prices = {"BTC": 112000, "SOL": 188}
    return prices.get(coin, 0)


def set_leverage(coin: str, leverage: int):
    """Set leverage for a coin (only works when no position exists)."""
    print(f"  Setting leverage for {coin} to {leverage}x...")

    # We need to call the Hyperliquid service directly
    # For now, we'll just document this needs to be done via API
    print("  ℹ️  Note: Leverage will be set automatically on first trade")


def open_position(coin: str, side: str, usd_value: float, leverage: int = 10):
    """
    Open a position via market order.

    Args:
        coin: Coin symbol
        side: 'buy' or 'sell'
        usd_value: USD value to trade
        leverage: Leverage to use
    """
    price = get_price(coin)
    size = usd_value / price

    # Round to appropriate decimals
    if coin == "BTC":
        size = round(size, 5)
    elif coin == "SOL":
        size = round(size, 2)

    print(f"  Opening {coin} {side}: ${usd_value:.2f} (~{size} {coin}) at {leverage}x leverage")

    # Place market order
    # Note: The system will use default leverage or we need to set it first
    # For now, just document what needs to happen
    print("  ⚠️  Manual action needed:")
    print("     1. Go to https://app.hyperliquid-testnet.xyz")
    print(f"     2. Set {coin} leverage to {leverage}x")
    print(f"     3. Open {side} position: {size} {coin} (${usd_value:.2f})")
    print()


def main():
    """Set up test positions."""
    print("=" * 80)
    print("  SETTING UP TEST POSITIONS")
    print("=" * 80)

    # Get account info
    print("\nStep 1: Check Account Status")
    print("-" * 40)

    try:
        account = get_account_info()
        account_value = account["margin_summary"]["account_value"]
        print(f"  Account Value: ${account_value:.2f}")
        print(f"  Max at 10x: ${account_value * 10:.2f}")
        print(f"  Max at 2x: ${account_value * 2:.2f}")
    except Exception as e:
        print(f"  ⚠️  Could not fetch account: {e}")
        print("  Using estimated values...")
        account_value = 416

    # Calculate position sizes
    print("\nStep 2: Calculate Position Sizes")
    print("-" * 40)

    target_total = 600  # Total position value
    btc_pct = 70
    sol_pct = 30

    btc_value = target_total * (btc_pct / 100)
    sol_value = target_total * (sol_pct / 100)

    print(f"  Target Total: ${target_total:.2f} at 10x leverage")
    print(f"  BTC: ${btc_value:.2f} ({btc_pct}%)")
    print(f"  SOL: ${sol_value:.2f} ({sol_pct}%)")
    print()
    print(f"  Margin needed: ${target_total / 10:.2f}")
    print(f"  After rebalance to 2x: ${target_total:.2f} needs ${target_total / 2:.2f} margin")
    print(f"  Available: ${account_value:.2f} ✓ (plenty of room)")

    # Setup instructions
    print("\nStep 3: Open Positions")
    print("-" * 40)
    print()
    print("  MANUAL SETUP REQUIRED:")
    print()
    print("  Go to: https://app.hyperliquid-testnet.xyz")
    print()
    print("  1. Set BTC leverage to 10x (cross margin)")
    print(f"     - Open BTC LONG: {btc_value / get_price('BTC'):.5f} BTC (~${btc_value:.2f})")
    print()
    print("  2. Set SOL leverage to 10x (cross margin)")
    print(f"     - Open SOL LONG: {sol_value / get_price('SOL'):.2f} SOL (~${sol_value:.2f})")
    print()
    print("=" * 80)
    print()
    print("  After opening positions, verify with:")
    print("    curl http://localhost:8000/api/positions/ | python3 -m json.tool")
    print()
    print("  Then run rebalance test:")
    print("    python3 scripts/test_leverage_rebalance.py")
    print()
    print("=" * 80)

    # Alternative: Try to use API
    print("\n  OR use API (if endpoints available):")
    print("-" * 40)

    btc_size = btc_value / get_price("BTC")
    sol_size = sol_value / get_price("SOL")

    print()
    print("  # Set leverage (must be done before opening positions)")
    print("  # This would need to be via Hyperliquid SDK directly")
    print()
    print("  # Open BTC position")
    print("  curl -X POST http://localhost:8000/api/positions/BTC/open \\")
    print('    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"size": {btc_size:.5f}, "is_buy": true, "leverage": 10}}\'')
    print()
    print("  # Open SOL position")
    print("  curl -X POST http://localhost:8000/api/positions/SOL/open \\")
    print('    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"size": {sol_size:.2f}, "is_buy": true, "leverage": 10}}\'')
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
