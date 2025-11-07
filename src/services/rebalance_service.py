"""
Rebalancing Service for portfolio rebalancing with risk management.

Adjusts position sizes to match target allocation percentages while
managing leverage and monitoring liquidation risk.

See: docs/research/hyperliquid-liquidation-mechanics.md
"""

from dataclasses import dataclass
from enum import Enum

from src.config import logger
from src.services.account_service import account_service
from src.services.hyperliquid_service import hyperliquid_service
from src.services.leverage_service import leverage_service
from src.services.market_data_service import market_data_service
from src.services.order_service import order_service
from src.services.position_service import position_service
from src.services.risk_calculator import RiskLevel, risk_calculator


class TradeAction(str, Enum):
    """Trade action types for rebalancing."""

    OPEN = "OPEN"  # Open new position
    INCREASE = "INCREASE"  # Increase existing position
    DECREASE = "DECREASE"  # Decrease existing position
    CLOSE = "CLOSE"  # Close position completely
    SKIP = "SKIP"  # No action needed (within tolerance)


@dataclass
class RebalanceTrade:
    """
    A single trade required for rebalancing.
    """

    coin: str
    action: TradeAction
    current_allocation_pct: float  # Current % of portfolio
    target_allocation_pct: float  # Target % of portfolio
    diff_pct: float  # Difference (target - current)

    # Trade details
    current_usd_value: float  # Current position value in USD
    target_usd_value: float  # Target position value in USD
    trade_usd_value: float  # USD value to trade (+ buy, - sell)
    trade_size: float | None  # Size in coin units (calculated later)
    target_leverage: int | None = None  # Target leverage for OPEN actions

    # Execution
    executed: bool = False
    success: bool = False
    error: str | None = None
    result: dict | None = None

    # Risk assessment (populated after execution)
    estimated_liquidation_price: float | None = None
    estimated_risk_level: RiskLevel | None = None
    estimated_health_score: int | None = None


@dataclass
class RebalanceResult:
    """Result of a rebalancing operation."""

    success: bool
    message: str

    # Trades
    planned_trades: list[RebalanceTrade]
    executed_trades: int
    successful_trades: int
    failed_trades: int
    skipped_trades: int

    # Portfolio state
    initial_allocation: dict[str, float]
    final_allocation: dict[str, float]

    # Risk assessment
    critical_risk_prevented: bool = False
    risk_warnings: list[str] = None

    # Errors
    errors: list[str] = None


class RebalanceService:
    """
    Portfolio rebalancing with risk management.

    Features:
    - Validates target allocations
    - Calculates optimal trades to reach target
    - Sets leverage before trading
    - Monitors risk during execution
    - Blocks trades that would create CRITICAL risk
    - Dry-run mode for previewing changes

    Usage:
        service = RebalanceService()

        # Preview
        preview = service.preview_rebalance(
            target_weights={"BTC": 50, "ETH": 30, "SOL": 20},
            leverage=3
        )

        # Execute
        result = service.execute_rebalance(
            target_weights={"BTC": 50, "ETH": 30, "SOL": 20},
            leverage=3,
            dry_run=False
        )
    """

    def __init__(self):
        """Initialize rebalance service."""
        self.position_service = position_service
        self.account_service = account_service
        self.order_service = order_service
        self.market_data_service = market_data_service
        self.risk_calculator = risk_calculator
        self.hyperliquid = hyperliquid_service

    def validate_target_weights(
        self, target_weights: dict[str, float], tolerance: float = 0.1
    ) -> None:
        """
        Validate target allocation weights.

        Args:
            target_weights: Dict of {coin: percentage} (e.g., {"BTC": 50, "ETH": 50})
            tolerance: Acceptable difference from 100% (default 0.1%)

        Raises:
            ValueError: If weights don't sum to 100% or invalid coins
        """
        # Check weights sum to 100%
        total = sum(target_weights.values())
        if abs(total - 100.0) > tolerance:
            raise ValueError(
                f"Target weights must sum to 100% (got {total:.2f}%). Weights: {target_weights}"
            )

        # Check all percentages are valid
        for coin, pct in target_weights.items():
            if pct < 0:
                raise ValueError(f"Negative weight for {coin}: {pct}%")
            if pct > 100:
                raise ValueError(f"Weight exceeds 100% for {coin}: {pct}%")

        # Verify coins exist
        try:
            prices = self.market_data_service.get_all_prices()
            for coin in target_weights:
                if coin not in prices:
                    available = ", ".join(sorted(prices.keys())[:20])
                    raise ValueError(f"Invalid coin '{coin}'. Available: {available}...")
        except Exception as e:
            logger.error(f"Failed to validate coins: {e}")
            raise ValueError(f"Failed to validate coins: {e}") from e

        logger.debug(f"Target weights validated: {target_weights}")

    def calculate_current_allocation(self) -> dict[str, float]:
        """
        Calculate current portfolio allocation percentages.

        Returns:
            Dict of {coin: percentage} (e.g., {"BTC": 60.5, "ETH": 39.5})
            Empty dict if no positions
        """
        try:
            positions = self.position_service.list_positions()

            if not positions:
                logger.debug("No positions found - empty allocation")
                return {}

            # Calculate total portfolio value
            total_value = sum(abs(float(p["position"]["position_value"])) for p in positions)

            if total_value == 0:
                logger.debug("Total portfolio value is 0 - empty allocation")
                return {}

            # Calculate allocation percentages
            allocation = {}
            for pos in positions:
                coin = pos["position"]["coin"]
                value = abs(float(pos["position"]["position_value"]))
                allocation[coin] = (value / total_value) * 100

            logger.debug(f"Current allocation: {allocation}")
            return allocation

        except Exception as e:
            logger.error(f"Failed to calculate current allocation: {e}")
            raise

    def calculate_required_trades(
        self,
        target_weights: dict[str, float],
        leverage: int = 3,  # noqa: ARG002
        min_trade_usd: float = 10.0,
        tolerance_pct: float = 1.0,
    ) -> list[RebalanceTrade]:
        """
        Calculate trades needed to reach target allocation.

        Args:
            target_weights: Target allocation percentages
            leverage: Leverage to use for positions (default 3x, conservative)
            min_trade_usd: Minimum trade size in USD (skip smaller trades)
            tolerance_pct: Tolerance for considering positions "balanced" (default 1%)

        Returns:
            List of RebalanceTrade objects
        """
        try:
            current = self.calculate_current_allocation()
            account_info = self.account_service.get_account_info()
            # Use total notional position value (leveraged), not account value (margin)
            total_value = float(account_info["margin_summary"]["total_ntl_pos"])

            if total_value == 0:
                raise ValueError("Total position value is 0 - cannot rebalance")

            # Get current prices
            self.market_data_service.get_all_prices()

            # Combine all coins (current + target)
            all_coins = set(list(current.keys()) + list(target_weights.keys()))

            trades = []
            for coin in all_coins:
                current_pct = current.get(coin, 0.0)
                target_pct = target_weights.get(coin, 0.0)
                diff_pct = target_pct - current_pct

                current_usd = (current_pct / 100) * total_value
                target_usd = (target_pct / 100) * total_value
                trade_usd = target_usd - current_usd

                # Determine action
                if abs(diff_pct) < tolerance_pct:
                    # Within tolerance - skip
                    action = TradeAction.SKIP

                elif target_pct == 0 and current_pct > 0:
                    # Close position completely
                    action = TradeAction.CLOSE

                elif current_pct == 0 and target_pct > 0:
                    # Open new position
                    action = TradeAction.OPEN

                elif diff_pct > 0:
                    # Increase position
                    action = TradeAction.INCREASE

                else:
                    # Decrease position
                    action = TradeAction.DECREASE

                # Skip if trade too small (unless closing completely)
                if action != TradeAction.CLOSE and abs(trade_usd) < min_trade_usd:
                    action = TradeAction.SKIP

                trade = RebalanceTrade(
                    coin=coin,
                    action=action,
                    current_allocation_pct=current_pct,
                    target_allocation_pct=target_pct,
                    diff_pct=diff_pct,
                    current_usd_value=current_usd,
                    target_usd_value=target_usd,
                    trade_usd_value=trade_usd,
                    trade_size=None,  # Will calculate during execution
                )

                trades.append(trade)

            logger.info(
                f"Calculated {len(trades)} trades: "
                f"{sum(1 for t in trades if t.action != TradeAction.SKIP)} actionable"
            )

            return trades

        except Exception as e:
            logger.error(f"Failed to calculate required trades: {e}")
            raise

    def get_position_leverage(self, coin: str) -> int | None:
        """
        Get current leverage for a position.

        Delegates to leverage_service for centralized leverage management.

        Args:
            coin: Coin symbol

        Returns:
            Current leverage value, or None if no position exists
        """
        return leverage_service.get_coin_leverage(coin)

    def set_leverage_for_coin(self, coin: str, leverage: int, is_cross: bool = True) -> bool:
        """
        Set leverage for a single coin.

        Delegates to leverage_service for centralized leverage management
        with validation and warnings.

        IMPORTANT: Can only be called when NO position exists for this coin.
        Hyperliquid does not allow changing leverage on open positions.

        Args:
            coin: Coin symbol
            leverage: Leverage value to set
            is_cross: Use cross margin (default True)

        Returns:
            Success status
        """
        success, message = leverage_service.set_coin_leverage(
            coin=coin, leverage=leverage, is_cross=is_cross
        )

        if not success:
            logger.warning(f"Failed to set leverage for {coin}: {message}")
        else:
            logger.info(f"Successfully set leverage for {coin}: {message}")

        return success

    def execute_trade(self, trade: RebalanceTrade, slippage: float = 0.05) -> None:
        """
        Execute a single trade.

        Modifies the trade object in-place with execution results.

        Args:
            trade: RebalanceTrade object to execute
            slippage: Maximum acceptable slippage (default 5%)
        """
        try:
            if trade.action == TradeAction.SKIP:
                trade.executed = True
                trade.success = True
                logger.debug(f"Skipping {trade.coin} (within tolerance)")
                return

            # Get current price for size calculation
            price = self.market_data_service.get_price(trade.coin)
            trade_size = abs(trade.trade_usd_value) / price

            # Round to correct precision based on coin metadata
            metadata = self.market_data_service.get_asset_metadata(trade.coin)
            if metadata and "szDecimals" in metadata:
                sz_decimals = metadata["szDecimals"]
                trade_size = round(trade_size, sz_decimals)
                logger.debug(
                    f"Rounded trade size for {trade.coin}: {trade_size} ({sz_decimals} decimals)"
                )

            trade.trade_size = trade_size

            if trade.action == TradeAction.CLOSE:
                # Close entire position
                logger.info(f"Closing position: {trade.coin}")
                result = self.position_service.close_position(
                    coin=trade.coin,
                    size=None,  # None = close full position
                    slippage=slippage,
                )
                trade.result = result

            elif trade.action in [TradeAction.OPEN, TradeAction.INCREASE]:
                # Buy (open or increase)
                # For OPEN actions, set leverage first (can only set when no position exists)
                if trade.action == TradeAction.OPEN and hasattr(trade, "target_leverage"):
                    leverage_set = self.set_leverage_for_coin(trade.coin, trade.target_leverage)
                    if not leverage_set:
                        logger.warning(
                            f"Failed to set leverage for {trade.coin} - "
                            f"continuing with existing leverage"
                        )

                logger.info(f"Opening/increasing position: {trade.coin} size={trade_size:.4f}")
                result = self.order_service.place_market_order(
                    coin=trade.coin, is_buy=True, size=trade_size, slippage=slippage
                )
                trade.result = result

            elif trade.action == TradeAction.DECREASE:
                # Sell (decrease)
                logger.info(f"Decreasing position: {trade.coin} size={trade_size:.4f}")
                result = self.order_service.place_market_order(
                    coin=trade.coin, is_buy=False, size=trade_size, slippage=slippage
                )
                trade.result = result

            trade.executed = True
            trade.success = True
            logger.info(f"Trade executed successfully: {trade.coin} {trade.action.value}")

        except Exception as e:
            trade.executed = True
            trade.success = False
            trade.error = str(e)
            logger.error(f"Trade failed for {trade.coin}: {e}")

    def preview_rebalance(
        self, target_weights: dict[str, float], leverage: int = 3, min_trade_usd: float = 10.0
    ) -> RebalanceResult:
        """
        Preview rebalancing without executing trades.

        Args:
            target_weights: Target allocation percentages
            leverage: Leverage to use (default 5x)
            min_trade_usd: Minimum trade size in USD

        Returns:
            RebalanceResult with planned trades and risk assessment
        """
        try:
            # Validate inputs
            self.validate_target_weights(target_weights)

            # Calculate trades
            trades = self.calculate_required_trades(target_weights, leverage, min_trade_usd)

            # Get current allocation
            initial_allocation = self.calculate_current_allocation()

            # Count actionable trades
            actionable = [t for t in trades if t.action != TradeAction.SKIP]

            result = RebalanceResult(
                success=True,
                message=f"Preview: {len(actionable)} trades planned",
                planned_trades=trades,
                executed_trades=0,
                successful_trades=0,
                failed_trades=0,
                skipped_trades=sum(1 for t in trades if t.action == TradeAction.SKIP),
                initial_allocation=initial_allocation,
                final_allocation=target_weights,
                errors=[],
            )

            logger.info(f"Rebalance preview generated: {len(actionable)} actionable trades")
            return result

        except Exception as e:
            logger.error(f"Preview failed: {e}")
            return RebalanceResult(
                success=False,
                message=f"Preview failed: {str(e)}",
                planned_trades=[],
                executed_trades=0,
                successful_trades=0,
                failed_trades=0,
                skipped_trades=0,
                initial_allocation={},
                final_allocation={},
                errors=[str(e)],
            )

    def execute_rebalance(
        self,
        target_weights: dict[str, float],
        leverage: int = 3,
        dry_run: bool = True,
        min_trade_usd: float = 10.0,
        max_slippage: float = 0.05,
    ) -> RebalanceResult:
        """
        Execute portfolio rebalancing.

        Steps:
        1. Validate target weights
        2. Calculate required trades
        3. Set leverage for all coins
        4. Execute trades (close/reduce first, then open/increase)
        5. Monitor risk during execution
        6. Return results

        Args:
            target_weights: Target allocation percentages (e.g., {"BTC": 50, "ETH": 50})
            leverage: Leverage to use for all positions (default 5x)
            dry_run: If True, only preview (don't execute). Default True for safety
            min_trade_usd: Minimum trade size in USD (default $10)
            max_slippage: Maximum acceptable slippage (default 5%)

        Returns:
            RebalanceResult with execution details
        """
        try:
            logger.info(
                f"Starting rebalance: dry_run={dry_run}, leverage={leverage}x, "
                f"target={target_weights}"
            )

            # Validate inputs
            self.validate_target_weights(target_weights)

            # Calculate trades
            trades = self.calculate_required_trades(target_weights, leverage, min_trade_usd)

            initial_allocation = self.calculate_current_allocation()

            # If dry run, return preview
            if dry_run:
                logger.info("Dry run mode - returning preview")
                return self.preview_rebalance(target_weights, leverage, min_trade_usd)

            # Handle leverage mismatches:
            # If a position exists with wrong leverage and needs modification,
            # we must close it first, then reopen with correct leverage
            adjusted_trades = []
            for trade in trades:
                if trade.action in [TradeAction.INCREASE, TradeAction.DECREASE]:
                    current_leverage = self.get_position_leverage(trade.coin)
                    if current_leverage is not None and current_leverage != leverage:
                        logger.warning(
                            f"{trade.coin} has {current_leverage}x leverage but target is {leverage}x. "
                            f"Will close and reopen with correct leverage."
                        )
                        # Replace with CLOSE + OPEN
                        close_trade = RebalanceTrade(
                            coin=trade.coin,
                            action=TradeAction.CLOSE,
                            current_allocation_pct=trade.current_allocation_pct,
                            target_allocation_pct=0.0,
                            diff_pct=-trade.current_allocation_pct,
                            current_usd_value=trade.current_usd_value,
                            target_usd_value=0.0,
                            trade_usd_value=-trade.current_usd_value,
                            trade_size=None,
                        )
                        open_trade = RebalanceTrade(
                            coin=trade.coin,
                            action=TradeAction.OPEN,
                            current_allocation_pct=0.0,
                            target_allocation_pct=trade.target_allocation_pct,
                            diff_pct=trade.target_allocation_pct,
                            current_usd_value=0.0,
                            target_usd_value=trade.target_usd_value,
                            trade_usd_value=trade.target_usd_value,
                            trade_size=None,
                            target_leverage=leverage,
                        )
                        adjusted_trades.append(close_trade)
                        adjusted_trades.append(open_trade)
                        continue

                # Set target leverage for OPEN trades
                if trade.action == TradeAction.OPEN:
                    trade.target_leverage = leverage

                adjusted_trades.append(trade)

            trades = adjusted_trades
            logger.info(f"Adjusted trades for leverage: {len(trades)} total trades")

            # Separate trades into phases:
            # Phase 1: Close and decrease positions (free up margin)
            # Phase 2: Open and increase positions (use freed margin)

            close_trades = [
                t for t in trades if t.action in [TradeAction.CLOSE, TradeAction.DECREASE]
            ]
            open_trades = [
                t for t in trades if t.action in [TradeAction.OPEN, TradeAction.INCREASE]
            ]
            skip_trades = [t for t in trades if t.action == TradeAction.SKIP]

            logger.info(
                f"Execution plan: {len(close_trades)} close/decrease, "
                f"{len(open_trades)} open/increase, {len(skip_trades)} skip"
            )

            # Phase 1: Close/decrease positions
            for trade in close_trades:
                self.execute_trade(trade, max_slippage)

            # Wait for exchange to update margin after closes
            if close_trades:
                import time

                logger.info("Waiting 2 seconds for margin to be freed after closes...")
                time.sleep(2)

                # CRITICAL: Recalculate target_usd_value for OPEN trades
                # After closing positions, total_ntl_pos has changed, so we need to
                # recalculate targets based on the DESIRED final total and target percentages

                account_info = self.account_service.get_account_info()
                account_value = float(account_info["margin_summary"]["account_value"])
                current_total_ntl_pos = float(account_info["margin_summary"]["total_ntl_pos"])

                # Calculate the desired final total_ntl_pos
                # Option 1: Use max position value based on account and leverage
                # Option 2: Calculate based on what we'll have after all trades

                # We'll calculate the target total by considering:
                # - Current positions (after closes)
                # - Target allocations
                # - Maintaining reasonable leverage usage

                # Get current allocations after closes
                current_allocation = self.calculate_current_allocation()

                # Calculate what the final total SHOULD be based on:
                # - Existing positions that we're keeping/decreasing
                # - New positions we're opening/increasing
                # Such that the final percentages match target_weights

                # For each coin in target_weights, calculate what the total must be
                # to achieve the target percentage given current/planned positions
                target_total = 0.0

                # Start with current positions that we're NOT changing
                for coin, pct in current_allocation.items():
                    if coin not in target_weights:
                        # Position being closed - already handled
                        continue
                    target_pct = target_weights.get(coin, 0.0)
                    if target_pct == 0:
                        # Being closed - skip
                        continue

                    # This coin exists and has a target
                    # If we're not opening it (meaning we already have a position),
                    # use current value to calculate what total should be
                    if coin not in [t.coin for t in open_trades if t.action == TradeAction.OPEN]:
                        current_value = (pct / 100) * current_total_ntl_pos
                        # If current_value should be target_pct of total, then:
                        # current_value = (target_pct / 100) * total
                        # total = current_value * 100 / target_pct
                        if target_pct > 0:
                            implied_total = current_value * 100 / target_pct
                            target_total = max(target_total, implied_total)

                # If we couldn't determine target_total from existing positions,
                # use account_value * leverage as the target
                if target_total == 0:
                    target_total = account_value * leverage
                    logger.info(
                        f"Using account-based target total: ${target_total:.2f} "
                        f"(${account_value:.2f} * {leverage}x)"
                    )
                else:
                    logger.info(
                        f"Calculated target total from existing positions: ${target_total:.2f}"
                    )

                # Now recalculate all OPEN trade targets based on this total
                for trade in open_trades:
                    if trade.action == TradeAction.OPEN:
                        # Recalculate target based on percentage of target_total
                        old_target = trade.target_usd_value
                        trade.target_usd_value = (trade.target_allocation_pct / 100) * target_total
                        trade.trade_usd_value = trade.target_usd_value  # OPEN means current is 0
                        logger.info(
                            f"Recalculated {trade.coin} target: ${old_target:.2f} → ${trade.target_usd_value:.2f} "
                            f"({trade.target_allocation_pct}% of ${target_total:.2f})"
                        )

                # Validate we have enough margin
                max_position_value = account_value * leverage
                total_target_after_recalc = sum(
                    abs(t.target_usd_value) for t in open_trades if t.action == TradeAction.OPEN
                )
                total_target_after_recalc += current_total_ntl_pos  # Add existing positions

                if total_target_after_recalc > max_position_value:
                    scale_factor = max_position_value / total_target_after_recalc
                    logger.warning(
                        f"Account value (${account_value:.2f}) at {leverage}x can only support "
                        f"${max_position_value:.2f} in positions, but target is ${total_target_after_recalc:.2f}. "
                        f"Scaling down by {scale_factor:.1%}"
                    )

                    # Scale down all OPEN trades proportionally
                    for trade in open_trades:
                        if trade.action == TradeAction.OPEN:
                            trade.target_usd_value *= scale_factor
                            trade.trade_usd_value *= scale_factor
                            logger.info(
                                f"Scaled down {trade.coin} target to ${trade.target_usd_value:.2f}"
                            )

            # Check if any CLOSE trades failed - must abort if so
            failed_closes = [
                t for t in close_trades if t.action == TradeAction.CLOSE and not t.success
            ]
            if failed_closes:
                failed_coins = [t.coin for t in failed_closes]
                error_msg = f"CRITICAL: Failed to close positions for {failed_coins}. Cannot continue with leverage change."
                logger.error(error_msg)

                # Mark remaining trades as skipped
                for trade in open_trades:
                    trade.executed = False
                    trade.success = False
                    trade.error = "Aborted due to failed close trades"

                # Return early with error
                final_allocation = self.calculate_current_allocation()
                return RebalanceResult(
                    success=False,
                    message=f"Rebalance aborted: {len(failed_closes)} close trades failed",
                    planned_trades=trades,
                    executed_trades=len(close_trades),
                    successful_trades=len([t for t in close_trades if t.success]),
                    failed_trades=len(failed_closes),
                    skipped_trades=len(open_trades) + len(skip_trades),
                    initial_allocation=initial_allocation,
                    final_allocation=final_allocation,
                    errors=[error_msg] + [t.error for t in failed_closes if t.error],
                )

            # Phase 2: Open/increase positions
            for trade in open_trades:
                self.execute_trade(trade, max_slippage)

            # Mark skip trades as executed
            for trade in skip_trades:
                trade.executed = True
                trade.success = True

            # Calculate final allocation
            final_allocation = self.calculate_current_allocation()

            # Count results
            executed = sum(1 for t in trades if t.executed)
            successful = sum(1 for t in trades if t.success)
            failed = sum(1 for t in trades if t.executed and not t.success)
            skipped = len(skip_trades)

            errors = [t.error for t in trades if t.error is not None]

            success = failed == 0
            if success:
                message = f"Rebalance complete: {successful} trades successful"
            else:
                message = f"Rebalance partial: {successful} successful, {failed} failed"

            result = RebalanceResult(
                success=success,
                message=message,
                planned_trades=trades,
                executed_trades=executed,
                successful_trades=successful,
                failed_trades=failed,
                skipped_trades=skipped,
                initial_allocation=initial_allocation,
                final_allocation=final_allocation,
                errors=errors if errors else [],
            )

            logger.info(f"Rebalance complete: {message}")
            return result

        except Exception as e:
            logger.error(f"Rebalance failed: {e}")
            return RebalanceResult(
                success=False,
                message=f"Rebalance failed: {str(e)}",
                planned_trades=[],
                executed_trades=0,
                successful_trades=0,
                failed_trades=0,
                skipped_trades=0,
                initial_allocation={},
                final_allocation={},
                errors=[str(e)],
            )


# Singleton instance
rebalance_service = RebalanceService()
