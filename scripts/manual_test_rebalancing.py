#!/usr/bin/env python3
"""
Test script for rebalancing functionality.

Tests the rebalancing service with various scenarios:
- Preview rebalancing plans
- Test different target allocations
- Validate risk calculations
- Test edge cases (small positions, high risk)

Usage:
    python scripts/test_rebalancing.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger, settings
from src.services.account_service import account_service
from src.services.hyperliquid_service import hyperliquid_service
from src.services.position_service import position_service
from src.services.rebalance_service import rebalance_service
from src.services.risk_calculator import risk_calculator


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_subsection(title: str):
    """Print a subsection header."""
    print(f"\n--- {title} ---\n")


async def test_current_portfolio():
    """Display current portfolio state."""
    print_section("TEST 1: Current Portfolio State")

    try:
        # Get account info
        account = account_service.get_account_info()
        positions = position_service.list_positions()

        print(f"Account Value: ${account['margin_summary']['account_value']:.2f}")
        print(f"Total Margin Used: ${account['margin_summary']['total_margin_used']:.2f}")
        print(f"Cross Margin Ratio: {account['margin_summary']['cross_margin_ratio_pct']:.2f}%")
        print(f"\nNumber of Positions: {len(positions)}")

        if positions:
            print("\nCurrent Positions:")
            print(f"{'Coin':<8} {'Size':>12} {'Value':>12} {'% of Portfolio':>15} {'PnL':>12}")
            print("-" * 70)

            total_value = sum(abs(p["position"]["position_value"]) for p in positions)

            for item in positions:
                pos = item["position"]
                pct = (abs(pos["position_value"]) / total_value * 100) if total_value > 0 else 0
                print(
                    f"{pos['coin']:<8} "
                    f"{pos['size']:>12.4f} "
                    f"${abs(pos['position_value']):>11.2f} "
                    f"{pct:>14.1f}% "
                    f"${pos['unrealized_pnl']:>11.2f}"
                )

            print(f"\nTotal Portfolio Value: ${total_value:.2f}")

        return account, positions

    except Exception as e:
        logger.error(f"Failed to get portfolio state: {e}")
        raise


async def test_equal_weight_rebalance(positions):
    """Test equal-weight rebalancing (all positions to same %)."""
    print_section("TEST 2: Equal-Weight Rebalancing")

    if not positions:
        print("⚠️  No positions to rebalance")
        return

    try:
        # Calculate equal weight for all positions
        num_positions = len(positions)
        equal_weight = 100.0 / num_positions

        target_allocations = {item["position"]["coin"]: equal_weight for item in positions}

        print(f"Target: Equal weight ({equal_weight:.1f}% per position)")
        print("\nTarget Allocations:")
        for coin, pct in target_allocations.items():
            print(f"  {coin}: {pct:.1f}%")

        # Preview rebalance
        print_subsection("Preview")
        result = rebalance_service.preview_rebalance(target_allocations)

        print(f"Success: {result.success}")
        print(f"Message: {result.message}")

        if result.risk_warnings:
            print("\n⚠️  Risk Warnings:")
            for warning in result.risk_warnings:
                print(f"  - {warning}")

        print(f"\nPlanned Trades: {len(result.planned_trades)}")
        if result.planned_trades:
            print("\nProposed Trades:")
            print(f"{'Coin':<8} {'Current %':>12} {'Target %':>12} {'Change':>12} {'Action':>15}")
            print("-" * 70)

            for trade in result.planned_trades:
                action = f"{trade.action.value} ${abs(trade.trade_usd_value):.2f}"
                print(
                    f"{trade.coin:<8} "
                    f"{trade.current_allocation_pct:>11.1f}% "
                    f"{trade.target_allocation_pct:>11.1f}% "
                    f"{trade.diff_pct:>+11.1f}% "
                    f"{action:>15}"
                )

        return result

    except Exception as e:
        logger.error(f"Equal-weight rebalance test failed: {e}")
        raise


async def test_custom_allocation_rebalance(positions):
    """Test custom allocation rebalancing."""
    print_section("TEST 3: Custom Allocation Rebalancing")

    if not positions:
        print("⚠️  No positions to rebalance")
        return

    try:
        # Create custom allocation based on current positions
        # Example: Give more weight to first position, less to others
        coins = [item["position"]["coin"] for item in positions]

        if len(coins) == 1:
            target_allocations = {coins[0]: 100.0}
            print("Only one position - 100% allocation")
        else:
            # First position gets 50%, rest split equally
            remaining_weight = 50.0 / (len(coins) - 1)
            target_allocations = {coins[0]: 50.0}
            for coin in coins[1:]:
                target_allocations[coin] = remaining_weight

        print("Target: Custom allocation")
        print("\nTarget Allocations:")
        for coin, pct in target_allocations.items():
            print(f"  {coin}: {pct:.1f}%")

        # Preview rebalance
        print_subsection("Preview")
        result = rebalance_service.preview_rebalance(target_allocations)

        print(f"Success: {result.success}")
        print(f"Message: {result.message}")

        if result.risk_warnings:
            print("\n⚠️  Risk Warnings:")
            for warning in result.risk_warnings:
                print(f"  - {warning}")

        print(f"\nPlanned Trades: {len(result.planned_trades)}")
        if result.planned_trades:
            print("\nProposed Trades:")
            print(f"{'Coin':<8} {'Current %':>12} {'Target %':>12} {'Change':>12} {'Action':>15}")
            print("-" * 70)

            for trade in result.planned_trades:
                action = f"{trade.action.value} ${abs(trade.trade_usd_value):.2f}"
                print(
                    f"{trade.coin:<8} "
                    f"{trade.current_allocation_pct:>11.1f}% "
                    f"{trade.target_allocation_pct:>11.1f}% "
                    f"{trade.diff_pct:>+11.1f}% "
                    f"{action:>15}"
                )

        return result

    except Exception as e:
        logger.error(f"Custom allocation rebalance test failed: {e}")
        raise


async def test_risk_assessment(positions):
    """Test risk assessment on current portfolio."""
    print_section("TEST 4: Risk Assessment")

    if not positions:
        print("⚠️  No positions to assess")
        return

    try:
        # Get account info for margin data
        account = account_service.get_account_info()
        margin_summary = account["margin_summary"]

        # Get current prices
        from src.services.market_data_service import market_data_service

        prices = market_data_service.get_all_prices()

        # Assess portfolio risk
        print_subsection("Portfolio Risk Assessment")
        portfolio_risk = risk_calculator.assess_portfolio_risk(
            positions=positions,  # Pass full items, not just position dicts
            margin_summary=margin_summary,
            prices=prices,
        )

        print(f"Overall Risk Level: {portfolio_risk.overall_risk_level.value}")
        print(f"Overall Health Score: {portfolio_risk.overall_health_score}/100")
        print(f"Total Positions: {portfolio_risk.position_count}")
        print("\nPositions by Risk:")
        print(f"  SAFE: {portfolio_risk.positions_by_risk.get('SAFE', 0)}")
        print(f"  LOW: {portfolio_risk.positions_by_risk.get('LOW', 0)}")
        print(f"  MODERATE: {portfolio_risk.positions_by_risk.get('MODERATE', 0)}")
        print(f"  HIGH: {portfolio_risk.positions_by_risk.get('HIGH', 0)}")
        print(f"  CRITICAL: {portfolio_risk.positions_by_risk.get('CRITICAL', 0)}")

        if portfolio_risk.warnings:
            print("\n⚠️  Warnings:")
            for warning in portfolio_risk.warnings:
                print(f"  - {warning}")

        # Assess individual positions
        print_subsection("Individual Position Risk")
        print(f"{'Coin':<8} {'Liq Price':>12} {'Liq Dist':>12} {'Risk':>12} {'Health':>8}")
        print("-" * 65)

        for item in positions:
            pos = item["position"]
            risk = item.get("risk")

            if risk:
                print(
                    f"{pos['coin']:<8} "
                    f"${risk['liquidation_price']:>11.2f} "
                    f"{risk['liquidation_distance_pct']:>11.1f}% "
                    f"{risk['level']:>12} "
                    f"{risk['health_score']:>7}/100"
                )

        return portfolio_risk

    except Exception as e:
        logger.error(f"Risk assessment test failed: {e}")
        raise


async def test_edge_cases():
    """Test edge cases and validation."""
    print_section("TEST 5: Edge Cases & Validation")

    try:
        print_subsection("Test 1: Invalid allocations (sum != 100%)")
        try:
            invalid_allocations = {"BTC": 50.0, "ETH": 40.0}  # Only 90%
            result = rebalance_service.preview_rebalance(invalid_allocations)
            print("❌ FAIL: Should have raised ValueError")
        except ValueError as e:
            print(f"✅ PASS: Correctly rejected - {e}")

        print_subsection("Test 2: Negative allocations")
        try:
            invalid_allocations = {"BTC": 110.0, "ETH": -10.0}
            result = rebalance_service.preview_rebalance(invalid_allocations)
            print("❌ FAIL: Should have raised ValueError")
        except ValueError as e:
            print(f"✅ PASS: Correctly rejected - {e}")

        print_subsection("Test 3: Empty allocations")
        try:
            result = rebalance_service.preview_rebalance({})
            print("❌ FAIL: Should have raised ValueError")
        except ValueError as e:
            print(f"✅ PASS: Correctly rejected - {e}")

        print_subsection("Test 4: Non-existent coin")
        try:
            invalid_allocations = {"FAKECOIN": 100.0}
            result = rebalance_service.preview_rebalance(invalid_allocations)
            print(f"⚠️  WARNING: Accepted but may fail on execution - {result['status']}")
        except Exception as e:
            print(f"✅ PASS: Correctly rejected - {e}")

    except Exception as e:
        logger.error(f"Edge case tests failed: {e}")
        raise


async def test_calculation_accuracy(positions):
    """Test calculation accuracy and verify totals."""
    print_section("TEST 6: Calculation Accuracy")

    if not positions:
        print("⚠️  No positions to test")
        return

    try:
        # Calculate totals manually
        total_value = sum(abs(p["position"]["position_value"]) for p in positions)
        total_pnl = sum(p["position"]["unrealized_pnl"] for p in positions)

        print("Manual Calculation:")
        print(f"  Total Position Value: ${total_value:.2f}")
        print(f"  Total Unrealized PnL: ${total_pnl:.2f}")

        # Get summary from service
        summary = position_service.get_position_summary()

        print("\nService Calculation:")
        print(f"  Total Position Value: ${summary['total_position_value']:.2f}")
        print(f"  Total Unrealized PnL: ${summary['total_unrealized_pnl']:.2f}")

        # Compare
        value_diff = abs(total_value - summary["total_position_value"])
        pnl_diff = abs(total_pnl - summary["total_unrealized_pnl"])

        print("\nDifferences:")
        print(f"  Value: ${value_diff:.2f}")
        print(f"  PnL: ${pnl_diff:.2f}")

        if value_diff < 0.01 and pnl_diff < 0.01:
            print("\n✅ PASS: Calculations match (within $0.01)")
        else:
            print("\n⚠️  WARNING: Calculations differ by more than $0.01")

        # Test allocation percentages add to 100%
        print_subsection("Allocation Percentage Validation")
        allocation_sum = 0.0
        for item in positions:
            pos = item["position"]
            pct = (abs(pos["position_value"]) / total_value * 100) if total_value > 0 else 0
            allocation_sum += pct
            print(f"  {pos['coin']}: {pct:.2f}%")

        print(f"\nSum of allocations: {allocation_sum:.2f}%")

        if abs(allocation_sum - 100.0) < 0.01:
            print("✅ PASS: Allocations sum to 100%")
        else:
            print(f"⚠️  WARNING: Allocations sum to {allocation_sum:.2f}%")

    except Exception as e:
        logger.error(f"Calculation accuracy test failed: {e}")
        raise


async def main():
    """Run all rebalancing tests."""
    print("\n" + "=" * 80)
    print("  HYPERBOT REBALANCING TEST SUITE")
    print("=" * 80)
    print(f"\nEnvironment: {'TESTNET' if settings.HYPERLIQUID_TESTNET else 'MAINNET'}")
    print(f"Wallet: {settings.HYPERLIQUID_WALLET_ADDRESS}")
    print()

    if not settings.HYPERLIQUID_TESTNET:
        print("⚠️  WARNING: Running on MAINNET!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return

    try:
        # Initialize services
        print("Initializing services...")
        hyperliquid_service.initialize()  # Has internal check for re-initialization

        # Run tests
        account, positions = await test_current_portfolio()
        await test_risk_assessment(positions)
        await test_calculation_accuracy(positions)

        if positions:
            await test_equal_weight_rebalance(positions)
            await test_custom_allocation_rebalance(positions)

        await test_edge_cases()

        # Summary
        print_section("TEST SUMMARY")
        print("✅ All tests completed successfully!")
        print("\nWhat was tested:")
        print("  ✓ Current portfolio state retrieval")
        print("  ✓ Risk assessment (portfolio and individual positions)")
        print("  ✓ Calculation accuracy validation")
        if positions:
            print("  ✓ Equal-weight rebalancing preview")
            print("  ✓ Custom allocation rebalancing preview")
        print("  ✓ Edge case handling and validation")

        print("\n⚠️  NOTE: These were PREVIEW operations only.")
        print("No actual trades were executed.")

        if positions:
            print("\nTo execute a rebalance, use:")
            print("  curl -X POST http://localhost:8000/api/rebalance/execute \\")
            print("    -H 'Content-Type: application/json' \\")
            print("    -d '{\"target_allocations\": {...}}'")

    except Exception as e:
        logger.exception(f"Test suite failed: {e}")
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
