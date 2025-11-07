"""
Unit tests for PlaceScaleOrderUseCase.

Tests scale order placement logic.
CRITICAL - bugs here = actual trading operations with real money.

MIGRATED: Now using tests/helpers for service mocking.
- create_service_with_mocks replaces manual fixture boilerplate
- AsyncMock configured manually for scale_order_service (no builder yet)
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.models.scale_order import OrderPlacement, ScaleOrderConfig, ScaleOrderResult
from src.use_cases.scale_orders.place import (
    PlaceScaleOrderRequest,
    PlaceScaleOrderUseCase,
)

# Import helpers for cleaner service mocking
from tests.helpers import create_service_with_mocks


class TestPlaceScaleOrderUseCase:
    """Test PlaceScaleOrderUseCase."""

    @pytest.fixture
    def use_case(self):
        """Create PlaceScaleOrderUseCase with mocked dependencies."""
        # Create mock with AsyncMock for place_scale_order
        mock_scale_order = Mock()
        mock_scale_order.place_scale_order = AsyncMock()

        return create_service_with_mocks(
            PlaceScaleOrderUseCase,
            "src.use_cases.scale_orders.place",
            {"scale_order_service": mock_scale_order},
        )

    @pytest.fixture
    def mock_scale_order_service(self, use_case):
        """Get the mocked scale_order_service from use_case."""
        return use_case.scale_order_service

    @pytest.fixture
    def sample_config(self):
        """Sample scale order config."""
        return ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            num_orders=5,
            start_price=50000.0,
            end_price=48000.0,
            distribution_type="linear",
            time_in_force="Gtc",
        )

    # ===================================================================
    # Successful Placement tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_place_all_orders_success(
        self, use_case, mock_scale_order_service, sample_config
    ):
        """Test all orders placed successfully."""
        # Mock successful result
        result = ScaleOrderResult(
            scale_order_id="scale_12345",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            placements=[
                OrderPlacement(order_id=1001, price=50000.0, size=0.040, status="success"),
                OrderPlacement(order_id=1002, price=49500.0, size=0.040, status="success"),
                OrderPlacement(order_id=1003, price=49000.0, size=0.041, status="success"),
                OrderPlacement(order_id=1004, price=48500.0, size=0.041, status="success"),
                OrderPlacement(order_id=1005, price=48000.0, size=0.042, status="success"),
            ],
            orders_placed=5,
            orders_failed=0,
            average_price=49000.0,
            total_placed_size=0.204,
            status="completed",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=sample_config)

        response = await use_case.execute(request)

        # Verify service called
        mock_scale_order_service.place_scale_order.assert_called_once_with(sample_config)

        # Verify response
        assert response.result.scale_order_id == "scale_12345"
        assert response.result.coin == "BTC"
        assert response.result.is_buy is True
        assert response.result.num_orders == 5
        assert response.result.orders_placed == 5
        assert response.result.orders_failed == 0
        assert response.result.status == "completed"
        assert len(response.result.placements) == 5

    @pytest.mark.asyncio
    async def test_place_sell_orders_success(self, use_case, mock_scale_order_service):
        """Test SELL scale order placement."""
        config = ScaleOrderConfig(
            coin="ETH",
            is_buy=False,  # SELL
            total_usd_amount=5000.0,
            num_orders=3,
            start_price=3000.0,
            end_price=3300.0,
        )

        result = ScaleOrderResult(
            scale_order_id="scale_67890",
            coin="ETH",
            is_buy=False,
            total_usd_amount=5000.0,
            total_coin_size=1.6,
            num_orders=3,
            placements=[
                OrderPlacement(order_id=2001, price=3000.0, size=0.533, status="success"),
                OrderPlacement(order_id=2002, price=3150.0, size=0.533, status="success"),
                OrderPlacement(order_id=2003, price=3300.0, size=0.534, status="success"),
            ],
            orders_placed=3,
            orders_failed=0,
            average_price=3150.0,
            total_placed_size=1.6,
            status="completed",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=config)

        response = await use_case.execute(request)

        assert response.result.is_buy is False
        assert response.result.orders_placed == 3
        assert response.result.status == "completed"

    # ===================================================================
    # Partial Success tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_place_partial_success(self, use_case, mock_scale_order_service, sample_config):
        """Test some orders placed, some failed."""
        result = ScaleOrderResult(
            scale_order_id="scale_partial",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            placements=[
                OrderPlacement(order_id=1001, price=50000.0, size=0.040, status="success"),
                OrderPlacement(order_id=1002, price=49500.0, size=0.040, status="success"),
                OrderPlacement(
                    order_id=None,
                    price=49000.0,
                    size=0.041,
                    status="failed",
                    error="Insufficient liquidity",
                ),
                OrderPlacement(order_id=1004, price=48500.0, size=0.041, status="success"),
                OrderPlacement(
                    order_id=None, price=48000.0, size=0.042, status="failed", error="API timeout"
                ),
            ],
            orders_placed=3,
            orders_failed=2,
            average_price=49300.0,
            total_placed_size=0.121,
            status="partial",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=sample_config)

        response = await use_case.execute(request)

        assert response.result.orders_placed == 3
        assert response.result.orders_failed == 2
        assert response.result.status == "partial"

        # Check failed placements
        failed_placements = [p for p in response.result.placements if p.status == "failed"]
        assert len(failed_placements) == 2
        assert failed_placements[0].error is not None

    @pytest.mark.asyncio
    async def test_place_mostly_failed(self, use_case, mock_scale_order_service, sample_config):
        """Test mostly failed orders (only 1 success)."""
        result = ScaleOrderResult(
            scale_order_id="scale_mostly_failed",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            placements=[
                OrderPlacement(order_id=1001, price=50000.0, size=0.040, status="success"),
                OrderPlacement(
                    order_id=None, price=49500.0, size=0.040, status="failed", error="Rate limit"
                ),
                OrderPlacement(
                    order_id=None, price=49000.0, size=0.041, status="failed", error="Rate limit"
                ),
                OrderPlacement(
                    order_id=None, price=48500.0, size=0.041, status="failed", error="Rate limit"
                ),
                OrderPlacement(
                    order_id=None, price=48000.0, size=0.042, status="failed", error="Rate limit"
                ),
            ],
            orders_placed=1,
            orders_failed=4,
            average_price=50000.0,
            total_placed_size=0.040,
            status="partial",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=sample_config)

        response = await use_case.execute(request)

        assert response.result.orders_placed == 1
        assert response.result.orders_failed == 4
        assert response.result.status == "partial"

    # ===================================================================
    # Complete Failure tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_place_all_orders_failed(self, use_case, mock_scale_order_service, sample_config):
        """Test all orders failed to place."""
        result = ScaleOrderResult(
            scale_order_id="scale_failed",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            placements=[
                OrderPlacement(
                    order_id=None, price=50000.0, size=0.040, status="failed", error="API Error"
                ),
                OrderPlacement(
                    order_id=None, price=49500.0, size=0.040, status="failed", error="API Error"
                ),
                OrderPlacement(
                    order_id=None, price=49000.0, size=0.041, status="failed", error="API Error"
                ),
                OrderPlacement(
                    order_id=None, price=48500.0, size=0.041, status="failed", error="API Error"
                ),
                OrderPlacement(
                    order_id=None, price=48000.0, size=0.042, status="failed", error="API Error"
                ),
            ],
            orders_placed=0,
            orders_failed=5,
            average_price=None,
            total_placed_size=0.0,
            status="failed",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=sample_config)

        response = await use_case.execute(request)

        assert response.result.orders_placed == 0
        assert response.result.orders_failed == 5
        assert response.result.status == "failed"
        assert response.result.total_placed_size == 0.0

    # ===================================================================
    # Placement Detail tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_placement_includes_order_ids(
        self, use_case, mock_scale_order_service, sample_config
    ):
        """Test placements include Hyperliquid order IDs."""
        result = ScaleOrderResult(
            scale_order_id="scale_12345",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            placements=[
                OrderPlacement(order_id=12345, price=50000.0, size=0.040, status="success"),
                OrderPlacement(order_id=12346, price=49500.0, size=0.040, status="success"),
                OrderPlacement(order_id=12347, price=49000.0, size=0.041, status="success"),
                OrderPlacement(order_id=12348, price=48500.0, size=0.041, status="success"),
                OrderPlacement(order_id=12349, price=48000.0, size=0.042, status="success"),
            ],
            orders_placed=5,
            orders_failed=0,
            average_price=49000.0,
            total_placed_size=0.204,
            status="completed",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=sample_config)

        response = await use_case.execute(request)

        # Verify all placements have order IDs
        for placement in response.result.placements:
            if placement.status == "success":
                assert placement.order_id is not None
                assert placement.order_id > 0

    @pytest.mark.asyncio
    async def test_placement_includes_price_and_size(
        self, use_case, mock_scale_order_service, sample_config
    ):
        """Test placements include price and size for each order."""
        result = ScaleOrderResult(
            scale_order_id="scale_12345",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            placements=[
                OrderPlacement(order_id=1001, price=50000.0, size=0.040, status="success"),
                OrderPlacement(order_id=1002, price=49500.0, size=0.040, status="success"),
                OrderPlacement(order_id=1003, price=49000.0, size=0.041, status="success"),
                OrderPlacement(order_id=1004, price=48500.0, size=0.041, status="success"),
                OrderPlacement(order_id=1005, price=48000.0, size=0.042, status="success"),
            ],
            orders_placed=5,
            orders_failed=0,
            average_price=49000.0,
            total_placed_size=0.204,
            status="completed",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=sample_config)

        response = await use_case.execute(request)

        # Verify all placements have price and size
        for placement in response.result.placements:
            assert placement.price > 0
            assert placement.size > 0

    @pytest.mark.asyncio
    async def test_placement_error_messages(
        self, use_case, mock_scale_order_service, sample_config
    ):
        """Test failed placements include error messages."""
        result = ScaleOrderResult(
            scale_order_id="scale_partial",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=3,
            placements=[
                OrderPlacement(order_id=1001, price=50000.0, size=0.068, status="success"),
                OrderPlacement(
                    order_id=None,
                    price=49000.0,
                    size=0.068,
                    status="failed",
                    error="Insufficient margin",
                ),
                OrderPlacement(
                    order_id=None,
                    price=48000.0,
                    size=0.068,
                    status="failed",
                    error="Order size below minimum",
                ),
            ],
            orders_placed=1,
            orders_failed=2,
            average_price=50000.0,
            total_placed_size=0.068,
            status="partial",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=sample_config)

        response = await use_case.execute(request)

        # Verify failed placements have error messages
        failed_placements = [p for p in response.result.placements if p.status == "failed"]
        assert len(failed_placements) == 2
        assert all(p.error is not None for p in failed_placements)
        assert "Insufficient margin" in failed_placements[0].error
        assert "Order size below minimum" in failed_placements[1].error

    # ===================================================================
    # Result Metrics tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_result_includes_scale_order_id(
        self, use_case, mock_scale_order_service, sample_config
    ):
        """Test result includes unique scale order ID for tracking."""
        result = ScaleOrderResult(
            scale_order_id="scale_abc123xyz",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            placements=[
                OrderPlacement(order_id=1001, price=50000.0, size=0.040, status="success"),
                OrderPlacement(order_id=1002, price=49500.0, size=0.040, status="success"),
                OrderPlacement(order_id=1003, price=49000.0, size=0.041, status="success"),
                OrderPlacement(order_id=1004, price=48500.0, size=0.041, status="success"),
                OrderPlacement(order_id=1005, price=48000.0, size=0.042, status="success"),
            ],
            orders_placed=5,
            orders_failed=0,
            average_price=49000.0,
            total_placed_size=0.204,
            status="completed",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=sample_config)

        response = await use_case.execute(request)

        assert response.result.scale_order_id == "scale_abc123xyz"
        assert len(response.result.scale_order_id) > 0

    @pytest.mark.asyncio
    async def test_result_includes_average_price(
        self, use_case, mock_scale_order_service, sample_config
    ):
        """Test result includes average fill price."""
        result = ScaleOrderResult(
            scale_order_id="scale_12345",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            placements=[
                OrderPlacement(order_id=1001, price=50000.0, size=0.040, status="success"),
                OrderPlacement(order_id=1002, price=49500.0, size=0.040, status="success"),
                OrderPlacement(order_id=1003, price=49000.0, size=0.041, status="success"),
                OrderPlacement(order_id=1004, price=48500.0, size=0.041, status="success"),
                OrderPlacement(order_id=1005, price=48000.0, size=0.042, status="success"),
            ],
            orders_placed=5,
            orders_failed=0,
            average_price=49000.0,
            total_placed_size=0.204,
            status="completed",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=sample_config)

        response = await use_case.execute(request)

        assert response.result.average_price == 49000.0

    @pytest.mark.asyncio
    async def test_result_includes_total_placed_size(
        self, use_case, mock_scale_order_service, sample_config
    ):
        """Test result includes total size actually placed."""
        result = ScaleOrderResult(
            scale_order_id="scale_12345",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            placements=[
                OrderPlacement(order_id=1001, price=50000.0, size=0.040, status="success"),
                OrderPlacement(order_id=1002, price=49500.0, size=0.040, status="success"),
                OrderPlacement(order_id=1003, price=49000.0, size=0.041, status="success"),
                OrderPlacement(order_id=1004, price=48500.0, size=0.041, status="success"),
                OrderPlacement(order_id=1005, price=48000.0, size=0.042, status="success"),
            ],
            orders_placed=5,
            orders_failed=0,
            average_price=49000.0,
            total_placed_size=0.204,
            status="completed",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=sample_config)

        response = await use_case.execute(request)

        assert response.result.total_placed_size == 0.204

    # ===================================================================
    # Error Handling tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_invalid_config_raises_value_error(self, use_case, mock_scale_order_service):
        """Test invalid configuration raises ValueError."""
        mock_scale_order_service.place_scale_order.side_effect = ValueError(
            "start_price must be different from end_price"
        )

        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            num_orders=5,
            start_price=50000.0,
            end_price=49000.0,
        )

        request = PlaceScaleOrderRequest(config=config)

        with pytest.raises(ValueError, match="start_price must be different from end_price"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_service_failure_raises_runtime_error(
        self, use_case, mock_scale_order_service, sample_config
    ):
        """Test service failure raises RuntimeError."""
        mock_scale_order_service.place_scale_order.side_effect = Exception("API connection error")

        request = PlaceScaleOrderRequest(config=sample_config)

        with pytest.raises(RuntimeError, match="Failed to place scale order"):
            await use_case.execute(request)

    # ===================================================================
    # Edge Case tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_place_minimum_orders(self, use_case, mock_scale_order_service):
        """Test placing minimum orders (2)."""
        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=1000.0,
            num_orders=2,
            start_price=50000.0,
            end_price=49000.0,
        )

        result = ScaleOrderResult(
            scale_order_id="scale_min",
            coin="BTC",
            is_buy=True,
            total_usd_amount=1000.0,
            total_coin_size=0.0204,
            num_orders=2,
            placements=[
                OrderPlacement(order_id=1001, price=50000.0, size=0.010, status="success"),
                OrderPlacement(order_id=1002, price=49000.0, size=0.0104, status="success"),
            ],
            orders_placed=2,
            orders_failed=0,
            average_price=49500.0,
            total_placed_size=0.0204,
            status="completed",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=config)

        response = await use_case.execute(request)

        assert response.result.num_orders == 2
        assert response.result.orders_placed == 2
        assert len(response.result.placements) == 2

    @pytest.mark.asyncio
    async def test_place_many_orders(self, use_case, mock_scale_order_service):
        """Test placing many orders (20)."""
        config = ScaleOrderConfig(
            coin="ETH",
            is_buy=True,
            total_usd_amount=20000.0,
            num_orders=20,
            start_price=3000.0,
            end_price=2800.0,
        )

        # Generate 20 placements
        placements = []
        for i in range(20):
            price = 3000.0 - (i * 10.5)
            placements.append(
                OrderPlacement(order_id=3000 + i, price=price, size=0.333, status="success")
            )

        result = ScaleOrderResult(
            scale_order_id="scale_many",
            coin="ETH",
            is_buy=True,
            total_usd_amount=20000.0,
            total_coin_size=6.66,
            num_orders=20,
            placements=placements,
            orders_placed=20,
            orders_failed=0,
            average_price=2900.0,
            total_placed_size=6.66,
            status="completed",
        )
        mock_scale_order_service.place_scale_order.return_value = result

        request = PlaceScaleOrderRequest(config=config)

        response = await use_case.execute(request)

        assert response.result.num_orders == 20
        assert response.result.orders_placed == 20
        assert len(response.result.placements) == 20
