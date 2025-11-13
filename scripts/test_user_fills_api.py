# mypy: disable-error-code="no-any-return"
"""
Integration test to learn how Hyperliquid user_fills() API works.

This script explores the user_fills() API method for querying historical fill data.
This is critical for the recovery mechanism when the bot restarts.

Goals:
1. Query user_fills() with various parameters
2. Understand response format and structure
3. Test filtering by timestamp
4. Compare with WebSocket event structure
5. Document findings for recovery implementation

Usage:
    uv run python scripts/test_user_fills_api.py
"""

import json
import os
from datetime import datetime, timedelta
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


class UserFillsTester:
    """Test user_fills() API method."""

    def __init__(self):
        """Initialize tester."""
        self.api_url = constants.TESTNET_API_URL if IS_TESTNET else constants.MAINNET_API_URL
        self.info = Info(self.api_url, skip_ws=True)  # Don't need WebSocket for this test

    def query_all_recent_fills(self) -> list[dict[str, Any]]:
        """
        Query all recent fills (no time filter).

        Returns:
            List of fill events
        """
        print("\n" + "=" * 80)
        print("TEST 1: Query all recent fills (no time filter)")
        print("=" * 80 + "\n")

        try:
            # Check Info API documentation for user_fills method signature
            # Possible signatures:
            # - user_fills(user_address)
            # - user_fills(user_address, start_time=None)
            # - user_fills(address)

            # Try basic call
            fills = self.info.user_fills(WALLET_ADDRESS)

            print(f"✓ Retrieved {len(fills)} fills")

            if fills:
                print("\nFirst fill structure:")
                print(json.dumps(fills[0], indent=2))

                print("\nLast fill structure:")
                print(json.dumps(fills[-1], indent=2))

            return fills

        except Exception as e:
            print(f"✗ Error querying fills: {e}")
            import traceback

            traceback.print_exc()
            return []

    def query_fills_by_time(self, hours_ago: int = 24) -> list[dict[str, Any]]:
        """
        Query fills since a specific time.

        Args:
            hours_ago: How many hours back to query

        Returns:
            List of fill events
        """
        print("\n" + "=" * 80)
        print(f"TEST 2: Query fills from last {hours_ago} hours")
        print("=" * 80 + "\n")

        try:
            # Calculate timestamp
            start_time = datetime.utcnow() - timedelta(hours=hours_ago)
            start_timestamp = int(start_time.timestamp() * 1000)  # Milliseconds

            print(f"Start time: {start_time.isoformat()}")
            print(f"Start timestamp: {start_timestamp}")

            # Try querying with timestamp
            # Note: Need to check API signature - might be:
            # - user_fills(user, start_time=timestamp)
            # - user_fills(user, startTime=timestamp)
            # - user_fills(user, aggregateByTime=timestamp)

            # Try different parameter names
            try:
                fills = self.info.user_fills(WALLET_ADDRESS, start_time=start_timestamp)
            except TypeError:
                try:
                    fills = self.info.user_fills(WALLET_ADDRESS, startTime=start_timestamp)
                except TypeError:
                    print("⚠ user_fills() may not support time filtering via parameters")
                    print("   We may need to filter results manually")

                    # Get all fills and filter manually
                    all_fills = self.info.user_fills(WALLET_ADDRESS)
                    fills = [
                        fill for fill in all_fills if self._parse_fill_time(fill) >= start_time
                    ]

            print(f"✓ Retrieved {len(fills)} fills since {start_time.isoformat()}")

            if fills:
                print("\nOldest fill:")
                print(json.dumps(fills[-1], indent=2))

                print("\nNewest fill:")
                print(json.dumps(fills[0], indent=2))

            return fills

        except Exception as e:
            print(f"✗ Error querying fills by time: {e}")
            import traceback

            traceback.print_exc()
            return []

    def _parse_fill_time(self, fill: dict[str, Any]) -> datetime:
        """
        Parse timestamp from fill data.

        Args:
            fill: Fill event data

        Returns:
            Datetime object
        """
        # Try to find timestamp field
        # Common possibilities: "time", "timestamp", "t", "closedPnl.time"

        if "time" in fill:
            # Could be milliseconds or ISO string
            time_value = fill["time"]

            if isinstance(time_value, (int, float)):
                # Assume milliseconds
                return datetime.fromtimestamp(time_value / 1000)
            elif isinstance(time_value, str):
                return datetime.fromisoformat(time_value.replace("Z", "+00:00"))

        elif "timestamp" in fill:
            timestamp = fill["timestamp"]
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp / 1000)

        # Default to very old time if can't parse
        return datetime(2000, 1, 1)

    def analyze_fill_structure(self, fills: list[dict[str, Any]]) -> None:
        """
        Analyze fill structure for patterns.

        Args:
            fills: List of fill events
        """
        print("\n" + "=" * 80)
        print("TEST 3: Analyze fill structure")
        print("=" * 80 + "\n")

        if not fills:
            print("No fills to analyze")
            return

        # Collect all unique keys across all fills
        all_keys: set[str] = set()
        for fill in fills:
            all_keys.update(fill.keys())

        print(f"Total unique fields: {len(all_keys)}")
        print("\nAll fields found:")
        for key in sorted(all_keys):
            print(f"  - {key}")

        # Analyze field types
        print("\n" + "-" * 80)
        print("Field type analysis (from first fill):")
        print("-" * 80 + "\n")

        first_fill = fills[0]
        for key in sorted(first_fill.keys()):
            value = first_fill[key]
            value_type = type(value).__name__
            value_preview = str(value)[:50]

            print(f"  {key}:")
            print(f"    Type: {value_type}")
            print(f"    Example: {value_preview}")

        # Check for nested structures
        print("\n" + "-" * 80)
        print("Nested structures:")
        print("-" * 80 + "\n")

        for key, value in first_fill.items():
            if isinstance(value, dict):
                print(f"  {key} (dict): {list(value.keys())}")
            elif isinstance(value, list):
                print(f"  {key} (list): {len(value)} items")
                if value and isinstance(value[0], dict):
                    print(f"    Item structure: {list(value[0].keys())}")

    def extract_essential_fields(self, fills: list[dict[str, Any]]) -> None:
        """
        Extract essential fields for notification purposes.

        Args:
            fills: List of fill events
        """
        print("\n" + "=" * 80)
        print("TEST 4: Extract essential notification fields")
        print("=" * 80 + "\n")

        if not fills:
            print("No fills to extract from")
            return

        print("Attempting to extract essential fields for notifications:\n")

        for i, fill in enumerate(fills[:3], 1):  # Show first 3 fills
            print(f"Fill #{i}:")

            # Essential fields for notifications
            fields_to_extract = {
                "Order ID": ["oid", "orderId", "order_id"],
                "Trade ID": ["tid", "tradeId", "trade_id"],
                "Coin": ["coin", "symbol", "asset"],
                "Side": ["side", "dir", "direction"],
                "Size": ["sz", "size", "qty", "quantity"],
                "Price": ["px", "price"],
                "Time": ["time", "timestamp", "t"],
                "Fee": ["fee", "feeUsed"],
                "P&L": ["closedPnl", "pnl", "realizedPnl"],
            }

            for field_name, possible_keys in fields_to_extract.items():
                found = False
                for key in possible_keys:
                    if key in fill:
                        print(f"  {field_name}: {fill[key]}")
                        found = True
                        break

                if not found:
                    print(f"  {field_name}: NOT FOUND (checked: {', '.join(possible_keys)})")

            print()

    def compare_with_websocket_event(self, fills: list[dict[str, Any]]) -> None:
        """
        Compare user_fills() structure with WebSocket event structure.

        Args:
            fills: List of fills from user_fills()
        """
        print("\n" + "=" * 80)
        print("TEST 5: Compare with WebSocket event structure")
        print("=" * 80 + "\n")

        print("NOTE: Run test_websocket_connection.py first to capture WebSocket events")
        print("      Then compare structures manually\n")

        # Try to load WebSocket events if available
        try:
            with open("logs/websocket_events.json") as f:
                ws_data = json.load(f)
                ws_events = ws_data.get("events", [])

                if ws_events:
                    print(f"Found {len(ws_events)} WebSocket events in logs/websocket_events.json")
                    print("\nWebSocket event structure (first event):")
                    print(json.dumps(ws_events[0], indent=2))

                    if fills:
                        print("\nuser_fills() structure (first fill):")
                        print(json.dumps(fills[0], indent=2))

                        print("\n" + "-" * 80)
                        print("COMPARISON ANALYSIS")
                        print("-" * 80 + "\n")

                        ws_keys = set(ws_events[0]["event"].keys())
                        fill_keys = set(fills[0].keys())

                        print(f"WebSocket event fields: {sorted(ws_keys)}")
                        print(f"user_fills() fields: {sorted(fill_keys)}")

                        common_keys = ws_keys & fill_keys
                        ws_only = ws_keys - fill_keys
                        fill_only = fill_keys - ws_keys

                        print(f"\nCommon fields: {sorted(common_keys)}")
                        print(f"WebSocket only: {sorted(ws_only)}")
                        print(f"user_fills() only: {sorted(fill_only)}")

                else:
                    print("No WebSocket events found in logs")

        except FileNotFoundError:
            print("logs/websocket_events.json not found")
            print("Run test_websocket_connection.py first to capture events")

    def save_results(self, fills: list[dict[str, Any]]) -> None:
        """
        Save results to file for documentation.

        Args:
            fills: List of fills
        """
        output_file = "logs/user_fills_api_results.json"
        os.makedirs("logs", exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(
                {
                    "total_fills": len(fills),
                    "query_time": datetime.utcnow().isoformat(),
                    "fills": fills,
                },
                f,
                indent=2,
            )

        print(f"\n✓ Saved {len(fills)} fills to {output_file}")

    def run_all_tests(self) -> None:
        """Run all tests."""
        print("\n" + "=" * 80)
        print("HYPERLIQUID USER_FILLS() API TESTING")
        print("=" * 80)
        print(f"API URL: {self.api_url}")
        print(f"Wallet: {WALLET_ADDRESS}")
        print(f"Testnet: {IS_TESTNET}")
        print("=" * 80)

        # Test 1: Get all recent fills
        all_fills = self.query_all_recent_fills()

        # Test 2: Query by time (last 24 hours)
        if all_fills:
            self.query_fills_by_time(hours_ago=24)
        else:
            print("\n⚠ Skipping time-based query (no fills found)")

        # Test 3: Analyze structure
        if all_fills:
            self.analyze_fill_structure(all_fills)
        else:
            print("\n⚠ Skipping structure analysis (no fills found)")

        # Test 4: Extract essential fields
        if all_fills:
            self.extract_essential_fields(all_fills)
        else:
            print("\n⚠ Skipping field extraction (no fills found)")

        # Test 5: Compare with WebSocket
        if all_fills:
            self.compare_with_websocket_event(all_fills)
        else:
            print("\n⚠ Skipping WebSocket comparison (no fills found)")

        # Save results
        if all_fills:
            self.save_results(all_fills)

        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        print(f"\nTotal fills retrieved: {len(all_fills)}")

        if all_fills:
            print("\nNext steps:")
            print("1. Review logs/user_fills_api_results.json")
            print("2. Compare with logs/websocket_events.json")
            print("3. Document field mappings in docs/research/")


def main():
    """Main entry point."""
    tester = UserFillsTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
