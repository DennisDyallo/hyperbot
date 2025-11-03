#!/usr/bin/env python3
"""
Comprehensive test for rebalancing with leverage changes.

Tests the scenario:
- Current: SOL + BTC at 10x leverage (any ratio)
- Target: 50% SOL, 50% BTC at 2x leverage
- Expected: Close all → Set 2x leverage → Open at 50/50

This validates:
1. Leverage mismatch detection
2. Close/reopen logic
3. Leverage setting between close and open
4. Final allocation accuracy
"""

import sys
import requests
import json
from typing import Dict, List

API_BASE = "http://localhost:8000/api"


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_section(text: str):
    """Print a section header."""
    print(f"\n--- {text} ---")


def get_positions() -> List[Dict]:
    """Fetch current positions."""
    response = requests.get(f"{API_BASE}/positions/")
    response.raise_for_status()
    return response.json()


def calculate_allocation(positions: List[Dict]) -> Dict:
    """Calculate allocation percentages."""
    total_value = sum(abs(p["position"]["position_value"]) for p in positions)

    allocation = {}
    for pos in positions:
        coin = pos["position"]["coin"]
        value = abs(pos["position"]["position_value"])
        pct = (value / total_value * 100) if total_value > 0 else 0
        allocation[coin] = {
            "value": value,
            "percentage": pct,
            "leverage": pos["position"]["leverage_value"]
        }

    return {
        "total_value": total_value,
        "coins": allocation
    }


def print_allocation(allocation: Dict, title: str):
    """Print allocation details."""
    print(f"\n{title}:")
    print(f"  Total Portfolio Value: ${allocation['total_value']:.2f}")
    print(f"\n  {'Coin':<8} {'Value ($)':<15} {'Allocation (%)':<15} {'Leverage':<10}")
    print(f"  {'-'*8} {'-'*15} {'-'*15} {'-'*10}")

    for coin, data in allocation["coins"].items():
        print(f"  {coin:<8} ${data['value']:<14.2f} {data['percentage']:<14.1f}% {data['leverage']}x")


def calculate_expected_results(
    current: Dict,
    target_weights: Dict[str, float],
    target_leverage: int
) -> Dict:
    """
    Calculate expected results after rebalancing.

    For leverage changes, the process is:
    1. Close all positions (free up all margin)
    2. Set leverage to 2x for each coin
    3. Reopen positions at target allocations
    """
    total_value = current["total_value"]

    expected = {}
    for coin, target_pct in target_weights.items():
        target_value = (target_pct / 100) * total_value
        expected[coin] = {
            "target_percentage": target_pct,
            "target_value": target_value,
            "target_leverage": target_leverage
        }

    return {
        "total_value": total_value,
        "coins": expected
    }


def preview_rebalance(target_weights: Dict[str, float], leverage: int) -> Dict:
    """Preview rebalancing."""
    response = requests.post(
        f"{API_BASE}/rebalance/preview",
        json={
            "target_weights": target_weights,
            "leverage": leverage,
            "dry_run": True
        }
    )
    response.raise_for_status()
    return response.json()


def execute_rebalance(target_weights: Dict[str, float], leverage: int) -> Dict:
    """Execute rebalancing."""
    response = requests.post(
        f"{API_BASE}/rebalance/execute",
        json={
            "target_weights": target_weights,
            "leverage": leverage,
            "dry_run": False
        }
    )
    response.raise_for_status()
    return response.json()


def print_trades(trades: List[Dict]):
    """Print trade details."""
    print(f"\n  {'Coin':<8} {'Action':<12} {'Current %':<12} {'Target %':<12} {'Trade ($)':<15}")
    print(f"  {'-'*8} {'-'*12} {'-'*12} {'-'*12} {'-'*15}")

    for trade in trades:
        if trade["action"] == "SKIP":
            continue

        action = trade["action"]
        trade_value = trade["trade_usd_value"]
        sign = "+" if trade_value > 0 else ""

        print(
            f"  {trade['coin']:<8} "
            f"{action:<12} "
            f"{trade['current_allocation_pct']:<11.1f}% "
            f"{trade['target_allocation_pct']:<11.1f}% "
            f"{sign}${abs(trade_value):<13.2f}"
        )


def verify_results(initial: Dict, final: Dict, expected: Dict, tolerance_pct: float = 1.0):
    """Verify rebalancing results."""
    print_section("VERIFICATION")

    all_passed = True

    # Check each coin
    for coin in expected["coins"]:
        if coin not in final["coins"]:
            print(f"  ❌ {coin}: Position not found!")
            all_passed = False
            continue

        final_pct = final["coins"][coin]["percentage"]
        expected_pct = expected["coins"][coin]["target_percentage"]
        final_lev = final["coins"][coin]["leverage"]
        expected_lev = expected["coins"][coin]["target_leverage"]

        # Check allocation
        diff = abs(final_pct - expected_pct)
        alloc_ok = diff <= tolerance_pct

        # Check leverage
        lev_ok = final_lev == expected_lev

        status = "✅" if (alloc_ok and lev_ok) else "❌"

        print(f"\n  {status} {coin}:")
        print(f"     Allocation: {final_pct:.1f}% (expected {expected_pct:.1f}%, diff {diff:.1f}%) {'✓' if alloc_ok else '✗'}")
        print(f"     Leverage:   {final_lev}x (expected {expected_lev}x) {'✓' if lev_ok else '✗'}")

        if not alloc_ok or not lev_ok:
            all_passed = False

    # Check total value preservation (allow for fees)
    value_change_pct = abs((final["total_value"] - initial["total_value"]) / initial["total_value"] * 100)
    value_ok = value_change_pct < 5.0  # Allow up to 5% change for fees/slippage

    print(f"\n  {'✅' if value_ok else '❌'} Portfolio Value:")
    print(f"     Initial: ${initial['total_value']:.2f}")
    print(f"     Final:   ${final['total_value']:.2f}")
    print(f"     Change:  {value_change_pct:.2f}% {'✓' if value_ok else '✗ (>5%!)'}")

    if not value_ok:
        all_passed = False

    return all_passed


def main():
    """Main test execution."""
    print_header("LEVERAGE REBALANCE TEST: 10x → 2x with 50/50 Allocation")

    # Configuration
    TARGET_WEIGHTS = {"SOL": 50.0, "BTC": 50.0}
    TARGET_LEVERAGE = 2

    try:
        # Step 1: Get current state
        print_section("STEP 1: Current Portfolio State")
        positions = get_positions()
        current_allocation = calculate_allocation(positions)
        print_allocation(current_allocation, "Current Portfolio")

        # Validate initial state
        print("\n  Validation:")
        for coin, data in current_allocation["coins"].items():
            if data["leverage"] != 10:
                print(f"  ⚠️  {coin} leverage is {data['leverage']}x (expected 10x)")

        # Step 2: Calculate expected results
        print_section("STEP 2: Expected Results")
        expected = calculate_expected_results(current_allocation, TARGET_WEIGHTS, TARGET_LEVERAGE)

        print(f"\n  Target Configuration:")
        print(f"    Leverage: {TARGET_LEVERAGE}x")
        print(f"    Allocation: {TARGET_WEIGHTS}")
        print(f"\n  Expected Process:")
        print(f"    1. Close all positions (10x leverage)")
        print(f"    2. Set leverage to {TARGET_LEVERAGE}x for each coin")
        print(f"    3. Open new positions at target allocations")

        print(f"\n  Expected Results:")
        for coin, data in expected["coins"].items():
            print(f"    {coin}: ${data['target_value']:.2f} ({data['target_percentage']:.0f}%) at {data['target_leverage']}x")

        # Step 3: Preview rebalance
        print_section("STEP 3: Preview Rebalance")
        preview = preview_rebalance(TARGET_WEIGHTS, TARGET_LEVERAGE)

        print(f"\n  Preview Status: {preview['message']}")
        if preview.get("warnings"):
            print(f"\n  ⚠️  Warnings:")
            for warning in preview["warnings"]:
                print(f"    - {warning}")

        print(f"\n  Planned Trades:")
        if preview.get("planned_trades"):
            print_trades(preview["planned_trades"])

        # Step 4: Confirm execution
        print_section("STEP 4: Execute Rebalance")
        response = input("\n  Execute rebalance? (yes/no): ")

        if response.lower() != "yes":
            print("\n  ❌ Aborted by user")
            return

        # Step 5: Execute
        print("\n  Executing rebalance...")
        result = execute_rebalance(TARGET_WEIGHTS, TARGET_LEVERAGE)

        print(f"\n  Execution Status: {result['message']}")
        print(f"  Summary:")
        print(f"    Executed: {result['summary']['executed']}")
        print(f"    Successful: {result['summary']['successful']}")
        print(f"    Failed: {result['summary']['failed']}")
        print(f"    Skipped: {result['summary']['skipped']}")

        if result.get("errors"):
            print(f"\n  ❌ Errors:")
            for error in result["errors"]:
                print(f"    - {error}")

        # Print executed trades
        if result.get("trades"):
            print(f"\n  Executed Trades:")
            print_trades(result["trades"])

        # Step 6: Wait for positions to update
        print_section("STEP 5: Verify Results")
        print("\n  Waiting 3 seconds for positions to update...")
        import time
        time.sleep(3)

        # Step 7: Get final state
        final_positions = get_positions()
        final_allocation = calculate_allocation(final_positions)
        print_allocation(final_allocation, "Final Portfolio")

        # Step 8: Verify
        all_passed = verify_results(current_allocation, final_allocation, expected)

        # Step 9: Summary
        print_header("TEST SUMMARY")

        if all_passed:
            print("\n  ✅ ALL CHECKS PASSED!")
            print("\n  The rebalancing worked correctly:")
            print(f"    - Both positions have {TARGET_LEVERAGE}x leverage")
            print(f"    - Allocation is within 1% of 50/50 target")
            print(f"    - Portfolio value preserved (within 5%)")
            return 0
        else:
            print("\n  ❌ SOME CHECKS FAILED")
            print("\n  Issues detected - see verification section above")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
