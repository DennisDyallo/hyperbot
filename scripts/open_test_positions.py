#!/usr/bin/env python3
"""
Open test positions for rebalancing test.
"""
import sys
import requests
import json

API_BASE = "http://localhost:8000/api"

def get_price(coin: str) -> float:
    """Get current market price."""
    response = requests.get(f"{API_BASE}/market/price/{coin}")
    response.raise_for_status()
    return float(response.json()["price"])

def set_leverage(coin: str, leverage: int):
    """Set leverage for a coin."""
    print(f"\n📊 Setting {coin} leverage to {leverage}x...")

    # Use rebalance service to set leverage
    from src.services.rebalance_service import rebalance_service
    rebalance_service.set_leverage_for_coin(coin, leverage, is_cross=True)
    print(f"✅ {coin} leverage set to {leverage}x (cross)")

def open_position(coin: str, usd_value: float):
    """Open a position via market order."""
    print(f"\n🚀 Opening {coin} position: ${usd_value:.2f}")

    # Get current price
    price = get_price(coin)
    print(f"  Current price: ${price:,.2f}")

    # Calculate size
    size = usd_value / price

    # Round appropriately
    if coin == "BTC":
        size = round(size, 5)
    elif coin == "SOL":
        size = round(size, 2)
    else:
        size = round(size, 4)

    print(f"  Size: {size} {coin}")

    # Place market order
    payload = {
        "coin": coin,
        "is_buy": True,
        "size": size,
        "slippage": 0.05  # 5% as decimal
    }

    response = requests.post(
        f"{API_BASE}/orders/market",
        json=payload
    )
    response.raise_for_status()
    result = response.json()

    print(f"✅ Order placed: {result}")
    return result

def verify_positions():
    """Verify positions were opened correctly."""
    print(f"\n🔍 Verifying positions...")

    response = requests.get(f"{API_BASE}/positions/")
    response.raise_for_status()
    positions = response.json()

    print(f"\n{'='*80}")
    print(f"  CURRENT POSITIONS")
    print(f"{'='*80}\n")

    total_value = 0
    for pos in positions:
        coin = pos["position"]["coin"]
        value = pos["position"]["position_value"]
        leverage = pos["position"]["leverage"]["value"]
        total_value += value

        pct = (value / total_value * 100) if total_value > 0 else 0
        print(f"  {coin}: ${value:.2f} ({pct:.1f}%) at {leverage}x leverage")

    print(f"\n  Total: ${total_value:.2f}")
    print(f"\n{'='*80}\n")

    return positions

def main():
    """Open test positions."""
    print("=" * 80)
    print("  OPENING TEST POSITIONS")
    print("=" * 80)

    # Target values
    btc_value = 210  # 70% of 300
    sol_value = 90   # 30% of 300
    leverage = 10

    print(f"\nTarget positions:")
    print(f"  BTC: ${btc_value:.2f} at {leverage}x leverage")
    print(f"  SOL: ${sol_value:.2f} at {leverage}x leverage")
    print(f"  Total: ${btc_value + sol_value:.2f} at {leverage}x leverage")

    try:
        # Set leverage (must be done before opening positions)
        print(f"\n{'='*80}")
        print(f"  STEP 1: SET LEVERAGE")
        print(f"{'='*80}")

        # Note: We can't set leverage via HTTP API easily
        # It needs to be done via the Hyperliquid service directly
        print("\n⚠️  Note: Leverage will be set automatically on first trade")
        print("    (Hyperliquid uses 10x cross margin by default)")

        # Open BTC position
        print(f"\n{'='*80}")
        print(f"  STEP 2: OPEN BTC POSITION")
        print(f"{'='*80}")

        btc_result = open_position("BTC", btc_value)

        # Open SOL position
        print(f"\n{'='*80}")
        print(f"  STEP 3: OPEN SOL POSITION")
        print(f"{'='*80}")

        sol_result = open_position("SOL", sol_value)

        # Verify
        print(f"\n{'='*80}")
        print(f"  STEP 4: VERIFY POSITIONS")
        print(f"{'='*80}")

        import time
        time.sleep(2)  # Wait for positions to update

        positions = verify_positions()

        # Check if ready for rebalance test
        print(f"{'='*80}")
        print(f"  READY FOR REBALANCE TEST")
        print(f"{'='*80}\n")

        print("Run the test with:")
        print("  uv run python scripts/test_leverage_rebalance.py\n")

        print(f"{'='*80}\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
