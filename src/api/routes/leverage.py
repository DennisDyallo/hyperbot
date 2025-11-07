"""
Leverage Management API Endpoints.

Provides endpoints for viewing and managing leverage settings
across trading pairs with validation and risk warnings.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.config import logger
from src.services.leverage_service import leverage_service

router = APIRouter(prefix="/leverage", tags=["leverage"])


# Request/Response Models


class SetLeverageRequest(BaseModel):
    """Request to set leverage for a coin."""

    coin: str = Field(..., description="Trading pair symbol (e.g., 'BTC', 'ETH')")
    leverage: int = Field(..., ge=1, le=50, description="Leverage multiplier (1-50x)")
    is_cross: bool = Field(True, description="Use cross margin (default True)")


class SetLeverageResponse(BaseModel):
    """Response after setting leverage."""

    success: bool
    message: str
    coin: str
    leverage: int | None = None
    warning_level: str | None = None


class GetLeverageResponse(BaseModel):
    """Response with current leverage for a coin."""

    coin: str
    leverage: int | None = None
    has_position: bool
    can_change: bool


class LeverageSettingsResponse(BaseModel):
    """Response with all leverage settings."""

    settings: list
    total_coins: int


class ValidateLeverageRequest(BaseModel):
    """Request to validate leverage value."""

    leverage: int = Field(..., ge=1, description="Leverage to validate")
    coin: str | None = Field(None, description="Optional coin for coin-specific checks")


class ValidateLeverageResponse(BaseModel):
    """Response with leverage validation results."""

    is_valid: bool
    warning_level: str
    message: str
    can_proceed: bool
    current_leverage: int | None = None
    has_open_position: bool = False


class EstimateLiquidationRequest(BaseModel):
    """Request to estimate liquidation price."""

    coin: str
    entry_price: float = Field(..., gt=0)
    size: float = Field(..., gt=0)
    leverage: int = Field(..., ge=1, le=50)
    is_long: bool


class EstimateLiquidationResponse(BaseModel):
    """Response with liquidation price estimate."""

    coin: str
    entry_price: float
    size: float
    leverage: int
    is_long: bool
    estimated_liquidation_price: float
    liquidation_distance_pct: float
    position_value: float
    margin_required: float
    risk_level: str
    warning: str | None = None


# Endpoints


@router.get(
    "/{coin}",
    response_model=GetLeverageResponse,
    summary="Get leverage for coin",
    description="Get current leverage setting for a specific coin",
)
def get_coin_leverage(coin: str):
    """
    Get current leverage for a coin.

    Returns leverage from open position if exists, otherwise None.

    Args:
        coin: Trading pair symbol (e.g., "BTC", "ETH")

    Returns:
        Current leverage and whether it can be changed
    """
    try:
        logger.info(f"Getting leverage for {coin}")

        leverage = leverage_service.get_coin_leverage(coin)
        has_position = leverage is not None

        return GetLeverageResponse(
            coin=coin,
            leverage=leverage,
            has_position=has_position,
            can_change=not has_position,  # Can only change when no position exists
        )

    except Exception as e:
        logger.error(f"Failed to get leverage for {coin}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get leverage: {str(e)}",
        ) from e


@router.get(
    "/",
    response_model=LeverageSettingsResponse,
    summary="Get all leverage settings",
    description="Get leverage settings for all coins with open positions",
)
def get_all_leverage_settings():
    """
    Get leverage settings for all coins with open positions.

    Returns list of leverage settings with position values.
    """
    try:
        logger.info("Getting all leverage settings")

        settings = leverage_service.get_all_leverage_settings()

        # Convert dataclass to dict
        settings_list = [
            {
                "coin": s.coin,
                "leverage": s.leverage,
                "leverage_type": s.leverage_type,
                "source": s.source,
                "can_change": s.can_change,
                "position_value": s.position_value,
            }
            for s in settings
        ]

        return LeverageSettingsResponse(settings=settings_list, total_coins=len(settings_list))

    except Exception as e:
        logger.error(f"Failed to get all leverage settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get leverage settings: {str(e)}",
        ) from e


@router.post(
    "/set",
    response_model=SetLeverageResponse,
    summary="Set leverage for coin",
    description="Set leverage for a coin (only works when no position exists)",
)
def set_coin_leverage(request: SetLeverageRequest):
    """
    Set leverage for a coin.

    IMPORTANT: Can only be set when NO position exists for this coin.
    Hyperliquid does not allow changing leverage on open positions.

    Args:
        request: SetLeverageRequest with coin, leverage, and is_cross

    Returns:
        Success status and message with warnings if applicable
    """
    try:
        logger.info(
            f"Setting leverage for {request.coin}: {request.leverage}x (cross={request.is_cross})"
        )

        # Validate first
        validation = leverage_service.validate_leverage(request.leverage, request.coin)

        if not validation.can_proceed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=validation.message)

        # Set leverage
        success, message = leverage_service.set_coin_leverage(
            coin=request.coin, leverage=request.leverage, is_cross=request.is_cross
        )

        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        return SetLeverageResponse(
            success=True,
            message=message,
            coin=request.coin,
            leverage=request.leverage,
            warning_level=validation.warning_level.value,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set leverage for {request.coin}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set leverage: {str(e)}",
        ) from e


@router.post(
    "/validate",
    response_model=ValidateLeverageResponse,
    summary="Validate leverage value",
    description="Validate leverage value against limits and get warnings",
)
def validate_leverage(request: ValidateLeverageRequest):
    """
    Validate leverage value against limits.

    Returns validation status with warnings for high leverage (>5x soft limit).

    Args:
        request: ValidateLeverageRequest with leverage and optional coin

    Returns:
        Validation results with warning level and message
    """
    try:
        logger.info(f"Validating leverage: {request.leverage}x for {request.coin or 'any coin'}")

        validation = leverage_service.validate_leverage(
            leverage=request.leverage, coin=request.coin
        )

        return ValidateLeverageResponse(
            is_valid=validation.is_valid,
            warning_level=validation.warning_level.value,
            message=validation.message,
            can_proceed=validation.can_proceed,
            current_leverage=validation.current_leverage,
            has_open_position=validation.has_open_position,
        )

    except Exception as e:
        logger.error(f"Failed to validate leverage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate leverage: {str(e)}",
        ) from e


@router.post(
    "/estimate-liquidation",
    response_model=EstimateLiquidationResponse,
    summary="Estimate liquidation price",
    description="Estimate liquidation price for a planned position",
)
def estimate_liquidation_price(request: EstimateLiquidationRequest):
    """
    Estimate liquidation price for a planned position.

    Uses simplified formula based on maintenance margin rate.
    This is an ESTIMATE - actual liquidation price from Hyperliquid
    may differ slightly.

    Args:
        request: EstimateLiquidationRequest with position details

    Returns:
        Liquidation price estimate with risk assessment
    """
    try:
        logger.info(
            f"Estimating liquidation for {request.coin}: "
            f"{'LONG' if request.is_long else 'SHORT'} "
            f"{request.size} @ ${request.entry_price} with {request.leverage}x"
        )

        estimate = leverage_service.estimate_liquidation_price(
            coin=request.coin,
            entry_price=request.entry_price,
            size=request.size,
            leverage=request.leverage,
            is_long=request.is_long,
        )

        return EstimateLiquidationResponse(
            coin=estimate.coin,
            entry_price=estimate.entry_price,
            size=estimate.size,
            leverage=estimate.leverage,
            is_long=estimate.is_long,
            estimated_liquidation_price=estimate.estimated_liquidation_price,
            liquidation_distance_pct=estimate.liquidation_distance_pct,
            position_value=estimate.position_value,
            margin_required=estimate.margin_required,
            risk_level=estimate.risk_level,
            warning=estimate.warning,
        )

    except Exception as e:
        logger.error(f"Failed to estimate liquidation price: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to estimate liquidation price: {str(e)}",
        ) from e
