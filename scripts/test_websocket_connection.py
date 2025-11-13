"""
Integration test to learn how Hyperliquid WebSocket works.

This script explores the Hyperliquid WebSocket API for real-time order fill notifications.

Goals:
1. Connect to testnet WebSocket
2. Subscribe to userEvents for our wallet address
3. Understand event structure and message format
4. Capture fill events from test orders
5. Document findings for implementation

Run this script, then place orders via Hyperliquid UI or API to see events arrive.

Usage:
    uv run python scripts/test_websocket_connection.py
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from hyperliquid.info import Info
from hyperliquid.utils import constants

# Load environment variables
load_dotenv()

# Configuration
WALLET_ADDRESS = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "")
IS_TESTNET = os.getenv("HYPERLIQUID_TESTNET", "true").lower() == "true"

if not WALLET_ADDRESS:
    raise ValueError("HYPERLIQUID_WALLET_ADDRESS not set in .env")


class WebSocketTester:
    """Test WebSocket connection and event handling."""

    def __init__(self):
        """Initialize WebSocket tester."""
        self.api_url = constants.TESTNET_API_URL if IS_TESTNET else constants.MAINNET_API_URL
        self.info: Info | None = None
        self.events_received = []
        self.fill_events = []

    def event_callback(self, event: dict[str, Any]) -> None:
        """
        Callback for WebSocket events.

        Args:
            event: Event data from WebSocket
        """
        timestamp = datetime.utcnow().isoformat()

        print(f"\n{'=' * 80}")
        print(f"[{timestamp}] EVENT RECEIVED")
        print(f"{'=' * 80}")
        print(json.dumps(event, indent=2))

        # Store event
        self.events_received.append({"timestamp": timestamp, "event": event})

        # Check if this is a fill event
        if self._is_fill_event(event):
            print("\n>>> THIS IS A FILL EVENT! <<<")
            self.fill_events.append(event)
            self._parse_fill_event(event)

    def _is_fill_event(self, event: dict[str, Any]) -> bool:
        """
        Determine if event is a fill event.

        Args:
            event: Event data

        Returns:
            True if fill event, False otherwise
        """
        # This is what we need to learn - event structure
        # Possible keys: "channel", "data", "type", "fills", etc.

        # Common patterns to check:
        if "fills" in event:
            return True
        if "type" in event and "fill" in str(event["type"]).lower():
            return True
        if "data" in event and isinstance(event["data"], dict):
            data = event["data"]
            if "fills" in data or "type" in data and "fill" in str(data["type"]).lower():
                return True

        return False

    def _parse_fill_event(self, event: dict[str, Any]) -> None:
        """
        Parse and display fill event details.

        Args:
            event: Fill event data
        """
        print("\n--- FILL EVENT DETAILS ---")

        # Try to extract common fields
        # This is exploratory - we'll learn the actual structure

        try:
            # Attempt to find fill data
            if "fills" in event:
                fills = event["fills"]
                print(f"Number of fills: {len(fills) if isinstance(fills, list) else 1}")

                if isinstance(fills, list):
                    for i, fill in enumerate(fills):
                        print(f"\nFill #{i + 1}:")
                        self._print_fill_data(fill)
                else:
                    self._print_fill_data(fills)

            elif "data" in event and "fills" in event["data"]:
                fills = event["data"]["fills"]
                print(f"Number of fills: {len(fills) if isinstance(fills, list) else 1}")

                if isinstance(fills, list):
                    for i, fill in enumerate(fills):
                        print(f"\nFill #{i + 1}:")
                        self._print_fill_data(fill)
                else:
                    self._print_fill_data(fills)

            else:
                print("Could not find 'fills' in standard locations")
                print("Full event structure:")
                print(json.dumps(event, indent=2))

        except Exception as e:
            print(f"Error parsing fill event: {e}")

    def _print_fill_data(self, fill: dict[str, Any]) -> None:
        """
        Print fill data fields.

        Args:
            fill: Fill data dictionary
        """
        # Common fields to look for
        fields_to_check = [
            "oid",  # Order ID
            "tid",  # Trade ID
            "coin",  # Coin/symbol
            "side",  # Buy/sell
            "sz",  # Size
            "px",  # Price
            "time",  # Timestamp
            "closedPnl",  # Closed P&L
            "dir",  # Direction
            "crossed",  # Crossed flag
            "fee",  # Fee
            "startPosition",  # Start position
        ]

        for field in fields_to_check:
            if field in fill:
                print(f"  {field}: {fill[field]}")

        # Print any other fields we didn't expect
        other_fields = set(fill.keys()) - set(fields_to_check)
        if other_fields:
            print(f"\n  Other fields: {', '.join(other_fields)}")
            for field in other_fields:
                print(f"    {field}: {fill[field]}")

    async def connect_and_subscribe(self) -> None:
        """Connect to WebSocket and subscribe to user events."""
        try:
            print(f"\n{'=' * 80}")
            print("Connecting to Hyperliquid WebSocket")
            print(f"{'=' * 80}")
            print(f"API URL: {self.api_url}")
            print(f"Wallet: {WALLET_ADDRESS}")
            print(f"Testnet: {IS_TESTNET}")
            print(f"{'=' * 80}\n")

            # Initialize Info with WebSocket enabled
            print("Initializing Info client with WebSocket...")
            self.info = Info(self.api_url, skip_ws=False)

            print("✓ Info client initialized")
            print("\nSubscribing to userEvents...")

            # Subscribe to user events
            subscription = {"type": "userEvents", "user": WALLET_ADDRESS}

            self.info.subscribe(subscription=subscription, callback=self.event_callback)

            print("✓ Subscribed to userEvents")
            print("\n" + "=" * 80)
            print("LISTENING FOR EVENTS...")
            print("=" * 80)
            print("\nPlace an order via Hyperliquid UI or API to see events arrive.")
            print("Press Ctrl+C to stop.\n")

            # Keep the script running
            while True:
                await asyncio.sleep(1)

                # Print stats every 30 seconds
                if len(self.events_received) > 0 and len(self.events_received) % 30 == 0:
                    print(
                        f"\n[Stats] Events received: {len(self.events_received)}, "
                        f"Fill events: {len(self.fill_events)}"
                    )

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")

        except Exception as e:
            print(f"\n\nError: {e}")
            import traceback

            traceback.print_exc()

        finally:
            await self.cleanup()

    async def cleanup(self) -> None:
        """Clean up resources."""
        print("\n" + "=" * 80)
        print("CLEANING UP")
        print("=" * 80)

        if self.info:
            print("Closing WebSocket connection...")
            # Note: Check if Info has a close method
            # self.info.close() or similar

        # Save events to file for analysis
        if self.events_received:
            output_file = "logs/websocket_events.json"
            os.makedirs("logs", exist_ok=True)

            with open(output_file, "w") as f:
                json.dump(
                    {
                        "total_events": len(self.events_received),
                        "fill_events": len(self.fill_events),
                        "events": self.events_received,
                    },
                    f,
                    indent=2,
                )

            print(f"\n✓ Saved {len(self.events_received)} events to {output_file}")

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total events received: {len(self.events_received)}")
        print(f"Fill events detected: {len(self.fill_events)}")

        if self.fill_events:
            print("\nFill events:")
            for i, fill_event in enumerate(self.fill_events, 1):
                print(f"  {i}. {json.dumps(fill_event, indent=6)}")

        print("\nTest complete!")


async def main():
    """Main entry point."""
    tester = WebSocketTester()
    await tester.connect_and_subscribe()


if __name__ == "__main__":
    asyncio.run(main())
