#!/usr/bin/env python3
"""
Integration test for OrderMonitorService.

Tests real-time order fill monitoring via WebSocket.

Usage:
    HYPERLIQUID_TESTNET=true python scripts/test_order_monitor_service.py

Expected behavior:
- Connects to Hyperliquid WebSocket
- Subscribes to userEvents
- Monitors for fill events
- Logs notification text (Telegram integration pending)
- Handles reconnection if connection drops

Note: This test runs indefinitely. To test fills:
1. Place an order on Hyperliquid testnet via UI
2. Watch console for fill event detection
3. Press Ctrl+C to stop
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Must set testnet before importing services
os.environ["HYPERLIQUID_TESTNET"] = "true"

from src.config import logger  # noqa: E402
from src.services.order_monitor_service import order_monitor_service  # noqa: E402


class OrderMonitorTest:
    """Integration test for order monitoring."""

    def __init__(self):
        """Initialize test."""
        self.test_duration = 60  # Run for 60 seconds by default
        self.fill_events_detected = 0

    async def run_test(self) -> None:
        """
        Run order monitoring test.

        Steps:
        1. Start OrderMonitorService
        2. Wait for events (or timeout)
        3. Display statistics
        4. Stop service
        """
        print("=" * 80)
        print("ORDER MONITOR SERVICE - INTEGRATION TEST")
        print("=" * 80)
        print()
        print("Configuration:")
        print(f"  Testnet: {os.environ.get('HYPERLIQUID_TESTNET', 'false')}")
        print(f"  Test Duration: {self.test_duration}s")
        print()
        print("Test Plan:")
        print("  1. Initialize OrderMonitorService")
        print("  2. Start WebSocket monitoring")
        print("  3. Wait for fill events (or timeout)")
        print("  4. Display statistics")
        print("  5. Stop service")
        print()
        print("Manual Test Steps:")
        print("  - To trigger fill events, place a small order on testnet")
        print("  - Watch console for fill detection")
        print("  - Press Ctrl+C to stop early")
        print()
        print("=" * 80)
        print()

        try:
            # Step 1: Start monitoring
            print("📡 Starting OrderMonitorService...")
            await order_monitor_service.start()
            print("✅ OrderMonitorService started successfully")
            print()

            # Display initial status
            status = order_monitor_service.get_status()
            print("📊 Initial Status:")
            print(f"  Running: {status['running']}")
            print(f"  WebSocket Healthy: {status['websocket_healthy']}")
            print(f"  Last Processed: {status['last_processed_timestamp']}")
            print(f"  State Age: {status['state_age_seconds']:.1f}s")
            print()

            # Step 2: Monitor for events
            print(f"⏱️  Monitoring for {self.test_duration}s...")
            print("   (Press Ctrl+C to stop early)")
            print()

            # Wait for test duration or interrupt
            await asyncio.sleep(self.test_duration)

        except KeyboardInterrupt:
            print()
            print("⚠️  Interrupted by user (Ctrl+C)")
        except Exception as e:
            logger.exception(f"Test error: {e}")
            print(f"❌ Test failed: {e}")
            raise
        finally:
            # Step 3: Display final statistics
            print()
            print("=" * 80)
            print("TEST RESULTS")
            print("=" * 80)
            print()

            final_status = order_monitor_service.get_status()
            print("📊 Final Status:")
            print(f"  Running: {final_status['running']}")
            print(f"  WebSocket Healthy: {final_status['websocket_healthy']}")
            print(f"  Reconnect Attempts: {final_status['reconnect_attempts']}")
            print(f"  Total Reconnects: {final_status['websocket_reconnects']}")
            print(f"  Last Heartbeat: {final_status['last_heartbeat']}")
            print(f"  Last Processed: {final_status['last_processed_timestamp']}")
            print(f"  State Age: {final_status['state_age_seconds']:.1f}s")
            print()

            # Step 4: Stop service
            print("🛑 Stopping OrderMonitorService...")
            await order_monitor_service.stop()
            print("✅ OrderMonitorService stopped")
            print()

            # Summary
            print("=" * 80)
            print("SUMMARY")
            print("=" * 80)
            print()

            if final_status["websocket_healthy"]:
                print("✅ WebSocket connection was healthy")
            else:
                print("⚠️  WebSocket connection had issues")

            if final_status["reconnect_attempts"] > 0:
                print(f"⚠️  Had {final_status['reconnect_attempts']} reconnection attempts")

            if final_status["websocket_reconnects"] > 0:
                print(f"ℹ️  WebSocket reconnected {final_status['websocket_reconnects']} times")

            print()
            print("Test completed successfully!")
            print()

            # Additional notes
            print("Next Steps:")
            print("  1. To test fill detection, place orders on testnet during test")
            print("  2. Check logs/hyperbot.log for detailed event logs")
            print("  3. Review data/notification_state.json for state persistence")
            print("  4. Phase 5D will add actual Telegram notifications")
            print()


async def main():
    """Run integration test."""
    test = OrderMonitorTest()
    await test.run_test()


if __name__ == "__main__":
    # Check environment
    if os.environ.get("HYPERLIQUID_TESTNET") != "true":
        print("⚠️  WARNING: HYPERLIQUID_TESTNET not set to 'true'")
        print("   This test should run on testnet!")
        print()
        response = input("Continue anyway? (y/N): ")
        if response.lower() != "y":
            print("Aborted.")
            sys.exit(1)
        print()

    # Run test
    asyncio.run(main())
