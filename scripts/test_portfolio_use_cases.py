#!/usr/bin/env python3
"""
Test Portfolio Use Cases.

Tests all portfolio use cases that the bot uses:
- PositionSummaryUseCase
- RiskAnalysisUseCase
- RebalanceUseCase

This ensures the use cases work correctly end-to-end.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import logger
from src.services import hyperliquid_service
from src.use_cases.portfolio import (
    PositionSummaryRequest,
    PositionSummaryUseCase,
    RebalanceRequest,
    RebalanceUseCase,
    RiskAnalysisRequest,
    RiskAnalysisUseCase,
)


def print_header(text: str):
    """Print test header."""
    logger.info("\n" + "=" * 80)
    logger.info(f"  {text}")
    logger.info("=" * 80)


async def test_position_summary():
    """Test PositionSummaryUseCase."""
    print_header("TEST 1: Position Summary Use Case")

    try:
        use_case = PositionSummaryUseCase()
        request = PositionSummaryRequest()

        logger.info("\nExecuting PositionSummaryUseCase...")
        response = await use_case.execute(request)

        logger.info("\n✓ Success")
        logger.info(f"Total Positions: {response.total_positions}")
        logger.info(f"Total Portfolio Value: ${response.total_position_value:.2f}")
        logger.info(f"Total Unrealized PnL: ${response.total_unrealized_pnl:.2f}")

        if response.positions:
            logger.info(f"\nPositions ({len(response.positions)}):")
            for pos in response.positions[:5]:  # Show first 5
                logger.info(
                    f"  {pos.coin}: ${pos.position_value:.2f} "
                    f"(PnL: ${pos.unrealized_pnl:.2f}, "
                    f"Leverage: {pos.leverage}x)"
                )
            if len(response.positions) > 5:
                logger.info(f"  ... and {len(response.positions) - 5} more")

        return True

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_risk_analysis():
    """Test RiskAnalysisUseCase."""
    print_header("TEST 2: Risk Analysis Use Case")

    try:
        use_case = RiskAnalysisUseCase()
        request = RiskAnalysisRequest()

        logger.info("\nExecuting RiskAnalysisUseCase...")
        response = await use_case.execute(request)

        logger.info("\n✓ Success")
        logger.info(f"Overall Risk Level: {response.overall_risk_level}")
        logger.info(f"Portfolio Health Score: {response.portfolio_health_score}/100")
        logger.info(f"Total Positions: {len(response.positions)}")

        logger.info("\nPositions by Risk Level:")
        logger.info(f"  Critical: {response.critical_positions}")
        logger.info(f"  High: {response.high_risk_positions}")
        logger.info(f"  Moderate: {response.moderate_risk_positions}")
        logger.info(f"  Low: {response.low_risk_positions}")
        logger.info(f"  Safe: {response.safe_positions}")

        if response.portfolio_warnings:
            logger.info(f"\n⚠️  Warnings ({len(response.portfolio_warnings)}):")
            for warning in response.portfolio_warnings[:3]:  # Show first 3
                logger.info(f"  - {warning}")

        if response.positions:
            logger.info(f"\nPosition Risk Details ({len(response.positions)}):")
            for risk in response.positions[:3]:  # Show first 3
                logger.info(
                    f"  {risk.coin}: {risk.risk_level} "
                    f"(Health: {risk.health_score}/100, "
                    f"Liq Distance: {risk.liquidation_distance_pct:.1f}%)"
                )

        return True

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_rebalance_preview():
    """Test RebalanceUseCase preview mode."""
    print_header("TEST 3: Rebalance Use Case (Preview)")

    try:
        use_case = RebalanceUseCase()

        # Get current positions first
        summary_use_case = PositionSummaryUseCase()
        summary = await summary_use_case.execute(PositionSummaryRequest())

        if not summary.positions:
            logger.warning("\n⚠️  No positions to rebalance")
            return True

        # Create equal-weight target allocation
        num_positions = len(summary.positions)
        equal_weight = 100.0 / num_positions
        target_allocations = {pos.coin: equal_weight for pos in summary.positions}

        logger.info(f"\nTarget: Equal weight ({equal_weight:.1f}% per position)")
        logger.info("\nTarget Allocations:")
        for coin, pct in list(target_allocations.items())[:3]:
            logger.info(f"  {coin}: {pct:.1f}%")
        if len(target_allocations) > 3:
            logger.info(f"  ... and {len(target_allocations) - 3} more")

        # Preview rebalance
        request = RebalanceRequest(
            target_weights=target_allocations,
            dry_run=True,  # Preview only
        )

        logger.info("\nExecuting RebalanceUseCase (preview mode)...")
        response = await use_case.execute(request)

        logger.info(f"\n✓ Status: {response.success}")
        logger.info(f"Message: {response.message}")

        if response.warnings:
            logger.info(f"\n⚠️  Warnings ({len(response.warnings)}):")
            for warning in response.warnings[:3]:
                logger.info(f"  - {warning}")

        logger.info(f"\nPlanned Trades: {len(response.planned_trades)}")
        if response.planned_trades:
            logger.info("\nSample Trades:")
            for trade in response.planned_trades[:3]:
                logger.info(
                    f"  {trade.coin}: {trade.action} "
                    f"${abs(trade.trade_usd_value):.2f} "
                    f"({trade.current_allocation_pct:.1f}% → "
                    f"{trade.target_allocation_pct:.1f}%)"
                )
            if len(response.planned_trades) > 3:
                logger.info(f"  ... and {len(response.planned_trades) - 3} more")

        return True

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all portfolio use case tests."""
    print_header("PORTFOLIO USE CASES TEST SUITE")

    logger.info("\nInitializing services...")
    hyperliquid_service.initialize()

    results = []

    # Test 1: Position Summary
    results.append(("PositionSummaryUseCase", await test_position_summary()))

    # Test 2: Risk Analysis
    results.append(("RiskAnalysisUseCase", await test_risk_analysis()))

    # Test 3: Rebalance (Preview)
    results.append(("RebalanceUseCase (Preview)", await test_rebalance_preview()))

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
