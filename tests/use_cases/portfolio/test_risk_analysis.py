"""
Unit tests for RiskAnalysisUseCase.

Tests portfolio and position-level risk assessment logic.
CRITICAL - bugs here = incorrect risk calculations.
"""

from unittest.mock import Mock

import pytest

from src.services.risk_calculator import RiskLevel
from src.use_cases.portfolio.risk_analysis import (
    RiskAnalysisRequest,
    RiskAnalysisUseCase,
)
from tests.helpers.mock_data import PositionBuilder
from tests.helpers.service_mocks import ServiceMockBuilder, create_service_with_mocks


class TestRiskAnalysisUseCase:
    """Test RiskAnalysisUseCase."""

    @pytest.fixture
    def sample_positions(self):
        """Sample position data with varying risk levels using PositionBuilder."""
        return [
            PositionBuilder()
            .with_coin("BTC")
            .with_size(1.0)
            .with_entry_price(48000.0)
            .with_leverage(3, "cross")
            .build(),
            PositionBuilder()
            .with_coin("ETH")
            .with_size(-10.0)  # Short position
            .with_entry_price(3200.0)
            .with_leverage(5, "isolated")
            .build(),
            PositionBuilder()
            .with_coin("SOL")
            .with_size(100.0)
            .with_entry_price(140.0)
            .with_leverage(2, "cross")
            .build(),
        ]

    @pytest.fixture
    def sample_account_info(self):
        """Sample account information."""
        return {
            "margin_summary": {
                "account_value": 100000.0,
                "available_balance": 70000.0,
                "total_margin_used": 30000.0,
            },
            "crossMarginSummary": {"crossMaintenanceMarginUsed": "5000", "accountValue": "100000"},
        }

    @pytest.fixture
    def use_case(self):
        """Create RiskAnalysisUseCase with mocked dependencies."""
        mock_position = ServiceMockBuilder.position_service()
        mock_account = ServiceMockBuilder.account_service()
        mock_market_data = ServiceMockBuilder.market_data_service()
        mock_risk = Mock()  # RiskCalculator doesn't have a builder yet

        return create_service_with_mocks(
            RiskAnalysisUseCase,
            "src.use_cases.portfolio.risk_analysis",
            {
                "position_service": mock_position,
                "account_service": mock_account,
                "market_data_service": mock_market_data,
                "risk_calculator": mock_risk,
            },
        )

    # ===================================================================
    # Basic Risk Analysis tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_risk_analysis_all_positions_success(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test basic risk analysis for all positions."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
        }

        # Mock position risk assessments
        use_case.risk_calculator.assess_position_risk.side_effect = [
            Mock(
                risk_level=RiskLevel.LOW,
                health_score=80,
                liquidation_price=40000.0,
                liquidation_distance_pct=20.0,
                warnings=[],
            ),
            Mock(
                risk_level=RiskLevel.MODERATE,
                health_score=60,
                liquidation_price=3500.0,
                liquidation_distance_pct=16.7,
                warnings=["Moderate leverage on short position"],
            ),
            Mock(
                risk_level=RiskLevel.SAFE,
                health_score=90,
                liquidation_price=100.0,
                liquidation_distance_pct=33.3,
                warnings=[],
            ),
        ]

        # Mock portfolio risk assessment
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.LOW, portfolio_health_score=75, warnings=[]
        )

        request = RiskAnalysisRequest()

        response = await use_case.execute(request)

        assert response.overall_risk_level == "LOW"
        assert response.portfolio_health_score == 75
        assert response.critical_positions == 0
        assert response.high_risk_positions == 0
        assert response.moderate_risk_positions == 1
        assert response.low_risk_positions == 1
        assert response.safe_positions == 1
        assert response.margin_utilization_pct == 30.0  # 30000/100000 * 100
        assert len(response.positions) == 3

    @pytest.mark.asyncio
    async def test_risk_analysis_with_cross_margin_ratio(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test risk analysis includes cross margin ratio."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
        }

        # Mock assessments
        use_case.risk_calculator.assess_position_risk.return_value = Mock(
            risk_level=RiskLevel.SAFE,
            health_score=85,
            liquidation_price=30000.0,
            liquidation_distance_pct=40.0,
            warnings=[],
        )
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.SAFE, portfolio_health_score=85, warnings=[]
        )

        request = RiskAnalysisRequest(include_cross_margin_ratio=True)

        response = await use_case.execute(request)

        # Cross margin ratio = 5000 / 100000 * 100 = 5%
        assert response.cross_margin_ratio_pct == pytest.approx(5.0, abs=0.01)
        assert response.cross_maintenance_margin == 5000.0
        assert response.cross_account_value == 100000.0

    @pytest.mark.asyncio
    async def test_risk_analysis_without_cross_margin_ratio(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test risk analysis excludes cross margin ratio when not requested."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
        }

        # Mock assessments
        use_case.risk_calculator.assess_position_risk.return_value = Mock(
            risk_level=RiskLevel.SAFE,
            health_score=85,
            liquidation_price=30000.0,
            liquidation_distance_pct=40.0,
            warnings=[],
        )
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.SAFE, portfolio_health_score=85, warnings=[]
        )

        request = RiskAnalysisRequest(include_cross_margin_ratio=False)

        response = await use_case.execute(request)

        assert response.cross_margin_ratio_pct is None
        assert response.cross_maintenance_margin is None
        assert response.cross_account_value is None

    # ===================================================================
    # Filtered Risk Analysis tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_risk_analysis_filtered_by_coins(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test risk analysis filtered by specific coins."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
        }

        # Mock assessments (should only be called for BTC and ETH)
        use_case.risk_calculator.assess_position_risk.side_effect = [
            Mock(
                risk_level=RiskLevel.LOW,
                health_score=80,
                liquidation_price=40000.0,
                liquidation_distance_pct=20.0,
                warnings=[],
            ),
            Mock(
                risk_level=RiskLevel.MODERATE,
                health_score=60,
                liquidation_price=3500.0,
                liquidation_distance_pct=16.7,
                warnings=[],
            ),
        ]
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.LOW, portfolio_health_score=70, warnings=[]
        )

        request = RiskAnalysisRequest(coins=["BTC", "ETH"])

        response = await use_case.execute(request)

        assert len(response.positions) == 2
        assert response.positions[0].coin == "BTC"
        assert response.positions[1].coin == "ETH"
        # Should only call assess_position_risk twice (not 3 times)
        assert use_case.risk_calculator.assess_position_risk.call_count == 2

    # ===================================================================
    # Risk Level Distribution tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_risk_level_counts(self, use_case, sample_account_info):
        """Test risk level counts are correct."""
        # Positions with different risk levels
        positions = [
            {
                "position": {
                    "coin": "BTC",
                    "size": 1.0,
                    "entry_price": 50000.0,
                    "leverage": {"value": 2, "type": "cross"},
                }
            },
            {
                "position": {
                    "coin": "ETH",
                    "size": 1.0,
                    "entry_price": 3000.0,
                    "leverage": {"value": 5, "type": "cross"},
                }
            },
            {
                "position": {
                    "coin": "SOL",
                    "size": 1.0,
                    "entry_price": 150.0,
                    "leverage": {"value": 10, "type": "cross"},
                }
            },
            {
                "position": {
                    "coin": "AVAX",
                    "size": 1.0,
                    "entry_price": 40.0,
                    "leverage": {"value": 20, "type": "cross"},
                }
            },
        ]

        use_case.position_service.list_positions.return_value = positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
            "AVAX": 40.0,
        }

        # Mock different risk levels
        use_case.risk_calculator.assess_position_risk.side_effect = [
            Mock(
                risk_level=RiskLevel.SAFE,
                health_score=95,
                liquidation_price=30000.0,
                liquidation_distance_pct=40.0,
                warnings=[],
            ),
            Mock(
                risk_level=RiskLevel.LOW,
                health_score=75,
                liquidation_price=2500.0,
                liquidation_distance_pct=16.7,
                warnings=[],
            ),
            Mock(
                risk_level=RiskLevel.HIGH,
                health_score=40,
                liquidation_price=135.0,
                liquidation_distance_pct=10.0,
                warnings=["High leverage"],
            ),
            Mock(
                risk_level=RiskLevel.CRITICAL,
                health_score=10,
                liquidation_price=38.0,
                liquidation_distance_pct=5.0,
                warnings=["Very close to liquidation"],
            ),
        ]
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.HIGH,
            portfolio_health_score=50,
            warnings=["Multiple high-risk positions"],
        )

        request = RiskAnalysisRequest()

        response = await use_case.execute(request)

        assert response.safe_positions == 1
        assert response.low_risk_positions == 1
        assert response.moderate_risk_positions == 0
        assert response.high_risk_positions == 1
        assert response.critical_positions == 1
        assert response.overall_risk_level == "HIGH"

    # ===================================================================
    # Position Detail tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_position_detail_fields(self, use_case, sample_account_info):
        """Test position risk detail includes all fields."""
        positions = [
            {
                "position": {
                    "coin": "BTC",
                    "size": -0.5,  # Short
                    "entry_price": 52000.0,
                    "mark_price": 50000.0,
                    "leverage": {"value": 3, "type": "isolated"},
                }
            }
        ]

        use_case.position_service.list_positions.return_value = positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {"BTC": 49000.0}

        use_case.risk_calculator.assess_position_risk.return_value = Mock(
            risk_level=RiskLevel.MODERATE,
            health_score=65,
            liquidation_price=56000.0,
            liquidation_distance_pct=14.3,
            warnings=["Price moved against short position"],
        )
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.MODERATE, portfolio_health_score=65, warnings=[]
        )

        request = RiskAnalysisRequest()

        response = await use_case.execute(request)

        pos = response.positions[0]
        assert pos.coin == "BTC"
        assert pos.size == 0.5  # Absolute value
        assert pos.side == "SHORT"
        assert pos.entry_price == 52000.0
        assert pos.current_price == 49000.0
        assert pos.leverage == 3
        assert pos.leverage_type == "isolated"
        assert pos.risk_level == "MODERATE"
        assert pos.health_score == 65
        assert pos.liquidation_price == 56000.0
        assert pos.liquidation_distance_pct == 14.3
        assert len(pos.warnings) == 1

    @pytest.mark.asyncio
    async def test_position_side_determination(self, use_case, sample_account_info):
        """Test position side (LONG/SHORT) is correctly determined."""
        positions = [
            {
                "position": {
                    "coin": "BTC",
                    "size": 1.0,
                    "entry_price": 50000.0,
                    "leverage": {"value": 2, "type": "cross"},
                }
            },
            {
                "position": {
                    "coin": "ETH",
                    "size": -10.0,
                    "entry_price": 3000.0,
                    "leverage": {"value": 2, "type": "cross"},
                }
            },
        ]

        use_case.position_service.list_positions.return_value = positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {"BTC": 50000.0, "ETH": 3000.0}

        use_case.risk_calculator.assess_position_risk.return_value = Mock(
            risk_level=RiskLevel.SAFE,
            health_score=85,
            liquidation_price=30000.0,
            liquidation_distance_pct=40.0,
            warnings=[],
        )
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.SAFE, portfolio_health_score=85, warnings=[]
        )

        request = RiskAnalysisRequest()

        response = await use_case.execute(request)

        assert response.positions[0].side == "LONG"
        assert response.positions[1].side == "SHORT"

    # ===================================================================
    # Price Handling tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_price_fallback_to_mark_price(self, use_case, sample_account_info):
        """Test price falls back to mark_price when not in price data."""
        positions = [
            {
                "position": {
                    "coin": "BTC",
                    "size": 1.0,
                    "entry_price": 48000.0,
                    "mark_price": 49500.0,
                    "leverage": {"value": 2, "type": "cross"},
                }
            }
        ]

        use_case.position_service.list_positions.return_value = positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {}  # No price data

        use_case.risk_calculator.assess_position_risk.return_value = Mock(
            risk_level=RiskLevel.SAFE,
            health_score=85,
            liquidation_price=30000.0,
            liquidation_distance_pct=40.0,
            warnings=[],
        )
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.SAFE, portfolio_health_score=85, warnings=[]
        )

        request = RiskAnalysisRequest()

        response = await use_case.execute(request)

        # Should use mark_price as fallback
        assert response.positions[0].current_price == 49500.0

    @pytest.mark.asyncio
    async def test_price_fallback_to_entry_price(self, use_case, sample_account_info):
        """Test price falls back to entry_price when mark_price unavailable."""
        positions = [
            {
                "position": {
                    "coin": "BTC",
                    "size": 1.0,
                    "entry_price": 48000.0,
                    # No mark_price field
                    "leverage": {"value": 2, "type": "cross"},
                }
            }
        ]

        use_case.position_service.list_positions.return_value = positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {}  # No price data

        use_case.risk_calculator.assess_position_risk.return_value = Mock(
            risk_level=RiskLevel.SAFE,
            health_score=85,
            liquidation_price=30000.0,
            liquidation_distance_pct=40.0,
            warnings=[],
        )
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.SAFE, portfolio_health_score=85, warnings=[]
        )

        request = RiskAnalysisRequest()

        response = await use_case.execute(request)

        # Should use entry_price as final fallback
        assert response.positions[0].current_price == 48000.0

    # ===================================================================
    # Account Metrics tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_account_metrics_included(self, use_case, sample_positions, sample_account_info):
        """Test account metrics are included in response."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
        }

        use_case.risk_calculator.assess_position_risk.return_value = Mock(
            risk_level=RiskLevel.SAFE,
            health_score=85,
            liquidation_price=30000.0,
            liquidation_distance_pct=40.0,
            warnings=[],
        )
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.SAFE, portfolio_health_score=85, warnings=[]
        )

        request = RiskAnalysisRequest()

        response = await use_case.execute(request)

        assert response.account_value == 100000.0
        assert response.available_margin == 70000.0
        assert response.total_margin_used == 30000.0
        assert response.margin_utilization_pct == 30.0

    @pytest.mark.asyncio
    async def test_margin_utilization_zero_account_value(self, use_case):
        """Test margin utilization handles zero account value."""
        use_case.position_service.list_positions.return_value = []
        use_case.account_service.get_account_info.return_value = {
            "margin_summary": {
                "account_value": 0.0,
                "available_balance": 0.0,
                "total_margin_used": 0.0,
            }
        }
        use_case.market_data.get_all_prices.return_value = {}

        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.SAFE, portfolio_health_score=100, warnings=[]
        )

        request = RiskAnalysisRequest()

        response = await use_case.execute(request)

        # Should not divide by zero
        assert response.margin_utilization_pct == 0.0

    # ===================================================================
    # Cross Margin Ratio tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_cross_margin_ratio_missing_data(self, use_case, sample_positions):
        """Test cross margin ratio handles missing data gracefully."""
        account_info_no_cross = {
            "margin_summary": {
                "account_value": 100000.0,
                "available_balance": 70000.0,
                "total_margin_used": 30000.0,
            }
            # No crossMarginSummary
        }

        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = account_info_no_cross
        use_case.market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
        }

        use_case.risk_calculator.assess_position_risk.return_value = Mock(
            risk_level=RiskLevel.SAFE,
            health_score=85,
            liquidation_price=30000.0,
            liquidation_distance_pct=40.0,
            warnings=[],
        )
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.SAFE, portfolio_health_score=85, warnings=[]
        )

        request = RiskAnalysisRequest(include_cross_margin_ratio=True)

        response = await use_case.execute(request)

        # Should not fail, just return None
        assert response.cross_margin_ratio_pct is None
        assert response.cross_maintenance_margin is None
        assert response.cross_account_value is None

    # ===================================================================
    # Error Handling tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_position_risk_assessment_failure_handled(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test position risk assessment failure is logged but doesn't break analysis."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
        }

        # First position fails, others succeed
        use_case.risk_calculator.assess_position_risk.side_effect = [
            Exception("API Error"),
            Mock(
                risk_level=RiskLevel.LOW,
                health_score=75,
                liquidation_price=2500.0,
                liquidation_distance_pct=16.7,
                warnings=[],
            ),
            Mock(
                risk_level=RiskLevel.SAFE,
                health_score=90,
                liquidation_price=100.0,
                liquidation_distance_pct=33.3,
                warnings=[],
            ),
        ]
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.LOW, portfolio_health_score=80, warnings=[]
        )

        request = RiskAnalysisRequest()

        response = await use_case.execute(request)

        # Should only include 2 positions (BTC failed)
        assert len(response.positions) == 2
        assert response.positions[0].coin == "ETH"
        assert response.positions[1].coin == "SOL"

    @pytest.mark.asyncio
    async def test_service_failure_raises_runtime_error(self, use_case):
        """Test service failure raises RuntimeError."""
        use_case.position_service.list_positions.side_effect = Exception("API Error")

        request = RiskAnalysisRequest()

        with pytest.raises(RuntimeError, match="Failed to analyze risk"):
            await use_case.execute(request)

    # ===================================================================
    # Edge Case tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_no_positions(self, use_case, sample_account_info):
        """Test risk analysis with no positions."""
        use_case.position_service.list_positions.return_value = []
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {}

        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.SAFE, portfolio_health_score=100, warnings=[]
        )

        request = RiskAnalysisRequest()

        response = await use_case.execute(request)

        assert len(response.positions) == 0
        assert response.safe_positions == 0
        assert response.low_risk_positions == 0
        assert response.moderate_risk_positions == 0
        assert response.high_risk_positions == 0
        assert response.critical_positions == 0
        assert response.overall_risk_level == "SAFE"
        assert response.portfolio_health_score == 100

    @pytest.mark.asyncio
    async def test_portfolio_warnings_included(
        self, use_case, sample_positions, sample_account_info
    ):
        """Test portfolio-level warnings are included."""
        use_case.position_service.list_positions.return_value = sample_positions
        use_case.account_service.get_account_info.return_value = sample_account_info
        use_case.market_data.get_all_prices.return_value = {
            "BTC": 50000.0,
            "ETH": 3000.0,
            "SOL": 150.0,
        }

        use_case.risk_calculator.assess_position_risk.return_value = Mock(
            risk_level=RiskLevel.SAFE,
            health_score=85,
            liquidation_price=30000.0,
            liquidation_distance_pct=40.0,
            warnings=[],
        )
        use_case.risk_calculator.assess_portfolio_risk.return_value = Mock(
            overall_risk_level=RiskLevel.MODERATE,
            portfolio_health_score=65,
            warnings=["High margin utilization", "Multiple correlated positions"],
        )

        request = RiskAnalysisRequest()

        response = await use_case.execute(request)

        assert len(response.portfolio_warnings) == 2
        assert "High margin utilization" in response.portfolio_warnings
        assert "Multiple correlated positions" in response.portfolio_warnings
