"""
Unit tests for ClosePositionUseCase.

Tests position closing logic that handles actual trading operations.
CRITICAL - bugs here = positions not closed properly.
"""

from unittest.mock import Mock

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.use_cases.common.validators import ValidationError
from src.use_cases.trading.close_position import (
    ClosePositionRequest,
    ClosePositionUseCase,
)
from tests.helpers.mock_data import PositionBuilder
from tests.helpers.service_mocks import ServiceMockBuilder, create_service_with_mocks


class TestClosePositionUseCase:
    """Test ClosePositionUseCase."""

    @pytest.fixture
    def mock_position_data(self):
        """Sample position data."""
        return (
            PositionBuilder()
            .with_coin("BTC")
            .with_size(1.0)
            .with_entry_price(50000.0)  # Match current price for USD calculations
            .with_position_value(50000.0)
            .build()
        )

    @pytest.fixture
    def use_case(self):
        """Create ClosePositionUseCase with mocked dependencies."""
        mock_position = ServiceMockBuilder.position_service()
        # All position_service methods are synchronous (not async)
        mock_position.close_position = Mock()

        # Create market_data_service with custom prices matching test expectations
        mock_market_data = ServiceMockBuilder.market_data_service(
            prices={"BTC": 50000.0, "ETH": 3000.0, "SOL": 150.0}
        )

        return create_service_with_mocks(
            ClosePositionUseCase,
            "src.use_cases.trading.close_position",
            {
                "position_service": mock_position,
                "market_data_service": mock_market_data,
            },
        )

    # ===================================================================
    # Full Position Close tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_full_position_close_success(self, use_case, mock_position_data):
        """Test full position close (no parameters)."""
        use_case.position_service.get_position.return_value = mock_position_data
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(coin="BTC")  # No size/percentage = full close

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.coin == "BTC"
        assert response.size_closed == 1.0
        assert response.remaining_size == 0.0
        assert response.close_type == "full"
        assert response.usd_value == pytest.approx(50000.0, abs=0.01)

        use_case.position_service.close_position.assert_called_once_with(
            coin="BTC", size=1.0, slippage=0.05
        )

    @pytest.mark.asyncio
    async def test_full_position_close_short_position(self, use_case):
        """Test full close of short position (negative size)."""
        short_position = (
            PositionBuilder().with_coin("ETH").with_size(-10.0).with_position_value(30000.0).build()
        )
        use_case.position_service.get_position.return_value = short_position
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(coin="ETH")

        response = await use_case.execute(request)

        assert response.size_closed == 10.0  # Absolute value
        assert response.remaining_size == 0.0
        assert response.close_type == "full"

    # ===================================================================
    # Percentage-based Close tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_partial_close_by_percentage(self, use_case, mock_position_data):
        """Test partial position close by percentage."""
        use_case.position_service.get_position.return_value = mock_position_data
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(
            coin="BTC",
            percentage=50.0,  # Close 50%
        )

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.size_closed == 0.5  # 50% of 1.0
        assert response.remaining_size == 0.5
        assert response.close_type == "partial"
        assert response.usd_value == pytest.approx(25000.0, abs=0.01)

        use_case.position_service.close_position.assert_called_once_with(
            coin="BTC", size=0.5, slippage=0.05
        )

    @pytest.mark.asyncio
    async def test_close_100_percent_is_full_close(self, use_case, mock_position_data):
        """Test 100% close is marked as full close."""
        use_case.position_service.get_position.return_value = mock_position_data
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(coin="BTC", percentage=100.0)

        response = await use_case.execute(request)

        assert response.size_closed == 1.0
        assert response.remaining_size == 0.0
        assert response.close_type == "full"

    @pytest.mark.asyncio
    async def test_close_25_percent(self, use_case, mock_position_data):
        """Test 25% position close."""
        use_case.position_service.get_position.return_value = mock_position_data
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(coin="BTC", percentage=25.0)

        response = await use_case.execute(request)

        assert response.size_closed == 0.25
        assert response.remaining_size == 0.75
        assert response.close_type == "partial"

    # ===================================================================
    # Absolute Size Close tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_partial_close_by_size(self, use_case, mock_position_data):
        """Test partial position close by absolute size."""
        use_case.position_service.get_position.return_value = mock_position_data
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(
            coin="BTC",
            size=0.3,  # Close 0.3 BTC
        )

        response = await use_case.execute(request)

        assert response.status == "success"
        assert response.size_closed == 0.3
        assert response.remaining_size == 0.7
        assert response.close_type == "partial"

    @pytest.mark.asyncio
    async def test_close_size_equals_position_size_is_full(self, use_case, mock_position_data):
        """Test close size equal to position size is full close."""
        use_case.position_service.get_position.return_value = mock_position_data
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(
            coin="BTC",
            size=1.0,  # Exact position size
        )

        response = await use_case.execute(request)

        assert response.size_closed == 1.0
        assert response.remaining_size == 0.0
        assert response.close_type == "full"

    # ===================================================================
    # Validation Error tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_position_not_found_raises_error(self, use_case):
        """Test closing non-existent position raises ValueError."""
        use_case.position_service.get_position.return_value = None

        request = ClosePositionRequest(coin="NOTFOUND")

        with pytest.raises(ValueError, match="No open position found"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_multiple_parameters_raises_error(self, use_case, mock_position_data):
        """Test specifying both size and percentage raises ValidationError."""
        use_case.position_service.get_position.return_value = mock_position_data

        request = ClosePositionRequest(
            coin="BTC",
            size=0.5,
            percentage=50.0,  # Both specified!
        )

        with pytest.raises(ValidationError, match="Specify only one of"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_close_size_exceeds_position_raises_error(self, use_case, mock_position_data):
        """Test close size exceeding position size raises ValidationError."""
        use_case.position_service.get_position.return_value = mock_position_data

        request = ClosePositionRequest(
            coin="BTC",
            size=2.0,  # Exceeds position size of 1.0
        )

        with pytest.raises(ValidationError, match="exceeds position size"):
            await use_case.execute(request)

    @pytest.mark.asyncio
    async def test_invalid_percentage_zero_raises_error(self, use_case, mock_position_data):
        """Test zero percentage raises ValidationError."""
        use_case.position_service.get_position.return_value = mock_position_data

        # Pydantic should catch this
        with pytest.raises(PydanticValidationError):
            ClosePositionRequest(coin="BTC", percentage=0.0)

    @pytest.mark.asyncio
    async def test_invalid_percentage_over_100_raises_error(self, use_case, mock_position_data):
        """Test percentage over 100 raises ValidationError."""
        use_case.position_service.get_position.return_value = mock_position_data

        # Pydantic should catch this
        with pytest.raises(PydanticValidationError):
            ClosePositionRequest(coin="BTC", percentage=150.0)

    @pytest.mark.asyncio
    async def test_empty_coin_symbol_raises_error(self, use_case):
        """Test empty coin symbol raises ValidationError."""
        request = ClosePositionRequest(coin="")

        with pytest.raises(ValidationError, match="cannot be empty"):
            await use_case.execute(request)

    # ===================================================================
    # Price Calculation tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_price_fallback_when_market_data_unavailable(self, use_case, mock_position_data):
        """Test fallback to position value when market price unavailable."""
        use_case.position_service.get_position.return_value = mock_position_data
        # Replace get_price to return None (price unavailable)
        use_case.market_data.get_price = Mock(return_value=None)
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(coin="BTC")

        response = await use_case.execute(request)

        # Should use position_value / size = 50000 / 1.0 = 50000
        assert response.usd_value == pytest.approx(50000.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_price_fallback_when_invalid_price(self, use_case, mock_position_data):
        """Test fallback when market price is zero."""
        use_case.position_service.get_position.return_value = mock_position_data
        # Replace get_price to return 0.0 (invalid price)
        use_case.market_data.get_price = Mock(return_value=0.0)
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(coin="BTC")

        response = await use_case.execute(request)

        # Should fallback to position value calculation
        assert response.usd_value == pytest.approx(50000.0, abs=0.01)

    # ===================================================================
    # Service Call tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_custom_slippage_passed_to_service(self, use_case, mock_position_data):
        """Test custom slippage is passed to position service."""
        use_case.position_service.get_position.return_value = mock_position_data
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(
            coin="BTC",
            slippage=0.10,  # 10% slippage
        )

        await use_case.execute(request)

        call_kwargs = use_case.position_service.close_position.call_args.kwargs
        assert call_kwargs["slippage"] == 0.10

    @pytest.mark.asyncio
    async def test_position_service_failure_raises_runtime_error(
        self, use_case, mock_position_data
    ):
        """Test position service failure raises RuntimeError."""
        use_case.position_service.get_position.return_value = mock_position_data
        use_case.position_service.close_position.side_effect = Exception("API Error")

        request = ClosePositionRequest(coin="BTC")

        with pytest.raises(RuntimeError, match="Failed to close position"):
            await use_case.execute(request)

    # ===================================================================
    # Response Building tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_response_includes_all_fields(self, use_case, mock_position_data):
        """Test response includes all expected fields."""
        use_case.position_service.get_position.return_value = mock_position_data
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(coin="BTC", percentage=50.0)

        response = await use_case.execute(request)

        # Verify all fields are present
        assert hasattr(response, "status")
        assert hasattr(response, "coin")
        assert hasattr(response, "size_closed")
        assert hasattr(response, "usd_value")
        assert hasattr(response, "remaining_size")
        assert hasattr(response, "close_type")
        assert hasattr(response, "message")

        # Verify message is meaningful
        assert "closed successfully" in response.message

    @pytest.mark.asyncio
    async def test_coin_symbol_normalized_to_uppercase(self, use_case, mock_position_data):
        """Test coin symbol is normalized to uppercase."""
        mock_position_data["position"]["coin"] = "BTC"  # Ensure data matches
        use_case.position_service.get_position.return_value = mock_position_data
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(coin="btc")  # Lowercase

        response = await use_case.execute(request)

        # Should be normalized to uppercase
        assert response.coin == "BTC"

    # ===================================================================
    # Edge Case tests
    # ===================================================================

    @pytest.mark.asyncio
    async def test_large_position_close(self, use_case):
        """Test closing large position."""
        large_position = (
            PositionBuilder()
            .with_coin("SOL")
            .with_size(10000.0)
            .with_position_value(1500000.0)
            .build()
        )
        use_case.position_service.get_position.return_value = large_position
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(coin="SOL", percentage=25.0)

        response = await use_case.execute(request)

        assert response.size_closed == 2500.0
        assert response.remaining_size == 7500.0
        assert response.usd_value == pytest.approx(375000.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_small_position_close(self, use_case):
        """Test closing very small position."""
        small_position = (
            PositionBuilder().with_coin("BTC").with_size(0.001).with_position_value(50.0).build()
        )
        use_case.position_service.get_position.return_value = small_position
        use_case.position_service.close_position.return_value = {"status": "success"}

        request = ClosePositionRequest(coin="BTC")

        response = await use_case.execute(request)

        assert response.size_closed == 0.001
        assert response.remaining_size == 0.0
