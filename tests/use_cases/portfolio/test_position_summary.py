"""
Unit tests for PositionSummaryUseCase.

Tests portfolio position aggregation and summary logic.
This is the primary dashboard data source.
"""

from unittest.mock import Mock

import pytest

from src.services.risk_calculator import PositionRisk, RiskLevel
from src.use_cases.portfolio.position_summary import (
    PositionSummaryRequest,
    PositionSummaryUseCase,
)
from tests.helpers.mock_data import PositionBuilder
from tests.helpers.service_mocks import ServiceMockBuilder, create_service_with_mocks


class TestPositionSummaryUseCase:
    """Test PositionSummaryUseCase."""

    @pytest.fixture
    def sample_positions(self):
        """Sample position data using PositionBuilder."""
        return [
            PositionBuilder()
            .with_coin("BTC")
            .with_size(1.0)
            .with_entry_price(48000.0)
            .with_position_value(50000.0)
            .with_pnl(2000.0)
            .with_leverage(3, "cross")
            .with_liquidation_price(40000.0)
            .build(),
            PositionBuilder()
            .with_coin("ETH")
            .with_size(-10.0)  # Short position
            .with_entry_price(3200.0)
            .with_position_value(30000.0)
            .with_pnl(-500.0)
            .with_leverage(2, "cross")
            .with_liquidation_price(3400.0)
            .build(),
        ]

    @pytest.fixture
    def sample_account_info(self):
        """Sample account information."""
        return {
            "margin_summary": {
                "account_value": 100000.0,
                "total_raw_usd": 70000.0,
                "total_margin_used": 30000.0,
            }
        }

    @pytest.fixture
    def use_case(self):
        """Create PositionSummaryUseCase with mocked dependencies."""
        mock_position = ServiceMockBuilder.position_service()
        mock_account = ServiceMockBuilder.account_service()
        mock_market_data = ServiceMockBuilder.market_data_service()
        mock_risk = Mock()  # RiskCalculator doesn't have a builder yet

        return create_service_with_mocks(
            PositionSummaryUseCase,
            "src.use_cases.portfolio.position_summary",
            {
                "position_service": mock_position,
                "account_service": mock_account,
                "market_data_service": mock_market_data,
                "risk_calculator": mock_risk,
            },
        )

    # ===================================================================
    # Basic Summary tests (no risk metrics)
    # ===================================================================

    @pytest.mark.asyncio
    async def test_position_summary_basic_success(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test basic position summary without risk metrics."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info

        request = PositionSummaryRequest(include_risk_metrics=False, include_spot_balances=False)

        response = await use_case.execute(request)

        assert response.total_positions == 2
        assert response.long_positions == 1
        assert response.short_positions == 1
        assert response.total_unrealized_pnl == 1500.0  # 2000 - 500
        assert response.total_position_value == 80000.0  # 50000 + 30000
        assert response.account_value == 100000.0
        assert response.margin_used == 30000.0
        assert response.margin_utilization_pct == 30.0
        assert len(response.positions) == 2

    @pytest.mark.asyncio
    async def test_position_summary_with_no_positions(self, use_case, sample_account_info):
        """Test summary with no open positions."""
        use_case.position_service.list_positions.return_value = []
        use_case.account_service.get_account_info.return_value = sample_account_info

        request = PositionSummaryRequest(include_risk_metrics=False)

        response = await use_case.execute(request)

        assert response.total_positions == 0
        assert response.long_positions == 0
        assert response.short_positions == 0
        assert response.total_unrealized_pnl == 0.0
        assert response.total_position_value == 0.0
        assert len(response.positions) == 0

    @pytest.mark.asyncio
    async def test_position_detail_fields(self, use_case, sample_positions, sample_account_info):
        """Test position detail fields are correctly populated."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info

        request = PositionSummaryRequest(include_risk_metrics=False)

        response = await use_case.execute(request)

        btc_pos = response.positions[0]
        assert btc_pos.coin == "BTC"
        assert btc_pos.size == 1.0
        assert btc_pos.side == "LONG"
        assert btc_pos.entry_price == 48000.0
        assert btc_pos.position_value == 50000.0
        assert btc_pos.unrealized_pnl == 2000.0
        assert btc_pos.leverage == 3
        assert btc_pos.leverage_type == "cross"

        eth_pos = response.positions[1]
        assert eth_pos.coin == "ETH"
        assert eth_pos.size == 10.0  # Absolute value
        assert eth_pos.side == "SHORT"
        assert eth_pos.unrealized_pnl == -500.0

    # ===================================================================
    # PnL Calculation tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_pnl_percentage_calculation(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test PnL percentage calculations."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info

        request = PositionSummaryRequest(include_risk_metrics=False)

        response = await use_case.execute(request)

        # Total PnL % = 1500 / 100000 * 100 = 1.5%
        assert response.total_unrealized_pnl_pct == pytest.approx(1.5, abs=0.01)

        # BTC position PnL% = 2000 / 50000 * 100 = 4%
        btc_pos = response.positions[0]
        assert btc_pos.unrealized_pnl_pct == pytest.approx(4.0, abs=0.01)

        # ETH position PnL% = -500 / 30000 * 100 = -1.67%
        eth_pos = response.positions[1]
        assert eth_pos.unrealized_pnl_pct == pytest.approx(-1.67, abs=0.01)

    @pytest.mark.asyncio
    async def test_margin_utilization_calculation(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test margin utilization percentage calculation."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info

        request = PositionSummaryRequest(include_risk_metrics=False)

        response = await use_case.execute(request)

        # Margin util = 30000 / 100000 * 100 = 30%
        assert response.margin_utilization_pct == pytest.approx(30.0, abs=0.01)
        assert response.available_balance == 70000.0

    # ===================================================================
    # Risk Metrics tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_position_summary_with_risk_metrics(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test summary with risk metrics enabled."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {"BTC": 50000.0, "ETH": 3000.0}

        # Mock risk assessments
        btc_risk = Mock(spec=PositionRisk)
        btc_risk.risk_level = RiskLevel.LOW
        btc_risk.health_score = 75
        btc_risk.liquidation_price = 40000.0
        btc_risk.liquidation_distance_pct = 20.0
        btc_risk.warnings = []

        eth_risk = Mock(spec=PositionRisk)
        eth_risk.risk_level = RiskLevel.CRITICAL
        eth_risk.health_score = 15
        eth_risk.liquidation_price = 3400.0
        eth_risk.liquidation_distance_pct = 5.0
        eth_risk.warnings = ["⚠️ CRITICAL RISK"]

        use_case.risk_calculator.assess_position_risk.side_effect = [btc_risk, eth_risk]

        request = PositionSummaryRequest(include_risk_metrics=True)

        response = await use_case.execute(request)

        # Verify risk metrics included
        btc_pos = response.positions[0]
        assert btc_pos.risk_level == "LOW"
        assert btc_pos.health_score == 75
        assert btc_pos.liquidation_price == 40000.0
        assert btc_pos.liquidation_distance_pct == 20.0

        eth_pos = response.positions[1]
        assert eth_pos.risk_level == "CRITICAL"
        assert eth_pos.health_score == 15
        assert len(eth_pos.warnings) == 1

        # Verify overall risk summary
        assert response.overall_risk_level == "CRITICAL"
        assert response.critical_positions == 1
        assert response.high_risk_positions == 0

    @pytest.mark.asyncio
    async def test_overall_risk_level_determination(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test overall risk level is determined from worst position."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {"BTC": 50000.0, "ETH": 3000.0}

        # Both positions at MODERATE risk
        risk = Mock(spec=PositionRisk)
        risk.risk_level = RiskLevel.MODERATE
        risk.health_score = 60
        risk.liquidation_price = None
        risk.liquidation_distance_pct = None
        risk.warnings = []

        use_case.risk_calculator.assess_position_risk.return_value = risk

        request = PositionSummaryRequest(include_risk_metrics=True)

        response = await use_case.execute(request)

        assert response.overall_risk_level == "MODERATE"
        assert response.critical_positions == 0
        assert response.high_risk_positions == 0

    @pytest.mark.asyncio
    async def test_risk_calculation_failure_handled_gracefully(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test that risk calculation failures don't break summary."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {"BTC": 50000.0, "ETH": 3000.0}

        # First position succeeds, second fails
        btc_risk = Mock(spec=PositionRisk)
        btc_risk.risk_level = RiskLevel.SAFE
        btc_risk.health_score = 95
        btc_risk.liquidation_price = None
        btc_risk.liquidation_distance_pct = None
        btc_risk.warnings = []

        use_case.risk_calculator.assess_position_risk.side_effect = [
            btc_risk,
            Exception("Risk calculation failed"),
        ]

        request = PositionSummaryRequest(include_risk_metrics=True)

        response = await use_case.execute(request)

        # Summary should still succeed
        assert response.total_positions == 2
        assert response.positions[0].risk_level == "SAFE"
        assert response.positions[1].risk_level is None  # Risk calc failed

    # ===================================================================
    # Spot Balances tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_position_summary_with_spot_balances(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test summary with spot balances included."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.account_service.get_spot_state.return_value = {
            "balances": [
                {"coin": "USDC", "total": "5000.0"},
                {"coin": "SOL", "total": "100.5"},
                {"coin": "AVAX", "total": "0.0"},  # Zero balance (filtered out)
            ]
        }

        request = PositionSummaryRequest(include_risk_metrics=False, include_spot_balances=True)

        response = await use_case.execute(request)

        assert response.spot_balances is not None
        assert response.num_spot_balances == 2
        assert response.spot_balances["USDC"] == 5000.0
        assert response.spot_balances["SOL"] == 100.5
        assert "AVAX" not in response.spot_balances  # Zero filtered out

    @pytest.mark.asyncio
    async def test_spot_balances_not_included_by_default(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test spot balances are not fetched by default."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        # Need to mock prices for position details
        use_case.market_data.get_all_prices.return_value = {"BTC": 50000.0, "ETH": 3000.0}

        request = PositionSummaryRequest(include_spot_balances=False)

        response = await use_case.execute(request)

        assert response.spot_balances is None
        assert response.num_spot_balances == 0
        use_case.account_service.get_spot_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_spot_balance_fetch_failure_handled_gracefully(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test spot balance fetch failure doesn't break summary."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.account_service.get_spot_state.side_effect = Exception("API Error")
        # Need to mock prices for position details
        use_case.market_data.get_all_prices.return_value = {"BTC": 50000.0, "ETH": 3000.0}

        request = PositionSummaryRequest(include_spot_balances=True)

        response = await use_case.execute(request)

        # Summary should still succeed
        assert response.total_positions == 2
        assert response.spot_balances is None
        assert response.num_spot_balances == 0

    # ===================================================================
    # Edge Case tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_zero_account_value_handled(self, use_case):
        """Test handling of zero account value (prevents division by zero)."""
        use_case.position_service.list_positions.return_value = []
        use_case.account_service.get_account_info.return_value = {
            "margin_summary": {
                "account_value": 0.0,
                "total_raw_usd": 0.0,
                "total_margin_used": 0.0,
            }
        }

        request = PositionSummaryRequest(include_risk_metrics=False)

        response = await use_case.execute(request)

        assert response.margin_utilization_pct == 0.0
        assert response.total_unrealized_pnl_pct == 0.0

    @pytest.mark.asyncio
    async def test_zero_position_value_handled(self, use_case):
        """Test handling of zero position value."""
        positions = [
            PositionBuilder()
            .with_coin("TEST")
            .with_size(0.0)
            .with_entry_price(1.0)
            .with_position_value(0.0)
            .with_pnl(0.0)
            .with_leverage(1, "cross")
            .build()
        ]
        use_case.position_service.list_positions.return_value = positions
        use_case.account_service.get_account_info.return_value = {
            "margin_summary": {
                "account_value": 100000.0,
                "total_raw_usd": 100000.0,
                "total_margin_used": 0.0,
            }
        }

        request = PositionSummaryRequest(include_risk_metrics=False)

        response = await use_case.execute(request)

        test_pos = response.positions[0]
        assert test_pos.unrealized_pnl_pct == 0.0  # No division by zero

    @pytest.mark.asyncio
    async def test_service_failure_raises_runtime_error(self, use_case):
        """Test service failure raises RuntimeError."""
        use_case.position_service.list_positions.side_effect = Exception("API Error")

        request = PositionSummaryRequest()

        with pytest.raises(RuntimeError, match="Failed to get position summary"):
            await use_case.execute(request)

    # ===================================================================
    # Price Handling tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_current_price_from_market_data_when_risk_enabled(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test current price is fetched from market data when risk metrics enabled."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {
            "BTC": 55000.0,  # Different from entry price
            "ETH": 3100.0,
        }

        request = PositionSummaryRequest(include_risk_metrics=True)

        response = await use_case.execute(request)

        btc_pos = response.positions[0]
        assert btc_pos.current_price == 55000.0  # From market data

        eth_pos = response.positions[1]
        assert eth_pos.current_price == 3100.0  # From market data

    @pytest.mark.asyncio
    async def test_current_price_fallback_to_entry_price(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test current price falls back to entry price when not available."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info

        request = PositionSummaryRequest(include_risk_metrics=False)

        response = await use_case.execute(request)

        btc_pos = response.positions[0]
        assert btc_pos.current_price == 48000.0  # Falls back to entry price

        eth_pos = response.positions[1]
        assert eth_pos.current_price == 3200.0  # Falls back to entry price
