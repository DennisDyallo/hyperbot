"""
Unit tests for PlaceOrderUseCase.

Tests order placement logic that handles actual trading operations.
This is CRITICAL - bugs here = lost money.

REFACTORED: Now using tests/helpers for service mocking.
- create_service_with_mocks replaces manual fixture boilerplate
- ServiceMockBuilder provides pre-configured service mocks
- Result: Cleaner fixtures, consistent with CLAUDE.md patterns
"""
import pytest
from unittest.mock import patch
from src.use_cases.trading.place_order import (
    PlaceOrderRequest,
    PlaceOrderResponse,
    PlaceOrderUseCase
)
from src.use_cases.common.validators import ValidationError

# Import helpers for cleaner service mocking
from tests.helpers import create_service_with_mocks, ServiceMockBuilder


class TestPlaceOrderUseCase:
    """Test PlaceOrderUseCase."""

    @pytest.fixture
    def use_case(self):
        """Create PlaceOrderUseCase with mocked dependencies."""
        return create_service_with_mocks(
            PlaceOrderUseCase,
            'src.use_cases.trading.place_order',
            {
                'order_service': ServiceMockBuilder.order_service(),
                'market_data_service': ServiceMockBuilder.market_data_service()
            }
        )

    # ===================================================================
    # Market Order with USD Amount tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_market_buy_with_usd_amount_success(self, use_case):
        """Test market buy order with USD amount."""
        # Mock USD to coin conversion
        with patch.object(use_case.usd_converter, 'convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (0.02, 50000.0)  # 0.02 BTC at $50k

            use_case.order_service.place_market_order.return_value = {
                "status": "success",
                "price": 50100.0  # Execution price with slippage
            }

            request = PlaceOrderRequest(
                coin="BTC",
                is_buy=True,
                usd_amount=1000.0,
                is_market=True
            )

            response = await use_case.execute(request)

            assert response.status == "success"
            assert response.coin == "BTC"
            assert response.side == "BUY"
            assert response.size == 0.02
            assert response.order_type == "MARKET"
            assert response.price == 50100.0
            assert response.usd_value == pytest.approx(1002.0, abs=0.01)  # 0.02 * 50100

            mock_convert.assert_called_once_with(1000.0, "BTC")
            use_case.order_service.place_market_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_market_sell_with_usd_amount_success(self, use_case):
        """Test market sell order with USD amount."""
        with patch.object(use_case.usd_converter, 'convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (10.0, 3000.0)  # 10 ETH at $3k

            use_case.order_service.place_market_order.return_value = {
                "status": "success",
                "price": 2990.0  # Execution price
            }

            request = PlaceOrderRequest(
                coin="ETH",
                is_buy=False,
                usd_amount=30000.0,
                is_market=True
            )

            response = await use_case.execute(request)

            assert response.status == "success"
            assert response.side == "SELL"
            assert response.size == 10.0
            assert response.price == 2990.0

    # ===================================================================
    # Market Order with Coin Size tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_market_buy_with_coin_size_success(self, use_case):
        """Test market buy order with coin size."""
        use_case.market_data.get_price.return_value = 50000.0
        use_case.order_service.place_market_order.return_value = {
            "status": "success",
            "price": 50050.0
        }

        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=True,
            coin_size=0.5,
            is_market=True
        )

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.size == 0.5
        assert response.usd_value == pytest.approx(25025.0, abs=0.01)  # 0.5 * 50050

        use_case.market_data.get_price.assert_called_once_with("BTC")
        use_case.order_service.place_market_order.assert_called_once_with(
            coin="BTC",
            is_buy=True,
            size=0.5,
            slippage=0.05,
            reduce_only=False
        )

    # ===================================================================
    # Limit Order tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_limit_buy_with_usd_amount_success(self, use_case):
        """Test limit buy order with USD amount."""
        with patch.object(use_case.usd_converter, 'convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (0.02, 50000.0)

            use_case.order_service.place_limit_order.return_value = {
                "status": "success",
                "order_id": 12345
            }

            request = PlaceOrderRequest(
                coin="BTC",
                is_buy=True,
                usd_amount=1000.0,
                is_market=False,
                limit_price=49000.0  # Buy below market
            )

            response = await use_case.execute(request)

            assert response.status == "success"
            assert response.order_type == "LIMIT"
            assert response.price == 49000.0
            assert response.order_id == 12345

            use_case.order_service.place_limit_order.assert_called_once_with(
                coin="BTC",
                is_buy=True,
                size=0.02,
                price=49000.0,
                reduce_only=False,
                time_in_force="Gtc"
            )

    @pytest.mark.asyncio
    async def test_limit_sell_with_coin_size_success(self, use_case):
        """Test limit sell order with coin size."""
        use_case.market_data.get_price.return_value = 3000.0
        use_case.order_service.place_limit_order.return_value = {
            "status": "success",
            "order_id": 99999
        }

        request = PlaceOrderRequest(
            coin="ETH",
            is_buy=False,
            coin_size=10.0,
            is_market=False,
            limit_price=3100.0,  # Sell above market
            time_in_force="Ioc"
        )

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.order_type == "LIMIT"
        assert response.order_id == 99999
        assert response.price == 3100.0

        use_case.order_service.place_limit_order.assert_called_once()
        call_kwargs = use_case.order_service.place_limit_order.call_args.kwargs
        assert call_kwargs["time_in_force"] == "Ioc"

    # ===================================================================
    # Validation Error tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_missing_both_usd_and_coin_size_fails(self, use_case):
        """Test that missing both size parameters fails."""
        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=True,
            is_market=True
        )

        with pytest.raises(ValidationError, match="Must specify either usd_amount or coin_size"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_both_usd_and_coin_size_provided_fails(self, use_case):
        """Test that providing both size parameters fails."""
        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=True,
            usd_amount=1000.0,
            coin_size=0.5,
            is_market=True
        )

        with pytest.raises(ValidationError, match="Specify either usd_amount or coin_size, not both"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_limit_order_missing_limit_price_fails(self, use_case):
        """Test limit order without limit price fails."""
        use_case.market_data.get_price.return_value = 50000.0

        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=True,
            coin_size=0.5,
            is_market=False
            # Missing limit_price!
        )

        with pytest.raises(ValidationError, match="Limit price required"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_invalid_coin_symbol_fails(self, use_case):
        """Test invalid coin symbol fails validation."""
        request = PlaceOrderRequest(
            coin="",  # Empty coin symbol
            is_buy=True,
            usd_amount=1000.0,
            is_market=True
        )

        with pytest.raises(ValidationError, match="cannot be empty"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_zero_coin_size_fails(self, use_case):
        """Test zero coin size fails validation."""
        use_case.market_data.get_price.return_value = 50000.0

        # Pydantic should catch this with gt=0 constraint
        with pytest.raises(Exception):  # Pydantic ValidationError
            request = PlaceOrderRequest(
                coin="BTC",
                is_buy=True,
                coin_size=0.0,
                is_market=True
            )

    # ===================================================================
    # Order Placement Failure tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_market_order_placement_failure(self, use_case):
        """Test market order placement failure raises RuntimeError."""
        with patch.object(use_case.usd_converter, 'convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (0.02, 50000.0)

            use_case.order_service.place_market_order.side_effect = Exception("API Error")

            request = PlaceOrderRequest(
                coin="BTC",
                is_buy=True,
                usd_amount=1000.0,
                is_market=True
            )

            with pytest.raises(RuntimeError, match="Failed to place order"):
                await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_limit_order_placement_failure(self, use_case):
        """Test limit order placement failure raises RuntimeError."""
        with patch.object(use_case.usd_converter, 'convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (0.02, 50000.0)

            use_case.order_service.place_limit_order.side_effect = Exception("Insufficient margin")

            request = PlaceOrderRequest(
                coin="BTC",
                is_buy=True,
                usd_amount=1000.0,
                is_market=False,
                limit_price=49000.0
            )

            with pytest.raises(RuntimeError, match="Failed to place order"):
                await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_usd_conversion_failure(self, use_case):
        """Test USD to coin conversion failure."""
        with patch.object(use_case.usd_converter, 'convert_usd_to_coin') as mock_convert:
            mock_convert.side_effect = ValueError("Coin not found")

            request = PlaceOrderRequest(
                coin="INVALID",
                is_buy=True,
                usd_amount=1000.0,
                is_market=True
            )

            with pytest.raises(RuntimeError, match="Failed to place order"):
                await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_invalid_price_for_coin_size_fails(self, use_case):
        """Test that invalid price from market data fails."""
        use_case.market_data.get_price.return_value = 0.0  # Invalid price

        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=True,
            coin_size=0.5,
            is_market=True
        )

        with pytest.raises(RuntimeError, match="Failed to place order"):
            await use_case.execute(request)

    # ===================================================================
    # Additional Parameter tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_reduce_only_flag_passed_to_service(self, use_case):
        """Test reduce_only flag is passed to order service."""
        use_case.market_data.get_price.return_value = 50000.0
        use_case.order_service.place_market_order.return_value = {
            "status": "success",
            "price": 50000.0
        }

        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=False,
            coin_size=0.5,
            is_market=True,
            reduce_only=True  # Reduce-only flag
        )

        await use_case.execute(request)

        call_kwargs = use_case.order_service.place_market_order.call_args.kwargs
        assert call_kwargs["reduce_only"] is True

    @pytest.mark.asyncio
    async def test_custom_slippage_passed_to_service(self, use_case):
        """Test custom slippage is passed to order service."""
        use_case.market_data.get_price.return_value = 50000.0
        use_case.order_service.place_market_order.return_value = {
            "status": "success",
            "price": 50000.0
        }

        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=True,
            coin_size=0.5,
            is_market=True,
            slippage=0.10  # 10% slippage
        )

        await use_case.execute(request)

        call_kwargs = use_case.order_service.place_market_order.call_args.kwargs
        assert call_kwargs["slippage"] == 0.10

    @pytest.mark.asyncio
    async def test_custom_time_in_force_passed_to_limit_order(self, use_case):
        """Test custom time_in_force is passed to limit order."""
        with patch.object(use_case.usd_converter, 'convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (0.02, 50000.0)
            use_case.order_service.place_limit_order.return_value = {
                "status": "success",
                "order_id": 12345
            }

            request = PlaceOrderRequest(
                coin="BTC",
                is_buy=True,
                usd_amount=1000.0,
                is_market=False,
                limit_price=49000.0,
                time_in_force="Alo"  # ALO time-in-force
            )

            await use_case.execute(request)

            call_kwargs = use_case.order_service.place_limit_order.call_args.kwargs
            assert call_kwargs["time_in_force"] == "Alo"

    # ===================================================================
    # Response Building tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_response_includes_all_fields(self, use_case):
        """Test response includes all expected fields."""
        use_case.market_data.get_price.return_value = 50000.0
        use_case.order_service.place_market_order.return_value = {
            "status": "success",
            "price": 50100.0
        }

        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=True,
            coin_size=0.5,
            is_market=True
        )

        response = await use_case.execute(request)

        # Verify all fields are present
        assert hasattr(response, 'status')
        assert hasattr(response, 'coin')
        assert hasattr(response, 'side')
        assert hasattr(response, 'size')
        assert hasattr(response, 'usd_value')
        assert hasattr(response, 'price')
        assert hasattr(response, 'order_type')
        assert hasattr(response, 'order_id')
        assert hasattr(response, 'message')

        # Verify message is meaningful
        assert "placed successfully" in response.message

    @pytest.mark.asyncio
    async def test_market_order_has_no_order_id(self, use_case):
        """Test market orders have no order_id (filled immediately)."""
        use_case.market_data.get_price.return_value = 50000.0
        use_case.order_service.place_market_order.return_value = {
            "status": "success",
            "price": 50000.0
        }

        request = PlaceOrderRequest(
            coin="BTC",
            is_buy=True,
            coin_size=0.5,
            is_market=True
        )

        response = await use_case.execute(request)

        assert response.order_id is None

    @pytest.mark.asyncio
    async def test_limit_order_has_order_id(self, use_case):
        """Test limit orders include order_id."""
        with patch.object(use_case.usd_converter, 'convert_usd_to_coin') as mock_convert:
            mock_convert.return_value = (0.02, 50000.0)
            use_case.order_service.place_limit_order.return_value = {
                "status": "success",
                "order_id": 98765
            }

            request = PlaceOrderRequest(
                coin="BTC",
                is_buy=True,
                usd_amount=1000.0,
                is_market=False,
                limit_price=49000.0
            )

            response = await use_case.execute(request)

            assert response.order_id == 98765
