"""
Unit tests for PreviewScaleOrderUseCase.

Tests scale order preview generation logic.
CRITICAL - bugs here = incorrect scale order calculations shown to users.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.use_cases.scale_orders.preview import (
    PreviewScaleOrderRequest,
    PreviewScaleOrderResponse,
    PreviewScaleOrderUseCase
)
from src.models.scale_order import ScaleOrderConfig, ScaleOrderPreview


class TestPreviewScaleOrderUseCase:
    """Test PreviewScaleOrderUseCase."""

    @pytest.fixture
    def mock_scale_order_service(self):
        """Mock ScaleOrderService."""
        mock = Mock()
        mock.preview_scale_order = AsyncMock()
        return mock

    @pytest.fixture
    def use_case(self, mock_scale_order_service):
        """Create PreviewScaleOrderUseCase with mocked dependencies."""
        with patch('src.use_cases.scale_orders.preview.scale_order_service', mock_scale_order_service):
            uc = PreviewScaleOrderUseCase()
            uc.scale_order_service = mock_scale_order_service
            return uc

    @pytest.fixture
    def sample_buy_config(self):
        """Sample BUY scale order config."""
        return ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            num_orders=5,
            start_price=50000.0,
            end_price=48000.0,
            distribution_type="linear",
            time_in_force="Gtc"
        )

    @pytest.fixture
    def sample_sell_config(self):
        """Sample SELL scale order config."""
        return ScaleOrderConfig(
            coin="ETH",
            is_buy=False,
            total_usd_amount=5000.0,
            num_orders=3,
            start_price=3000.0,
            end_price=3300.0,
            distribution_type="linear",
            time_in_force="Gtc"
        )

    # ===================================================================
    # Basic Preview tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_preview_buy_scale_order_success(
        self, use_case, mock_scale_order_service, sample_buy_config
    ):
        """Test preview BUY scale order success."""
        # Mock service response
        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            orders=[
                {"price": 50000.0, "size": 0.040, "notional": 2000.0},
                {"price": 49500.0, "size": 0.040, "notional": 1980.0},
                {"price": 49000.0, "size": 0.041, "notional": 2009.0},
                {"price": 48500.0, "size": 0.041, "notional": 1988.5},
                {"price": 48000.0, "size": 0.042, "notional": 2016.0}
            ],
            estimated_avg_price=49000.0,
            price_range_pct=4.0
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=sample_buy_config)

        response = await use_case.execute(request)

        # Verify service called correctly
        mock_scale_order_service.preview_scale_order.assert_called_once_with(sample_buy_config)

        # Verify response
        assert response.preview.coin == "BTC"
        assert response.preview.is_buy is True
        assert response.preview.total_usd_amount == 10000.0
        assert response.preview.total_coin_size == 0.204
        assert response.preview.num_orders == 5
        assert len(response.preview.orders) == 5
        assert response.preview.estimated_avg_price == 49000.0
        assert response.preview.price_range_pct == 4.0

    @pytest.mark.asyncio
    async def test_preview_sell_scale_order_success(
        self, use_case, mock_scale_order_service, sample_sell_config
    ):
        """Test preview SELL scale order success."""
        preview = ScaleOrderPreview(
            coin="ETH",
            is_buy=False,
            total_usd_amount=5000.0,
            total_coin_size=1.6,
            num_orders=3,
            orders=[
                {"price": 3000.0, "size": 0.533, "notional": 1599.0},
                {"price": 3150.0, "size": 0.533, "notional": 1678.95},
                {"price": 3300.0, "size": 0.534, "notional": 1762.2}
            ],
            estimated_avg_price=3150.0,
            price_range_pct=9.5
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=sample_sell_config)

        response = await use_case.execute(request)

        assert response.preview.coin == "ETH"
        assert response.preview.is_buy is False
        assert response.preview.num_orders == 3
        assert response.preview.estimated_avg_price == 3150.0

    # ===================================================================
    # Distribution Type tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_preview_linear_distribution(
        self, use_case, mock_scale_order_service
    ):
        """Test preview with linear distribution (equal sizes)."""
        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=5000.0,
            num_orders=5,
            start_price=50000.0,
            end_price=48000.0,
            distribution_type="linear"
        )

        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=5000.0,
            total_coin_size=0.102,
            num_orders=5,
            orders=[
                {"price": 50000.0, "size": 0.020, "notional": 1000.0},
                {"price": 49500.0, "size": 0.020, "notional": 990.0},
                {"price": 49000.0, "size": 0.020, "notional": 980.0},
                {"price": 48500.0, "size": 0.021, "notional": 1018.5},
                {"price": 48000.0, "size": 0.021, "notional": 1008.0}
            ],
            estimated_avg_price=49000.0,
            price_range_pct=4.0
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=config)

        response = await use_case.execute(request)

        # Verify all orders have similar sizes (linear)
        sizes = [order["size"] for order in response.preview.orders]
        assert all(0.019 <= size <= 0.022 for size in sizes)

    @pytest.mark.asyncio
    async def test_preview_geometric_distribution(
        self, use_case, mock_scale_order_service
    ):
        """Test preview with geometric distribution (weighted sizes)."""
        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=5000.0,
            num_orders=5,
            start_price=50000.0,
            end_price=48000.0,
            distribution_type="geometric",
            geometric_ratio=1.5
        )

        # Geometric distribution: sizes increase by ratio
        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=5000.0,
            total_coin_size=0.110,
            num_orders=5,
            orders=[
                {"price": 50000.0, "size": 0.010, "notional": 500.0},
                {"price": 49500.0, "size": 0.015, "notional": 742.5},
                {"price": 49000.0, "size": 0.023, "notional": 1127.0},
                {"price": 48500.0, "size": 0.034, "notional": 1649.0},
                {"price": 48000.0, "size": 0.051, "notional": 2448.0}
            ],
            estimated_avg_price=48500.0,
            price_range_pct=4.0
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=config)

        response = await use_case.execute(request)

        # Verify sizes increase geometrically
        sizes = [order["size"] for order in response.preview.orders]
        assert sizes[0] < sizes[1] < sizes[2] < sizes[3] < sizes[4]

    # ===================================================================
    # Order Count tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_preview_minimum_orders(
        self, use_case, mock_scale_order_service
    ):
        """Test preview with minimum orders (2)."""
        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=1000.0,
            num_orders=2,
            start_price=50000.0,
            end_price=49000.0
        )

        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=1000.0,
            total_coin_size=0.0204,
            num_orders=2,
            orders=[
                {"price": 50000.0, "size": 0.010, "notional": 500.0},
                {"price": 49000.0, "size": 0.0104, "notional": 509.6}
            ],
            estimated_avg_price=49500.0,
            price_range_pct=2.0
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=config)

        response = await use_case.execute(request)

        assert response.preview.num_orders == 2
        assert len(response.preview.orders) == 2

    @pytest.mark.asyncio
    async def test_preview_many_orders(
        self, use_case, mock_scale_order_service
    ):
        """Test preview with many orders (20)."""
        config = ScaleOrderConfig(
            coin="ETH",
            is_buy=True,
            total_usd_amount=20000.0,
            num_orders=20,
            start_price=3000.0,
            end_price=2800.0
        )

        # Generate 20 orders
        orders = []
        for i in range(20):
            price = 3000.0 - (i * 10.5)  # Roughly linear
            orders.append({"price": price, "size": 0.333, "notional": 1000.0})

        preview = ScaleOrderPreview(
            coin="ETH",
            is_buy=True,
            total_usd_amount=20000.0,
            total_coin_size=6.66,
            num_orders=20,
            orders=orders,
            estimated_avg_price=2900.0,
            price_range_pct=6.9
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=config)

        response = await use_case.execute(request)

        assert response.preview.num_orders == 20
        assert len(response.preview.orders) == 20

    # ===================================================================
    # Price Metrics tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_preview_estimated_avg_price(
        self, use_case, mock_scale_order_service, sample_buy_config
    ):
        """Test estimated average price calculation."""
        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            orders=[
                {"price": 50000.0, "size": 0.040, "notional": 2000.0},
                {"price": 49500.0, "size": 0.040, "notional": 1980.0},
                {"price": 49000.0, "size": 0.041, "notional": 2009.0},
                {"price": 48500.0, "size": 0.041, "notional": 1988.5},
                {"price": 48000.0, "size": 0.042, "notional": 2016.0}
            ],
            estimated_avg_price=49000.0,  # Weighted average
            price_range_pct=4.0
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=sample_buy_config)

        response = await use_case.execute(request)

        # Estimated avg should be between start and end
        assert 48000.0 <= response.preview.estimated_avg_price <= 50000.0
        assert response.preview.estimated_avg_price == 49000.0

    @pytest.mark.asyncio
    async def test_preview_price_range_percentage(
        self, use_case, mock_scale_order_service, sample_buy_config
    ):
        """Test price range percentage calculation."""
        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            orders=[
                {"price": 50000.0, "size": 0.040, "notional": 2000.0},
                {"price": 49500.0, "size": 0.040, "notional": 1980.0},
                {"price": 49000.0, "size": 0.041, "notional": 2009.0},
                {"price": 48500.0, "size": 0.041, "notional": 1988.5},
                {"price": 48000.0, "size": 0.042, "notional": 2016.0}
            ],
            estimated_avg_price=49000.0,
            price_range_pct=4.0  # (50000-48000)/50000 * 100
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=sample_buy_config)

        response = await use_case.execute(request)

        assert response.preview.price_range_pct == 4.0

    # ===================================================================
    # Order Detail tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_preview_order_fields_complete(
        self, use_case, mock_scale_order_service, sample_buy_config
    ):
        """Test each order has complete fields."""
        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            orders=[
                {"price": 50000.0, "size": 0.040, "notional": 2000.0},
                {"price": 49500.0, "size": 0.040, "notional": 1980.0},
                {"price": 49000.0, "size": 0.041, "notional": 2009.0},
                {"price": 48500.0, "size": 0.041, "notional": 1988.5},
                {"price": 48000.0, "size": 0.042, "notional": 2016.0}
            ],
            estimated_avg_price=49000.0,
            price_range_pct=4.0
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=sample_buy_config)

        response = await use_case.execute(request)

        # Verify all orders have required fields
        for order in response.preview.orders:
            assert "price" in order
            assert "size" in order
            assert "notional" in order
            assert order["price"] > 0
            assert order["size"] > 0
            assert order["notional"] > 0

    @pytest.mark.asyncio
    async def test_preview_total_notional_matches_usd_amount(
        self, use_case, mock_scale_order_service, sample_buy_config
    ):
        """Test sum of notional values approximately equals total USD amount."""
        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.204,
            num_orders=5,
            orders=[
                {"price": 50000.0, "size": 0.040, "notional": 2000.0},
                {"price": 49500.0, "size": 0.040, "notional": 1980.0},
                {"price": 49000.0, "size": 0.041, "notional": 2009.0},
                {"price": 48500.0, "size": 0.041, "notional": 1988.5},
                {"price": 48000.0, "size": 0.042, "notional": 2016.0}
            ],
            estimated_avg_price=49000.0,
            price_range_pct=4.0
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=sample_buy_config)

        response = await use_case.execute(request)

        total_notional = sum(order["notional"] for order in response.preview.orders)
        # Should be close to 10000 (within 1%)
        assert 9900.0 <= total_notional <= 10100.0

    # ===================================================================
    # Validation Error tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_invalid_config_raises_value_error(
        self, use_case, mock_scale_order_service
    ):
        """Test invalid configuration raises ValueError."""
        mock_scale_order_service.preview_scale_order.side_effect = ValueError(
            "num_orders must be between 2 and 20"
        )

        # Invalid config (num_orders = 1, which fails Pydantic validation before service call)
        # So let's test a service-level validation error
        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            num_orders=5,
            start_price=50000.0,
            end_price=48000.0
        )

        request = PreviewScaleOrderRequest(config=config)

        with pytest.raises(ValueError, match="num_orders must be between 2 and 20"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_service_failure_raises_runtime_error(
        self, use_case, mock_scale_order_service, sample_buy_config
    ):
        """Test service failure raises RuntimeError."""
        mock_scale_order_service.preview_scale_order.side_effect = Exception("API Error")

        request = PreviewScaleOrderRequest(config=sample_buy_config)

        with pytest.raises(RuntimeError, match="Failed to generate preview"):
            await use_case.execute(request)

    # ===================================================================
    # Edge Case tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_preview_small_usd_amount(
        self, use_case, mock_scale_order_service
    ):
        """Test preview with small USD amount."""
        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=100.0,  # Small amount
            num_orders=2,
            start_price=50000.0,
            end_price=49000.0
        )

        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=100.0,
            total_coin_size=0.00204,
            num_orders=2,
            orders=[
                {"price": 50000.0, "size": 0.001, "notional": 50.0},
                {"price": 49000.0, "size": 0.00104, "notional": 50.96}
            ],
            estimated_avg_price=49500.0,
            price_range_pct=2.0
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=config)

        response = await use_case.execute(request)

        assert response.preview.total_usd_amount == 100.0
        assert response.preview.total_coin_size < 0.01

    @pytest.mark.asyncio
    async def test_preview_large_usd_amount(
        self, use_case, mock_scale_order_service
    ):
        """Test preview with large USD amount."""
        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=1000000.0,  # $1M
            num_orders=10,
            start_price=50000.0,
            end_price=45000.0
        )

        # Generate 10 orders
        orders = []
        for i in range(10):
            price = 50000.0 - (i * 555.56)
            size = 2.0
            orders.append({"price": price, "size": size, "notional": 100000.0})

        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=1000000.0,
            total_coin_size=20.0,
            num_orders=10,
            orders=orders,
            estimated_avg_price=47500.0,
            price_range_pct=10.0
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=config)

        response = await use_case.execute(request)

        assert response.preview.total_usd_amount == 1000000.0
        assert response.preview.num_orders == 10

    @pytest.mark.asyncio
    async def test_preview_narrow_price_range(
        self, use_case, mock_scale_order_service
    ):
        """Test preview with narrow price range."""
        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            num_orders=5,
            start_price=50000.0,
            end_price=49900.0  # Only 0.2% range
        )

        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.2004,
            num_orders=5,
            orders=[
                {"price": 50000.0, "size": 0.040, "notional": 2000.0},
                {"price": 49975.0, "size": 0.040, "notional": 1999.0},
                {"price": 49950.0, "size": 0.040, "notional": 1998.0},
                {"price": 49925.0, "size": 0.040, "notional": 1997.0},
                {"price": 49900.0, "size": 0.040, "notional": 1996.0}
            ],
            estimated_avg_price=49950.0,
            price_range_pct=0.2
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=config)

        response = await use_case.execute(request)

        assert response.preview.price_range_pct == 0.2

    @pytest.mark.asyncio
    async def test_preview_wide_price_range(
        self, use_case, mock_scale_order_service
    ):
        """Test preview with wide price range."""
        config = ScaleOrderConfig(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            num_orders=5,
            start_price=50000.0,
            end_price=40000.0  # 20% range
        )

        preview = ScaleOrderPreview(
            coin="BTC",
            is_buy=True,
            total_usd_amount=10000.0,
            total_coin_size=0.222,
            num_orders=5,
            orders=[
                {"price": 50000.0, "size": 0.040, "notional": 2000.0},
                {"price": 47500.0, "size": 0.042, "notional": 1995.0},
                {"price": 45000.0, "size": 0.044, "notional": 1980.0},
                {"price": 42500.0, "size": 0.047, "notional": 1997.5},
                {"price": 40000.0, "size": 0.050, "notional": 2000.0}
            ],
            estimated_avg_price=45000.0,
            price_range_pct=20.0
        )
        mock_scale_order_service.preview_scale_order.return_value = preview

        request = PreviewScaleOrderRequest(config=config)

        response = await use_case.execute(request)

        assert response.preview.price_range_pct == 20.0
