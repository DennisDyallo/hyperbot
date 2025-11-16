"""
Direct WebSocket test to diagnose notification issue.

This script tests the Hyperliquid WebSocket connection directly
without going through our service layer to isolate the problem.
"""

import asyncio
import time
from datetime import datetime

from hyperliquid.info import Info
from hyperliquid.utils import constants

from src.config import settings

# Track events received
events_received = []
last_event_time = None


def on_user_event(event):
    """Callback for user events."""
    global last_event_time, events_received

    now = datetime.now()
    last_event_time = now
    events_received.append(event)

    print(f"\n{'=' * 60}")
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] EVENT RECEIVED!")
    print(f"{'=' * 60}")
    print(f"Channel: {event.get('channel')}")
    print(f"Data keys: {list(event.get('data', {}).keys())}")

    # Check for fills
    data = event.get("data", {})
    if "fills" in data:
        fills = data["fills"]
        print(f"\n🎯 FILL EVENT DETECTED - {len(fills)} fills")
        for i, fill in enumerate(fills, 1):
            print(f"\nFill #{i}:")
            print(f"  Coin: {fill.get('coin')}")
            print(f"  Side: {fill.get('side')}")
            print(f"  Size: {fill.get('sz')}")
            print(f"  Price: {fill.get('px')}")
            print(f"  Time: {fill.get('time')}")
    else:
        print(f"Data: {data}")

    print(f"{'=' * 60}\n")


async def test_websocket():
    """Test WebSocket connection directly."""
    print("=" * 80)
    print("HYPERLIQUID WEBSOCKET DIRECT TEST")
    print("=" * 80)
    print(f"\nTestnet: {settings.HYPERLIQUID_TESTNET}")
    print(f"Wallet: {settings.HYPERLIQUID_WALLET_ADDRESS}")

    # Determine base URL
    base_url = (
        constants.TESTNET_API_URL if settings.HYPERLIQUID_TESTNET else constants.MAINNET_API_URL
    )
    print(f"Base URL: {base_url}")

    print("\n" + "-" * 80)
    print("STEP 1: Creating WebSocket-enabled Info client (skip_ws=False)")
    print("-" * 80)

    try:
        info_ws = Info(base_url, skip_ws=False)
        print("✅ WebSocket Info client created")
    except Exception as e:
        print(f"❌ Failed to create WebSocket client: {e}")
        return

    print("\n" + "-" * 80)
    print("STEP 2: Subscribing to userEvents")
    print("-" * 80)

    try:
        info_ws.subscribe(
            subscription={"type": "userEvents", "user": settings.HYPERLIQUID_WALLET_ADDRESS},
            callback=on_user_event,
        )
        print(f"✅ Subscribed to userEvents for {settings.HYPERLIQUID_WALLET_ADDRESS}")
    except Exception as e:
        print(f"❌ Failed to subscribe: {e}")
        return

    print("\n" + "-" * 80)
    print("STEP 3: Waiting for events (60 seconds)")
    print("-" * 80)
    print("\nListening for WebSocket events...")
    print("To test: Place an order on Hyperliquid and it should appear here.\n")

    # Wait for events
    start_time = time.time()
    duration = 60  # seconds

    while time.time() - start_time < duration:
        elapsed = int(time.time() - start_time)
        remaining = duration - elapsed

        # Print status every 5 seconds
        if elapsed % 5 == 0 and elapsed > 0:
            print(f"⏱️  [{elapsed}s] Still listening... ({remaining}s remaining)")
            print(f"   Events received so far: {len(events_received)}")
            if last_event_time:
                age = (datetime.now() - last_event_time).total_seconds()
                print(f"   Last event: {age:.1f}s ago")

        await asyncio.sleep(1)

    print("\n" + "-" * 80)
    print("STEP 4: Results")
    print("-" * 80)

    if events_received:
        print(f"✅ SUCCESS: Received {len(events_received)} events")
        print(f"   Last event: {last_event_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nEvent types:")
        for event in events_received:
            data = event.get("data", {})
            event_types = list(data.keys())
            print(f"   - {', '.join(event_types)}")
    else:
        print("⚠️  NO EVENTS RECEIVED")
        print("\nPossible reasons:")
        print("1. No trading activity during test window")
        print("2. WebSocket connection not working")
        print("3. Subscription not active")
        print("4. SDK threading/async issue")
        print("\nTroubleshooting:")
        print("- Try placing a test order on Hyperliquid during the test")
        print("- Check if WebSocket connection is actually established")
        print("- Verify wallet address is correct")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
