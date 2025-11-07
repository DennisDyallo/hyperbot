"""
Unit tests for RebalanceUseCase.

Tests portfolio rebalancing logic (wrapper around rebalance_service).
CRITICAL - bugs here = incorrect rebalancing operations.

MIGRATED: Now using tests/helpers for service mocking.
- create_service_with_mocks replaces manual fixture boilerplate
- ServiceMockBuilder provides pre-configured rebalance_service mock
"""

from unittest.mock import Mock

import pytest

from src.services.rebalance_service import TradeAction
from src.services.risk_calculator import RiskLevel
from src.use_cases.portfolio.rebalance import (
    RebalanceRequest,
    RebalanceUseCase,
)

# Import helpers for cleaner service mocking
from tests.helpers import ServiceMockBuilder, create_service_with_mocks


class TestRebalanceUseCase:
    """Test RebalanceUseCase."""

    @pytest.fixture
    def use_case(self):
        """Create RebalanceUseCase with mocked dependencies."""
        return create_service_with_mocks(
            RebalanceUseCase,
            "src.use_cases.portfolio.rebalance",
            {"rebalance_service": ServiceMockBuilder.rebalance_service()},
        )

    @pytest.fixture
    def mock_rebalance_service(self, use_case):
        """Get the mocked rebalance_service from use_case."""
        return use_case.rebalance_service

    @pytest.fixture
    def sample_preview_result(self):
        """Sample preview result from rebalance service."""
        return Mock(
            success=True,
            message="Rebalance preview calculated successfully",
            initial_allocation={"BTC": 40.0, "ETH": 35.0, "SOL": 25.0},
            final_allocation={"BTC": 50.0, "ETH": 30.0, "SOL": 20.0},
            planned_trades=[
                Mock(
                    coin="BTC",
                    action=TradeAction.INCREASE,
                    current_allocation_pct=40.0,
                    target_allocation_pct=50.0,
                    diff_pct=10.0,
                    current_usd_value=40000.0,
                    target_usd_value=50000.0,
                    trade_usd_value=10000.0,
                    trade_size=0.2,
                    executed=False,
                    success=False,
                    error=None,
                    estimated_liquidation_price=40000.0,
                    estimated_risk_level=RiskLevel.LOW,
                    estimated_health_score=75,
                ),
                Mock(
                    coin="ETH",
                    action=TradeAction.DECREASE,
                    current_allocation_pct=35.0,
                    target_allocation_pct=30.0,
                    diff_pct=-5.0,
                    current_usd_value=35000.0,
                    target_usd_value=30000.0,
                    trade_usd_value=-5000.0,
                    trade_size=-1.67,
                    executed=False,
                    success=False,
                    error=None,
                    estimated_liquidation_price=2500.0,
                    estimated_risk_level=RiskLevel.SAFE,
                    estimated_health_score=85,
                ),
                Mock(
                    coin="SOL",
                    action=TradeAction.SKIP,
                    current_allocation_pct=25.0,
                    target_allocation_pct=20.0,
                    diff_pct=-5.0,
                    current_usd_value=25000.0,
                    target_usd_value=20000.0,
                    trade_usd_value=-5000.0,
                    trade_size=None,
                    executed=False,
                    success=False,
                    error="Trade too small",
                    estimated_liquidation_price=None,
                    estimated_risk_level=None,
                    estimated_health_score=None,
                ),
            ],
            executed_trades=0,
            successful_trades=0,
            failed_trades=0,
            skipped_trades=1,
            critical_risk_prevented=False,
            risk_warnings=["Leverage set to 3x for all positions"],
            errors=[],
        )

    # ===================================================================
    # Preview Mode tests (dry_run=True)
    # ===================================================================

    @pytest.mark.asyncio
    async def test_preview_rebalance_success(
        self, use_case, mock_rebalance_service, sample_preview_result
    ):
        """Test preview mode calls preview_rebalance()."""
        mock_rebalance_service.preview_rebalance.return_value = sample_preview_result

        request = RebalanceRequest(
            target_weights={"BTC": 50.0, "ETH": 30.0, "SOL": 20.0},
            leverage=3,
            dry_run=True,
            min_trade_usd=10.0,
        )

        response = await use_case.execute(request)

        # Verify correct method called
        mock_rebalance_service.preview_rebalance.assert_called_once_with(
            target_weights={"BTC": 50.0, "ETH": 30.0, "SOL": 20.0},
            leverage=3,
            min_trade_usd=10.0,
        )

        # Verify response
        assert response.success is True
        assert response.dry_run is True
        assert response.total_trades == 3
        assert response.actionable_trades == 2  # BTC and ETH (not SOL)
        assert response.executed_trades == 0
        assert response.successful_trades == 0
        assert response.skipped_trades == 1
        assert response.total_usd_volume == 15000.0  # 10000 + 5000

    @pytest.mark.asyncio
    async def test_preview_includes_risk_warnings(
        self, use_case, mock_rebalance_service, sample_preview_result
    ):
        """Test preview includes risk warnings."""
        mock_rebalance_service.preview_rebalance.return_value = sample_preview_result

        request = RebalanceRequest(target_weights={"BTC": 50.0, "ETH": 50.0}, dry_run=True)

        response = await use_case.execute(request)

        assert len(response.warnings) > 0
        assert "Leverage set to 3x" in response.warnings[0]

    @pytest.mark.asyncio
    async def test_preview_high_risk_coins_identified(self, use_case, mock_rebalance_service):
        """Test high-risk coins are identified in preview."""
        # Mock result with high-risk trade
        high_risk_result = Mock(
            success=True,
            message="Preview calculated",
            initial_allocation={"BTC": 50.0, "ETH": 50.0},
            final_allocation={"BTC": 60.0, "ETH": 40.0},
            planned_trades=[
                Mock(
                    coin="BTC",
                    action=TradeAction.INCREASE,
                    current_allocation_pct=50.0,
                    target_allocation_pct=60.0,
                    diff_pct=10.0,
                    current_usd_value=50000.0,
                    target_usd_value=60000.0,
                    trade_usd_value=10000.0,
                    trade_size=0.2,
                    executed=False,
                    success=False,
                    error=None,
                    estimated_liquidation_price=45000.0,
                    estimated_risk_level=RiskLevel.HIGH,
                    estimated_health_score=40,
                )
            ],
            executed_trades=0,
            successful_trades=0,
            failed_trades=0,
            skipped_trades=0,
            critical_risk_prevented=False,
            risk_warnings=["BTC position would be HIGH risk"],
            errors=[],
        )
        mock_rebalance_service.preview_rebalance.return_value = high_risk_result

        request = RebalanceRequest(target_weights={"BTC": 60.0, "ETH": 40.0}, dry_run=True)

        response = await use_case.execute(request)

        assert "BTC" in response.high_risk_coins
        assert response.high_risk_coins == ["BTC"]

    # ===================================================================
    # Execution Mode tests (dry_run=False)
    # ===================================================================

    @pytest.mark.asyncio
    async def test_execute_rebalance_success(self, use_case, mock_rebalance_service):
        """Test execution mode calls execute_rebalance()."""
        # Mock execution result
        execution_result = Mock(
            success=True,
            message="Rebalance executed successfully",
            initial_allocation={"BTC": 40.0, "ETH": 60.0},
            final_allocation={"BTC": 50.0, "ETH": 50.0},
            planned_trades=[
                Mock(
                    coin="BTC",
                    action=TradeAction.INCREASE,
                    current_allocation_pct=40.0,
                    target_allocation_pct=50.0,
                    diff_pct=10.0,
                    current_usd_value=40000.0,
                    target_usd_value=50000.0,
                    trade_usd_value=10000.0,
                    trade_size=0.2,
                    executed=True,
                    success=True,
                    error=None,
                    estimated_liquidation_price=40000.0,
                    estimated_risk_level=RiskLevel.LOW,
                    estimated_health_score=75,
                ),
                Mock(
                    coin="ETH",
                    action=TradeAction.DECREASE,
                    current_allocation_pct=60.0,
                    target_allocation_pct=50.0,
                    diff_pct=-10.0,
                    current_usd_value=60000.0,
                    target_usd_value=50000.0,
                    trade_usd_value=-10000.0,
                    trade_size=-3.33,
                    executed=True,
                    success=True,
                    error=None,
                    estimated_liquidation_price=2500.0,
                    estimated_risk_level=RiskLevel.SAFE,
                    estimated_health_score=85,
                ),
            ],
            executed_trades=2,
            successful_trades=2,
            failed_trades=0,
            skipped_trades=0,
            critical_risk_prevented=False,
            risk_warnings=[],
            errors=[],
        )
        mock_rebalance_service.execute_rebalance.return_value = execution_result

        request = RebalanceRequest(
            target_weights={"BTC": 50.0, "ETH": 50.0},
            leverage=3,
            dry_run=False,
            min_trade_usd=10.0,
            max_slippage=0.05,
        )

        response = await use_case.execute(request)

        # Verify correct method called
        mock_rebalance_service.execute_rebalance.assert_called_once_with(
            target_weights={"BTC": 50.0, "ETH": 50.0},
            leverage=3,
            dry_run=False,
            min_trade_usd=10.0,
            max_slippage=0.05,
        )

        # Verify response
        assert response.success is True
        assert response.dry_run is False
        assert response.executed_trades == 2
        assert response.successful_trades == 2
        assert response.failed_trades == 0

    @pytest.mark.asyncio
    async def test_execute_with_failures(self, use_case, mock_rebalance_service):
        """Test execution with some trade failures."""
        # Mock result with 1 success, 1 failure
        result_with_failures = Mock(
            success=False,
            message="Rebalance partially failed",
            initial_allocation={"BTC": 40.0, "ETH": 60.0},
            final_allocation={"BTC": 45.0, "ETH": 55.0},
            planned_trades=[
                Mock(
                    coin="BTC",
                    action=TradeAction.INCREASE,
                    current_allocation_pct=40.0,
                    target_allocation_pct=50.0,
                    diff_pct=10.0,
                    current_usd_value=40000.0,
                    target_usd_value=50000.0,
                    trade_usd_value=10000.0,
                    trade_size=0.2,
                    executed=True,
                    success=True,
                    error=None,
                    estimated_liquidation_price=40000.0,
                    estimated_risk_level=RiskLevel.LOW,
                    estimated_health_score=75,
                ),
                Mock(
                    coin="ETH",
                    action=TradeAction.DECREASE,
                    current_allocation_pct=60.0,
                    target_allocation_pct=50.0,
                    diff_pct=-10.0,
                    current_usd_value=60000.0,
                    target_usd_value=50000.0,
                    trade_usd_value=-10000.0,
                    trade_size=-3.33,
                    executed=True,
                    success=False,
                    error="Insufficient liquidity",
                    estimated_liquidation_price=None,
                    estimated_risk_level=None,
                    estimated_health_score=None,
                ),
            ],
            executed_trades=2,
            successful_trades=1,
            failed_trades=1,
            skipped_trades=0,
            critical_risk_prevented=False,
            risk_warnings=[],
            errors=["ETH trade failed: Insufficient liquidity"],
        )
        mock_rebalance_service.execute_rebalance.return_value = result_with_failures

        request = RebalanceRequest(target_weights={"BTC": 50.0, "ETH": 50.0}, dry_run=False)

        response = await use_case.execute(request)

        assert response.success is False
        assert response.successful_trades == 1
        assert response.failed_trades == 1
        assert len(response.errors) == 1
        assert "Insufficient liquidity" in response.errors[0]

    # ===================================================================
    # Trade Detail Conversion tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_trade_detail_fields_complete(self, use_case, mock_rebalance_service):
        """Test trade detail includes all fields."""
        result = Mock(
            success=True,
            message="Success",
            initial_allocation={"BTC": 100.0},
            final_allocation={"BTC": 100.0},
            planned_trades=[
                Mock(
                    coin="BTC",
                    action=TradeAction.OPEN,
                    current_allocation_pct=0.0,
                    target_allocation_pct=100.0,
                    diff_pct=100.0,
                    current_usd_value=0.0,
                    target_usd_value=100000.0,
                    trade_usd_value=100000.0,
                    trade_size=2.0,
                    executed=True,
                    success=True,
                    error=None,
                    estimated_liquidation_price=40000.0,
                    estimated_risk_level=RiskLevel.MODERATE,
                    estimated_health_score=65,
                )
            ],
            executed_trades=1,
            successful_trades=1,
            failed_trades=0,
            skipped_trades=0,
            critical_risk_prevented=False,
            risk_warnings=[],
            errors=[],
        )
        mock_rebalance_service.execute_rebalance.return_value = result

        request = RebalanceRequest(target_weights={"BTC": 100.0}, dry_run=False)

        response = await use_case.execute(request)

        trade = response.planned_trades[0]
        assert trade.coin == "BTC"
        assert trade.action == "OPEN"
        assert trade.current_allocation_pct == 0.0
        assert trade.target_allocation_pct == 100.0
        assert trade.diff_pct == 100.0
        assert trade.current_usd_value == 0.0
        assert trade.target_usd_value == 100000.0
        assert trade.trade_usd_value == 100000.0
        assert trade.trade_size == 2.0
        assert trade.executed is True
        assert trade.success is True
        assert trade.error is None
        assert trade.estimated_liquidation_price == 40000.0
        assert trade.estimated_risk_level == "MODERATE"
        assert trade.estimated_health_score == 65

    @pytest.mark.asyncio
    async def test_trade_detail_rounding(self, use_case, mock_rebalance_service):
        """Test trade detail values are properly rounded."""
        result = Mock(
            success=True,
            message="Success",
            initial_allocation={"BTC": 100.0},
            final_allocation={"BTC": 100.0},
            planned_trades=[
                Mock(
                    coin="BTC",
                    action=TradeAction.INCREASE,
                    current_allocation_pct=33.333333,
                    target_allocation_pct=50.555555,
                    diff_pct=17.222222,
                    current_usd_value=33333.333333,
                    target_usd_value=50555.555555,
                    trade_usd_value=17222.222222,
                    trade_size=0.344444444,
                    executed=False,
                    success=False,
                    error=None,
                    estimated_liquidation_price=None,
                    estimated_risk_level=None,
                    estimated_health_score=None,
                )
            ],
            executed_trades=0,
            successful_trades=0,
            failed_trades=0,
            skipped_trades=0,
            critical_risk_prevented=False,
            risk_warnings=[],
            errors=[],
        )
        mock_rebalance_service.preview_rebalance.return_value = result

        request = RebalanceRequest(target_weights={"BTC": 100.0}, dry_run=True)

        response = await use_case.execute(request)

        trade = response.planned_trades[0]
        # Percentages rounded to 2 decimals
        assert trade.current_allocation_pct == 33.33
        assert trade.target_allocation_pct == 50.56
        assert trade.diff_pct == 17.22
        # USD values rounded to 2 decimals
        assert trade.current_usd_value == 33333.33
        assert trade.target_usd_value == 50555.56
        assert trade.trade_usd_value == 17222.22
        # Trade size rounded to 6 decimals
        assert trade.trade_size == 0.344444

    # ===================================================================
    # Trade Counting tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_actionable_trade_counting(
        self, use_case, mock_rebalance_service, sample_preview_result
    ):
        """Test actionable trades are counted correctly (excludes SKIP)."""
        mock_rebalance_service.preview_rebalance.return_value = sample_preview_result

        request = RebalanceRequest(
            target_weights={"BTC": 50.0, "ETH": 30.0, "SOL": 20.0}, dry_run=True
        )

        response = await use_case.execute(request)

        # 3 total trades, but SOL is SKIP
        assert response.total_trades == 3
        assert response.actionable_trades == 2
        assert response.skipped_trades == 1

    @pytest.mark.asyncio
    async def test_total_usd_volume_calculation(
        self, use_case, mock_rebalance_service, sample_preview_result
    ):
        """Test total USD volume is sum of absolute trade values."""
        mock_rebalance_service.preview_rebalance.return_value = sample_preview_result

        request = RebalanceRequest(
            target_weights={"BTC": 50.0, "ETH": 30.0, "SOL": 20.0}, dry_run=True
        )

        response = await use_case.execute(request)

        # BTC: 10000, ETH: 5000, SOL: skipped = 15000 total
        assert response.total_usd_volume == 15000.0

    # ===================================================================
    # Risk Assessment tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_critical_risk_prevented_flag(self, use_case, mock_rebalance_service):
        """Test critical_risk_prevented flag is passed through."""
        result = Mock(
            success=False,
            message="Rebalance blocked due to critical risk",
            initial_allocation={"BTC": 50.0, "ETH": 50.0},
            final_allocation={"BTC": 50.0, "ETH": 50.0},
            planned_trades=[
                Mock(
                    coin="BTC",
                    action=TradeAction.SKIP,
                    current_allocation_pct=50.0,
                    target_allocation_pct=100.0,
                    diff_pct=50.0,
                    current_usd_value=50000.0,
                    target_usd_value=100000.0,
                    trade_usd_value=50000.0,
                    trade_size=None,
                    executed=False,
                    success=False,
                    error="CRITICAL risk detected",
                    estimated_liquidation_price=None,
                    estimated_risk_level=RiskLevel.CRITICAL,
                    estimated_health_score=5,
                )
            ],
            executed_trades=0,
            successful_trades=0,
            failed_trades=0,
            skipped_trades=1,
            critical_risk_prevented=True,
            risk_warnings=["BTC position would be CRITICAL risk"],
            errors=["Rebalance blocked to prevent critical risk"],
        )
        mock_rebalance_service.preview_rebalance.return_value = result

        request = RebalanceRequest(target_weights={"BTC": 100.0}, dry_run=True)

        response = await use_case.execute(request)

        assert response.critical_risk_prevented is True
        assert "BTC" in response.high_risk_coins

    # ===================================================================
    # Validation Error tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_invalid_weights_raises_value_error(self, use_case, mock_rebalance_service):
        """Test invalid weights raise ValueError."""
        result = Mock(
            success=False,
            message="Weights must sum to 100%",
            initial_allocation={},
            final_allocation={},
            planned_trades=[],
            executed_trades=0,
            successful_trades=0,
            failed_trades=0,
            skipped_trades=0,
            critical_risk_prevented=False,
            risk_warnings=[],
            errors=["Weights must sum to 100% (got 80%)"],
        )
        mock_rebalance_service.preview_rebalance.return_value = result

        request = RebalanceRequest(
            target_weights={"BTC": 50.0, "ETH": 30.0},  # Only 80%
            dry_run=True,
        )

        with pytest.raises(ValueError, match="Weights must sum to 100%"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_negative_weight_raises_value_error(self, use_case, mock_rebalance_service):
        """Test negative weight raises ValueError."""
        result = Mock(
            success=False,
            message="Weights cannot be negative",
            initial_allocation={},
            final_allocation={},
            planned_trades=[],
            executed_trades=0,
            successful_trades=0,
            failed_trades=0,
            skipped_trades=0,
            critical_risk_prevented=False,
            risk_warnings=[],
            errors=["Weight for BTC cannot be negative"],
        )
        mock_rebalance_service.preview_rebalance.return_value = result

        request = RebalanceRequest(target_weights={"BTC": -50.0, "ETH": 150.0}, dry_run=True)

        with pytest.raises(ValueError, match="Weight"):
            await use_case.execute(request)

    # ===================================================================
    # Error Handling tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_service_failure_raises_runtime_error(self, use_case, mock_rebalance_service):
        """Test service failure raises RuntimeError."""
        mock_rebalance_service.preview_rebalance.side_effect = Exception("API Error")

        request = RebalanceRequest(target_weights={"BTC": 50.0, "ETH": 50.0}, dry_run=True)

        with pytest.raises(RuntimeError, match="Failed to execute rebalancing"):
            await use_case.execute(request)

    # ===================================================================
    # Edge Case tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_no_trades_needed(self, use_case, mock_rebalance_service):
        """Test when portfolio is already balanced."""
        result = Mock(
            success=True,
            message="Portfolio already balanced",
            initial_allocation={"BTC": 50.0, "ETH": 50.0},
            final_allocation={"BTC": 50.0, "ETH": 50.0},
            planned_trades=[
                Mock(
                    coin="BTC",
                    action=TradeAction.SKIP,
                    current_allocation_pct=50.0,
                    target_allocation_pct=50.0,
                    diff_pct=0.0,
                    current_usd_value=50000.0,
                    target_usd_value=50000.0,
                    trade_usd_value=0.0,
                    trade_size=None,
                    executed=False,
                    success=False,
                    error="No trade needed",
                    estimated_liquidation_price=None,
                    estimated_risk_level=None,
                    estimated_health_score=None,
                ),
                Mock(
                    coin="ETH",
                    action=TradeAction.SKIP,
                    current_allocation_pct=50.0,
                    target_allocation_pct=50.0,
                    diff_pct=0.0,
                    current_usd_value=50000.0,
                    target_usd_value=50000.0,
                    trade_usd_value=0.0,
                    trade_size=None,
                    executed=False,
                    success=False,
                    error="No trade needed",
                    estimated_liquidation_price=None,
                    estimated_risk_level=None,
                    estimated_health_score=None,
                ),
            ],
            executed_trades=0,
            successful_trades=0,
            failed_trades=0,
            skipped_trades=2,
            critical_risk_prevented=False,
            risk_warnings=[],
            errors=[],
        )
        mock_rebalance_service.preview_rebalance.return_value = result

        request = RebalanceRequest(target_weights={"BTC": 50.0, "ETH": 50.0}, dry_run=True)

        response = await use_case.execute(request)

        assert response.success is True
        assert response.actionable_trades == 0
        assert response.skipped_trades == 2
        assert response.total_usd_volume == 0.0

    @pytest.mark.asyncio
    async def test_trade_without_estimated_risk(self, use_case, mock_rebalance_service):
        """Test trade without risk estimation (None values)."""
        result = Mock(
            success=True,
            message="Success",
            initial_allocation={"BTC": 100.0},
            final_allocation={"BTC": 100.0},
            planned_trades=[
                Mock(
                    coin="BTC",
                    action=TradeAction.INCREASE,
                    current_allocation_pct=50.0,
                    target_allocation_pct=60.0,
                    diff_pct=10.0,
                    current_usd_value=50000.0,
                    target_usd_value=60000.0,
                    trade_usd_value=10000.0,
                    trade_size=0.2,
                    executed=False,
                    success=False,
                    error=None,
                    estimated_liquidation_price=None,
                    estimated_risk_level=None,  # No risk assessment
                    estimated_health_score=None,
                )
            ],
            executed_trades=0,
            successful_trades=0,
            failed_trades=0,
            skipped_trades=0,
            critical_risk_prevented=False,
            risk_warnings=[],
            errors=[],
        )
        mock_rebalance_service.preview_rebalance.return_value = result

        request = RebalanceRequest(target_weights={"BTC": 100.0}, dry_run=True)

        response = await use_case.execute(request)

        trade = response.planned_trades[0]
        assert trade.estimated_liquidation_price is None
        assert trade.estimated_risk_level is None
        assert trade.estimated_health_score is None
        # Should not be in high_risk_coins (no risk level)
        assert "BTC" not in response.high_risk_coins
