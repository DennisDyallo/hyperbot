"""
Advanced WebSocket diagnostic to check threading issues.

Tests if the WebSocket thread is actually running and receiving data.
"""

import asyncio
import threading
import time
from datetime import datetime

from hyperliquid.info import Info
from hyperliquid.utils import constants

from src.config import settings

# Track thread state
websocket_thread_alive = False
events_received = []
callback_called_count = 0


def on_user_event(event):
    """Callback for user events."""
    global events_received, callback_called_count

    callback_called_count += 1
    events_received.append(event)

    print(f"\n{'=' * 60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] CALLBACK INVOKED! (#{callback_called_count})")
    print(f"Event channel: {event.get('channel')}")
    print(f"Event data keys: {list(event.get('data', {}).keys())}")
    print(f"{'=' * 60}\n")


async def test_websocket_threading():
    """Test WebSocket threading behavior."""
    print("=" * 80)
    print("HYPERLIQUID WEBSOCKET THREADING TEST")
    print("=" * 80)
    print(f"\nWallet: {settings.HYPERLIQUID_WALLET_ADDRESS}")

    base_url = (
        constants.TESTNET_API_URL if settings.HYPERLIQUID_TESTNET else constants.MAINNET_API_URL
    )

    print(f"Base URL: {base_url}")
    print("\n" + "-" * 80)
    print("Creating WebSocket client...")
    print("-" * 80)

    info_ws = Info(base_url, skip_ws=False)
    print("✅ WebSocket client created")

    print("\n" + "-" * 80)
    print("Inspecting WebSocket internals...")
    print("-" * 80)

    # Check if WebSocket has internal state
    if hasattr(info_ws, "ws"):
        print(f"WebSocket object exists: {info_ws.ws}")
        if hasattr(info_ws.ws, "ws"):
            print(f"  Inner WebSocket: {info_ws.ws.ws}")
    else:
        print("⚠️  No 'ws' attribute found on Info client")

    # Check for threads
    print(f"\nActive threads before subscription: {threading.active_count()}")
    for thread in threading.enumerate():
        print(f"  - {thread.name} (daemon={thread.daemon}, alive={thread.is_alive()})")

    print("\n" + "-" * 80)
    print("Subscribing to userEvents...")
    print("-" * 80)

    info_ws.subscribe(
        subscription={"type": "userEvents", "user": settings.HYPERLIQUID_WALLET_ADDRESS},
        callback=on_user_event,
    )
    print("✅ Subscription call completed")

    # Wait a bit for thread to spawn
    await asyncio.sleep(2)

    print(f"\nActive threads after subscription: {threading.active_count()}")
    for thread in threading.enumerate():
        print(f"  - {thread.name} (daemon={thread.daemon}, alive={thread.is_alive()})")

    print("\n" + "-" * 80)
    print("Waiting 30 seconds for events...")
    print("-" * 80)

    start_time = time.time()
    duration = 30

    while time.time() - start_time < duration:
        elapsed = int(time.time() - start_time)

        if elapsed % 5 == 0 and elapsed > 0:
            alive_count = threading.active_count()
            print(
                f"⏱️  [{elapsed}s] Events: {len(events_received)}, Callbacks: {callback_called_count}, Threads: {alive_count}"
            )

        await asyncio.sleep(1)

    print("\n" + "-" * 80)
    print("RESULTS")
    print("-" * 80)
    print(f"Callback invoked: {callback_called_count} times")
    print(f"Events received: {len(events_received)}")
    print(f"Final thread count: {threading.active_count()}")

    if callback_called_count == 0:
        print("\n⚠️  CALLBACK NEVER INVOKED")
        print("\nPossible causes:")
        print("1. WebSocket thread not running")
        print("2. WebSocket connection not established")
        print("3. SDK bug with callback dispatch")
        print("4. No events during test window")

        print("\nActive threads at end:")
        for thread in threading.enumerate():
            print(f"  - {thread.name} (daemon={thread.daemon}, alive={thread.is_alive()})")
    else:
        print(f"\n✅ Callback working! Received {callback_called_count} events")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        asyncio.run(test_websocket_threading())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
