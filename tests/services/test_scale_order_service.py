"""
Unit tests for ScaleOrderService.

Tests scale order calculation logic, order placement, cancellation,
and status tracking. CRITICAL - bugs here = incorrect trade execution.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from src.services.scale_order_service import ScaleOrderService, scale_order_service
from src.models.scale_order import (
    ScaleOrderConfig,
    ScaleOrderCancel,
    ScaleOrder,
)
from tests.helpers.service_mocks import create_service_with_mocks, ServiceMockBuilder


class TestScaleOrderServiceCalculations:
    """Test calculation helper methods."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return ScaleOrderService()

    # ===================================================================
    # Price Level Calculations
    # ===================================================================

    def test_calculate_price_levels_single_order(self, service):
        """Test price calculation for single order."""
        levels = service._calculate_price_levels(
            start_price=50000.0,
            end_price=48000.0,
            num_orders=1
        )

        assert len(levels) == 1
        assert levels[0] == 50000.0

    def test_calculate_price_levels_linear_distribution(self, service):
        """Test linear price distribution."""
        levels = service._calculate_price_levels(
            start_price=50000.0,
            end_price=48000.0,
            num_orders=5
        )

        assert len(levels) == 5
        assert levels[0] == 50000.0
        assert levels[-1] == 48000.0
        # Check spacing is even (500 per level)
        assert levels[1] == 49500.0
        assert levels[2] == 49000.0
        assert levels[3] == 48500.0

    def test_calculate_price_levels_buy_ascending(self, service):
        """Test price levels for buy orders (ascending prices)."""
        levels = service._calculate_price_levels(
            start_price=48000.0,
            end_price=50000.0,
            num_orders=3
        )

        assert levels[0] == 48000.0
        assert levels[1] == 49000.0
        assert levels[2] == 50000.0

    # ===================================================================
    # Linear Size Calculations
    # ===================================================================

    def test_calculate_linear_sizes_equal_usd(self, service):
        """Test linear distribution gives equal USD per order."""
        price_levels = [50000.0, 49000.0, 48000.0]
        sizes = service._calculate_linear_sizes(
            total_usd_amount=30000.0,
            price_levels=price_levels,
            num_orders=3
        )

        assert len(sizes) == 3
        # Each order should be $10,000 worth
        assert sizes[0] * price_levels[0] == pytest.approx(10000.0)
        assert sizes[1] * price_levels[1] == pytest.approx(10000.0)
        assert sizes[2] * price_levels[2] == pytest.approx(10000.0)

    def test_calculate_linear_sizes_total_usd_correct(self, service):
        """Test total USD amount is correct with linear distribution."""
        price_levels = [50000.0, 49500.0, 49000.0, 48500.0, 48000.0]
        sizes = service._calculate_linear_sizes(
            total_usd_amount=50000.0,
            price_levels=price_levels,
            num_orders=5
        )

        total_usd = sum(size * price for size, price in zip(sizes, price_levels))
        assert total_usd == pytest.approx(50000.0)

    # ===================================================================
    # Geometric Size Calculations
    # ===================================================================

    def test_calculate_geometric_sizes_single_order(self, service):
        """Test geometric calculation for single order."""
        sizes = service._calculate_geometric_sizes(
            total_usd_amount=10000.0,
            price_levels=[50000.0],
            num_orders=1,
            ratio=1.5
        )

        assert len(sizes) == 1
        assert sizes[0] == pytest.approx(10000.0 / 50000.0)

    def test_calculate_geometric_sizes_weighted_distribution(self, service):
        """Test geometric distribution weights USD towards first orders."""
        price_levels = [50000.0, 49000.0, 48000.0]
        sizes = service._calculate_geometric_sizes(
            total_usd_amount=30000.0,
            price_levels=price_levels,
            num_orders=3,
            ratio=1.5
        )

        # Calculate USD amounts
        usd_amounts = [size * price for size, price in zip(sizes, price_levels)]

        # First order should have less USD than second (ratio 1.5)
        assert usd_amounts[0] < usd_amounts[1]
        assert usd_amounts[1] < usd_amounts[2]
        # Ratio should be approximately 1.5
        assert usd_amounts[1] / usd_amounts[0] == pytest.approx(1.5, rel=0.01)
        assert usd_amounts[2] / usd_amounts[1] == pytest.approx(1.5, rel=0.01)

    def test_calculate_geometric_sizes_total_usd_exact(self, service):
        """Test total USD is exact after adjustment for floating point errors."""
        price_levels = [50000.0, 49500.0, 49000.0, 48500.0, 48000.0]
        sizes = service._calculate_geometric_sizes(
            total_usd_amount=50000.0,
            price_levels=price_levels,
            num_orders=5,
            ratio=1.5
        )

        total_usd = sum(size * price for size, price in zip(sizes, price_levels))
        # Should be exact due to adjustment logic
        assert total_usd == pytest.approx(50000.0, abs=0.01)

    def test_calculate_geometric_sizes_different_ratios(self, service):
        """Test geometric distribution with different ratios."""
        price_levels = [50000.0, 49000.0, 48000.0]

        # Test ratio 2.0 (more aggressive)
        sizes = service._calculate_geometric_sizes(
            total_usd_amount=30000.0,
            price_levels=price_levels,
            num_orders=3,
            ratio=2.0
        )
        usd_amounts = [size * price for size, price in zip(sizes, price_levels)]
        assert usd_amounts[1] / usd_amounts[0] == pytest.approx(2.0, rel=0.01)

    # ===================================================================
    # Rounding Methods
    # ===================================================================

    def test_round_price_default_tick(self, service):
        """Test price rounding with default 0.01 tick."""
        assert service._round_price(50000.123) == pytest.approx(50000.12)
        assert service._round_price(49999.999) == pytest.approx(50000.00)
        # Banker's rounding: .005 rounds to nearest even (48500.0 not 48500.01)
        assert service._round_price(48500.005) == pytest.approx(48500.00)
        assert service._round_price(48500.015) == pytest.approx(48500.02)

    def test_round_price_custom_tick(self, service):
        """Test price rounding with custom tick size."""
        assert service._round_price(50000.12, tick_size=0.1) == pytest.approx(50000.1)
        assert service._round_price(50000.15, tick_size=0.5) == pytest.approx(50000.0, abs=0.5)
        assert service._round_price(50000.3, tick_size=0.5) == pytest.approx(50000.5)

    def test_round_size_default_decimals(self, service):
        """Test size rounding with default 4 decimals."""
        assert service._round_size(0.123456) == 0.1235
        assert service._round_size(1.999999) == 2.0
        assert service._round_size(0.000001) == 0.0

    def test_round_size_custom_decimals(self, service):
        """Test size rounding with custom decimals."""
        assert service._round_size(0.123456, size_decimals=2) == 0.12
        assert service._round_size(0.123456, size_decimals=6) == 0.123456
        assert service._round_size(1.5, size_decimals=0) == 2.0


class TestScaleOrderServicePreview:
    """Test preview_scale_order method."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return ScaleOrderService()

    @pytest.fixture
    def linear_config(self):
        """Sample linear distribution config."""
        return ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            num_orders=5,
            start_price=50000.0,
            end_price=48000.0,
            distribution_type="linear"
        )

    @pytest.fixture
    def geometric_config(self):
        """Sample geometric distribution config."""
        return ScaleOrderConfig(
            coin="ETH",
            is_buy=False,
            total_usd_amount=20000.0,
            num_orders=4,
            start_price=3000.0,
            end_price=3300.0,
            distribution_type="geometric",
            geometric_ratio=1.5
        )

    @pytest.mark.asyncio
    async def test_preview_linear_structure(self, service, linear_config):
        """Test preview returns correct structure for linear distribution."""
        preview = await service.preview_scale_order(linear_config)

        assert preview.coin == "BTC"
        assert preview.is_buy is True
        assert preview.total_usd_amount == 10000.0
        assert preview.num_orders == 5
        assert len(preview.orders) == 5

    @pytest.mark.asyncio
    async def test_preview_geometric_structure(self, service, geometric_config):
        """Test preview returns correct structure for geometric distribution."""
        preview = await service.preview_scale_order(geometric_config)

        assert preview.coin == "ETH"
        assert preview.is_buy is False
        assert preview.num_orders == 4
        assert len(preview.orders) == 4

    @pytest.mark.asyncio
    async def test_preview_price_range_percentage(self, service, linear_config):
        """Test price range percentage calculation."""
        preview = await service.preview_scale_order(linear_config)

        # Range: 48000 to 50000 = 2000
        # Percentage: 2000 / 50000 * 100 = 4%
        assert preview.price_range_pct == pytest.approx(4.0)

    @pytest.mark.asyncio
    async def test_preview_estimated_avg_price(self, service, linear_config):
        """Test estimated average price calculation."""
        preview = await service.preview_scale_order(linear_config)

        # With linear distribution, avg should be close to midpoint
        # Midpoint = (50000 + 48000) / 2 = 49000
        # Actual avg will be slightly different due to equal USD per order
        assert 48500 < preview.estimated_avg_price < 49500


class TestScaleOrderServicePlacement:
    """Test place_scale_order method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked hyperliquid."""
        mock_hyperliquid = ServiceMockBuilder.hyperliquid_service()
        mock_hyperliquid.is_initialized = Mock(return_value=True)
        mock_hyperliquid.initialize = AsyncMock()
        mock_hyperliquid.place_limit_order = AsyncMock()

        return create_service_with_mocks(
            ScaleOrderService,
            'src.services.scale_order_service',
            {'hyperliquid_service': mock_hyperliquid}
        )

    @pytest.fixture
    def sample_config(self):
        """Sample scale order config."""
        return ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            num_orders=3,
            start_price=50000.0,
            end_price=48000.0,
            distribution_type="linear"
        )

    @pytest.mark.asyncio
    async def test_place_initializes_hyperliquid_if_needed(self, service, sample_config):
        """Test service initializes hyperliquid if not initialized."""
        service.hyperliquid.is_initialized.return_value = False
        service.hyperliquid.place_limit_order.return_value = {
            "status": "ok",
            "response": {"data": {"statuses": [{"resting": {"oid": 1001}}]}}
        }

        await service.place_scale_order(sample_config)

        service.hyperliquid.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_place_all_orders_success(self, service, sample_config):
        """Test placing all orders successfully."""
        service.hyperliquid.place_limit_order.return_value = {
            "status": "ok",
            "response": {"data": {"statuses": [{"resting": {"oid": 1001}}]}}
        }

        result = await service.place_scale_order(sample_config)

        assert result.orders_placed == 3
        assert result.orders_failed == 0
        assert result.status == "completed"
        assert len(result.placements) == 3
        assert service.hyperliquid.place_limit_order.call_count == 3

    @pytest.mark.asyncio
    async def test_place_stores_scale_order(self, service, sample_config):
        """Test scale order is stored after placement."""
        service.hyperliquid.place_limit_order.return_value = {
            "status": "ok",
            "response": {"data": {"statuses": [{"resting": {"oid": 1001}}]}}
        }

        result = await service.place_scale_order(sample_config)

        # Verify stored in _scale_orders
        stored = service.get_scale_order(result.scale_order_id)
        assert stored is not None
        assert stored.coin == "BTC"
        assert stored.num_orders == 3
        assert len(stored.order_ids) == 3

    @pytest.mark.asyncio
    async def test_place_partial_success(self, service, sample_config):
        """Test partial placement when some orders fail."""
        # First order succeeds, second fails, third succeeds
        service.hyperliquid.place_limit_order.side_effect = [
            {"status": "ok", "response": {"data": {"statuses": [{"resting": {"oid": 1001}}]}}},
            {"status": "error", "response": {"message": "Insufficient margin"}},
            {"status": "ok", "response": {"data": {"statuses": [{"resting": {"oid": 1003}}]}}}
        ]

        result = await service.place_scale_order(sample_config)

        assert result.orders_placed == 2
        assert result.orders_failed == 1
        assert result.status == "partial"
        assert result.placements[1].status == "failed"
        assert result.placements[1].error == "Insufficient margin"

    @pytest.mark.asyncio
    async def test_place_all_failed(self, service, sample_config):
        """Test all orders failing."""
        service.hyperliquid.place_limit_order.return_value = {
            "status": "error",
            "response": {"message": "Order rejected"}
        }

        result = await service.place_scale_order(sample_config)

        assert result.orders_placed == 0
        assert result.orders_failed == 3
        assert result.status == "failed"
        assert result.average_price is None

    @pytest.mark.asyncio
    async def test_place_calculates_average_price(self, service, sample_config):
        """Test average price calculation for placed orders."""
        service.hyperliquid.place_limit_order.return_value = {
            "status": "ok",
            "response": {"data": {"statuses": [{"resting": {"oid": 1001}}]}}
        }

        result = await service.place_scale_order(sample_config)

        # Average price should be calculated from successful orders
        assert result.average_price is not None
        assert 48000 < result.average_price < 50000


class TestScaleOrderServiceCancellation:
    """Test cancel_scale_order method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked hyperliquid and sample orders."""
        mock_hyperliquid = ServiceMockBuilder.hyperliquid_service()
        mock_hyperliquid.cancel_order = AsyncMock()

        svc = create_service_with_mocks(
            ScaleOrderService,
            'src.services.scale_order_service',
            {'hyperliquid_service': mock_hyperliquid}
        )

        # Add a sample scale order to storage
        scale_order = ScaleOrder(
            id="scale_123",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.2,
            num_orders=3,
            start_price=50000.0,
            end_price=48000.0,
            distribution_type="linear",
            order_ids=[1001, 1002, 1003],
            orders_placed=3,
            status="active"
        )
        svc._scale_orders["scale_123"] = scale_order

        return svc

    @pytest.mark.asyncio
    async def test_cancel_not_found_raises_value_error(self, service):
        """Test cancelling non-existent scale order raises ValueError."""
        cancel_request = ScaleOrderCancel(
            scale_order_id="nonexistent",
            cancel_all_orders=True
        )

        with pytest.raises(ValueError, match="Scale order nonexistent not found"):
            await service.cancel_scale_order(cancel_request)

    @pytest.mark.asyncio
    async def test_cancel_without_cancelling_orders(self, service):
        """Test cancel_all_orders=False just marks as cancelled."""
        cancel_request = ScaleOrderCancel(
            scale_order_id="scale_123",
            cancel_all_orders=False
        )

        result = await service.cancel_scale_order(cancel_request)

        assert result["scale_order_id"] == "scale_123"
        assert result["orders_cancelled"] == 0
        assert result["status"] == "cancelled"
        # Verify scale order marked as cancelled
        assert service._scale_orders["scale_123"].status == "cancelled"
        # Verify no cancel_order calls made
        service.hyperliquid.cancel_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_cancel_all_orders_success(self, service):
        """Test cancelling all orders successfully."""
        service.hyperliquid.cancel_order.return_value = {"status": "ok"}

        cancel_request = ScaleOrderCancel(
            scale_order_id="scale_123",
            cancel_all_orders=True
        )

        result = await service.cancel_scale_order(cancel_request)

        assert result["orders_cancelled"] == 3
        assert result["total_orders"] == 3
        assert result["errors"] is None
        assert result["status"] == "cancelled"
        assert service.hyperliquid.cancel_order.call_count == 3

    @pytest.mark.asyncio
    async def test_cancel_partial_failure(self, service):
        """Test partial cancellation when some orders fail."""
        # First succeeds, second fails, third succeeds
        service.hyperliquid.cancel_order.side_effect = [
            {"status": "ok"},
            {"status": "error", "response": {"message": "Order already filled"}},
            {"status": "ok"}
        ]

        cancel_request = ScaleOrderCancel(
            scale_order_id="scale_123",
            cancel_all_orders=True
        )

        result = await service.cancel_scale_order(cancel_request)

        assert result["orders_cancelled"] == 2
        assert result["total_orders"] == 3
        assert len(result["errors"]) == 1
        assert "1002" in result["errors"][0]
        assert "already filled" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_cancel_handles_exceptions(self, service):
        """Test cancel handles exceptions gracefully."""
        service.hyperliquid.cancel_order.side_effect = Exception("Network error")

        cancel_request = ScaleOrderCancel(
            scale_order_id="scale_123",
            cancel_all_orders=True
        )

        result = await service.cancel_scale_order(cancel_request)

        assert result["orders_cancelled"] == 0
        assert len(result["errors"]) == 3
        assert all("Network error" in e for e in result["errors"])


class TestScaleOrderServiceStatus:
    """Test get_scale_order_status method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked hyperliquid and sample order."""
        mock_hyperliquid = ServiceMockBuilder.hyperliquid_service()
        mock_hyperliquid.get_open_orders = AsyncMock()

        svc = create_service_with_mocks(
            ScaleOrderService,
            'src.services.scale_order_service',
            {'hyperliquid_service': mock_hyperliquid}
        )

        # Add a sample scale order
        scale_order = ScaleOrder(
            id="scale_123",
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.2,
            num_orders=5,
            start_price=50000.0,
            end_price=48000.0,
            distribution_type="linear",
            order_ids=[1001, 1002, 1003, 1004, 1005],
            orders_placed=5,
            status="active"
        )
        svc._scale_orders["scale_123"] = scale_order

        return svc

    @pytest.mark.asyncio
    async def test_get_status_not_found_raises_value_error(self, service):
        """Test getting status for non-existent order raises ValueError."""
        with pytest.raises(ValueError, match="Scale order nonexistent not found"):
            await service.get_scale_order_status("nonexistent")

    @pytest.mark.asyncio
    async def test_get_status_all_open(self, service):
        """Test status when all orders still open."""
        service.hyperliquid.get_open_orders.return_value = [
            {"oid": 1001, "coin": "BTC"},
            {"oid": 1002, "coin": "BTC"},
            {"oid": 1003, "coin": "BTC"},
            {"oid": 1004, "coin": "BTC"},
            {"oid": 1005, "coin": "BTC"}
        ]

        status = await service.get_scale_order_status("scale_123")

        assert len(status.open_orders) == 5
        assert len(status.filled_orders) == 0
        assert status.fill_percentage == 0.0
        assert status.scale_order.status == "active"

    @pytest.mark.asyncio
    async def test_get_status_partial_filled(self, service):
        """Test status when some orders filled."""
        # Only 3 orders still open (2 filled)
        service.hyperliquid.get_open_orders.return_value = [
            {"oid": 1001, "coin": "BTC"},
            {"oid": 1003, "coin": "BTC"},
            {"oid": 1005, "coin": "BTC"}
        ]

        status = await service.get_scale_order_status("scale_123")

        assert len(status.open_orders) == 3
        assert len(status.filled_orders) == 2
        assert status.fill_percentage == pytest.approx(40.0)  # 2/5 = 40%
        assert status.scale_order.orders_filled == 2

    @pytest.mark.asyncio
    async def test_get_status_all_filled_updates_status(self, service):
        """Test status updates to completed when all orders filled."""
        # No orders open (all filled)
        service.hyperliquid.get_open_orders.return_value = []

        status = await service.get_scale_order_status("scale_123")

        assert len(status.open_orders) == 0
        assert len(status.filled_orders) == 5
        assert status.fill_percentage == 100.0
        # Status should update to completed
        assert status.scale_order.status == "completed"
        assert status.scale_order.completed_at is not None


class TestScaleOrderServiceListAndGet:
    """Test list_scale_orders and get_scale_order methods."""

    @pytest.fixture
    def service(self):
        """Create service with sample orders."""
        svc = ScaleOrderService()

        # Add multiple scale orders
        for i in range(3):
            scale_order = ScaleOrder(
                id=f"scale_{i}",
                coin="BTC" if i % 2 == 0 else "ETH",
                is_buy=True,
                total_usd_amount=10000.0 * (i + 1),
                total_coin_size=0.2 * (i + 1),
                num_orders=5,
                start_price=50000.0,
                end_price=48000.0,
                distribution_type="linear",
                order_ids=[1000 + i, 2000 + i],
                orders_placed=5,
                status="active"
            )
            svc._scale_orders[f"scale_{i}"] = scale_order

        return svc

    def test_list_scale_orders_returns_all(self, service):
        """Test listing all scale orders."""
        orders = service.list_scale_orders()

        assert len(orders) == 3
        assert all(isinstance(o, ScaleOrder) for o in orders)

    def test_list_scale_orders_empty(self):
        """Test listing when no orders exist."""
        service = ScaleOrderService()
        orders = service.list_scale_orders()

        assert len(orders) == 0

    def test_get_scale_order_found(self, service):
        """Test getting existing scale order."""
        order = service.get_scale_order("scale_1")

        assert order is not None
        assert order.id == "scale_1"
        assert order.coin == "ETH"

    def test_get_scale_order_not_found(self, service):
        """Test getting non-existent order returns None."""
        order = service.get_scale_order("nonexistent")

        assert order is None


class TestScaleOrderServiceSingleton:
    """Test global service singleton."""

    def test_singleton_instance_exists(self):
        """Test global service instance is available."""
        assert scale_order_service is not None
        assert isinstance(scale_order_service, ScaleOrderService)

    def test_singleton_has_hyperliquid_reference(self):
        """Test singleton has hyperliquid service reference."""
        assert hasattr(scale_order_service, 'hyperliquid')
        assert scale_order_service.hyperliquid is not None
