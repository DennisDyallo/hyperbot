"""
Leverage Management Service for Hyperliquid trading.

Provides centralized leverage management with validation, transparency,
and liquidation price estimation for new positions.

Key Features:
- Get/set leverage for any coin (even without existing position)
- Validate leverage against limits (soft 5x warning, hard exchange max)
- Estimate liquidation price for new positions
- Track leverage settings across all coins
- Integration with order service for leverage-aware trading

Usage:
    service = leverage_service

    # View leverage
    leverage = service.get_coin_leverage("BTC")
    all_settings = service.get_all_leverage_settings()

    # Set leverage (only works when no position exists)
    result = service.set_coin_leverage("BTC", leverage=3, is_cross=True)

    # Validate
    validation = service.validate_leverage(leverage=5, coin="BTC")

    # Estimate liquidation price for planned order
    liq_price = service.estimate_liquidation_price(
        coin="BTC",
        entry_price=50000,
        size=0.5,
        leverage=3,
        is_long=True
    )
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from src.services.hyperliquid_service import hyperliquid_service
from src.services.position_service import position_service
from src.services.market_data_service import market_data_service
from src.services.account_service import account_service
from src.config import logger, settings


class LeverageWarningLevel(str, Enum):
    """Warning levels for leverage validation."""
    OK = "OK"                    # <= 5x (recommended)
    HIGH = "HIGH"                # 6x-10x (requires confirmation)
    EXTREME = "EXTREME"          # > 10x (scary warning)


@dataclass
class LeverageValidation:
    """Result of leverage validation."""
    is_valid: bool
    warning_level: LeverageWarningLevel
    message: str
    can_proceed: bool  # Always True for soft limits

    # Additional info
    current_leverage: Optional[int] = None
    exchange_max_leverage: Optional[int] = None
    has_open_position: bool = False


@dataclass
class LeverageSetting:
    """Leverage setting for a coin."""
    coin: str
    leverage: int
    leverage_type: str  # "cross" or "isolated"
    source: str  # "position" (from open position) or "exchange" (default) or "unknown"
    can_change: bool  # False if position exists
    position_value: Optional[float] = None  # USD value if position exists


@dataclass
class LiquidationEstimate:
    """Estimated liquidation price and risk for a planned position."""
    coin: str
    entry_price: float
    size: float
    leverage: int
    is_long: bool

    # Estimates
    estimated_liquidation_price: float
    liquidation_distance_pct: float  # % from entry to liquidation
    position_value: float  # size * entry_price
    margin_required: float  # position_value / leverage

    # Risk assessment
    risk_level: str  # "LOW", "MODERATE", "HIGH", "EXTREME"
    warning: Optional[str] = None


class LeverageService:
    """
    Centralized leverage management service.

    Responsibilities:
    - Get current leverage for any coin
    - Set leverage (with validation)
    - Estimate liquidation price for new positions
    - Validate leverage against user-defined limits
    - Provide leverage transparency before orders

    Limitations:
    - Leverage can only be set when NO position exists for that coin
    - This is a Hyperliquid limitation, not a Hyperbot limitation
    - To change leverage on existing position, must close and reopen
    """

    def __init__(self):
        """Initialize leverage service."""
        self.hyperliquid = hyperliquid_service
        self.position_service = position_service
        self.market_data_service = market_data_service
        self.account_service = account_service

        # Hyperliquid's approximate maintenance margin rate (conservative estimate)
        # Used for liquidation price estimation
        self.MAINTENANCE_MARGIN_RATE = 0.05  # 5%

        logger.debug("LeverageService initialized")

    def get_coin_leverage(self, coin: str) -> Optional[int]:
        """
        Get current leverage setting for a coin.

        Returns leverage from open position if exists, otherwise returns None.
        Note: Hyperliquid doesn't provide a way to query leverage for coins
        without positions, so we can only know leverage for open positions.

        Args:
            coin: Asset symbol (e.g., "BTC", "ETH")

        Returns:
            Leverage value (e.g., 3 for 3x), or None if no position exists
        """
        try:
            positions = self.position_service.list_positions()

            for item in positions:
                pos = item["position"]
                if pos["coin"] == coin:
                    leverage = int(pos["leverage_value"])
                    logger.debug(f"Found leverage for {coin}: {leverage}x")
                    return leverage

            logger.debug(f"No position found for {coin}, leverage unknown")
            return None

        except Exception as e:
            logger.error(f"Failed to get leverage for {coin}: {e}")
            return None

    def get_all_leverage_settings(self) -> List[LeverageSetting]:
        """
        Get leverage settings for all coins with open positions.

        Returns:
            List of LeverageSetting objects for coins with positions
        """
        try:
            positions = self.position_service.list_positions()
            settings = []

            for item in positions:
                pos = item["position"]
                coin = pos["coin"]
                leverage_info = pos.get("leverage", {})

                setting = LeverageSetting(
                    coin=coin,
                    leverage=int(leverage_info.get("value", 1)),
                    leverage_type=leverage_info.get("type", "cross"),
                    source="position",
                    can_change=False,  # Cannot change leverage on open positions
                    position_value=abs(float(pos.get("position_value", 0)))
                )
                settings.append(setting)

            logger.info(f"Retrieved leverage settings for {len(settings)} coins")
            return settings

        except Exception as e:
            logger.error(f"Failed to get all leverage settings: {e}")
            return []

    def set_coin_leverage(
        self,
        coin: str,
        leverage: int,
        is_cross: bool = True
    ) -> Tuple[bool, str]:
        """
        Set leverage for a coin.

        CRITICAL: Can only be called when NO position exists for this coin.
        Hyperliquid does not allow changing leverage on open positions.

        Args:
            coin: Asset symbol (e.g., "BTC", "ETH")
            leverage: Leverage value (e.g., 3 for 3x)
            is_cross: Use cross margin (default True)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Check if position exists
            current_leverage = self.get_coin_leverage(coin)
            if current_leverage is not None:
                msg = (
                    f"Cannot set leverage for {coin} - position already exists "
                    f"with {current_leverage}x leverage. Must close position first."
                )
                logger.warning(msg)
                return False, msg

            # Validate leverage
            validation = self.validate_leverage(leverage, coin)
            if not validation.can_proceed:
                return False, validation.message

            logger.info(
                f"Setting leverage for {coin}: {leverage}x "
                f"(cross={is_cross})"
            )

            # Call Hyperliquid API
            exchange = self.hyperliquid.get_exchange_client()
            result = exchange.update_leverage(
                leverage=leverage,
                name=coin,  # SDK uses 'name' parameter, not 'coin'
                is_cross=is_cross
            )

            logger.info(f"Leverage set successfully for {coin}: {result}")

            # Add warning for high leverage
            msg = f"Leverage set to {leverage}x for {coin}"
            if validation.warning_level != LeverageWarningLevel.OK:
                msg += f" ⚠️ {validation.warning_level.value} leverage - use caution!"

            return True, msg

        except Exception as e:
            error_msg = f"Failed to set leverage for {coin}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def validate_leverage(
        self,
        leverage: int,
        coin: Optional[str] = None
    ) -> LeverageValidation:
        """
        Validate leverage value against limits and recommendations.

        Implements soft limit at 5x (warning but allow) as per user requirements.

        Args:
            leverage: Leverage value to validate
            coin: Optional coin symbol for coin-specific checks

        Returns:
            LeverageValidation object with validation results
        """
        try:
            # Check minimum
            if leverage < 1:
                return LeverageValidation(
                    is_valid=False,
                    warning_level=LeverageWarningLevel.OK,
                    message="Leverage must be at least 1x",
                    can_proceed=False
                )

            # Check if position exists for this coin
            has_position = False
            current_lev = None
            if coin:
                current_lev = self.get_coin_leverage(coin)
                has_position = current_lev is not None

            # Determine warning level based on 5x soft limit
            max_warning = settings.MAX_LEVERAGE_WARNING  # Default 5

            if leverage <= max_warning:
                # OK - within recommended range
                return LeverageValidation(
                    is_valid=True,
                    warning_level=LeverageWarningLevel.OK,
                    message=f"{leverage}x leverage - within recommended range",
                    can_proceed=True,
                    current_leverage=current_lev,
                    has_open_position=has_position
                )

            elif leverage <= 10:
                # HIGH - requires confirmation
                return LeverageValidation(
                    is_valid=True,
                    warning_level=LeverageWarningLevel.HIGH,
                    message=(
                        f"⚠️ {leverage}x leverage is HIGHER than recommended ({max_warning}x). "
                        f"This increases liquidation risk significantly. "
                        f"Proceed with caution!"
                    ),
                    can_proceed=True,  # Soft limit - allow with warning
                    current_leverage=current_lev,
                    has_open_position=has_position
                )

            else:
                # EXTREME - scary warning but still allow (soft limit)
                return LeverageValidation(
                    is_valid=True,
                    warning_level=LeverageWarningLevel.EXTREME,
                    message=(
                        f"🚨 {leverage}x leverage is EXTREMELY HIGH! "
                        f"A small price move could liquidate your position. "
                        f"This is NOT recommended. Consider using {max_warning}x or lower."
                    ),
                    can_proceed=True,  # Soft limit - allow but with scary warning
                    current_leverage=current_lev,
                    has_open_position=has_position
                )

        except Exception as e:
            logger.error(f"Leverage validation failed: {e}")
            return LeverageValidation(
                is_valid=False,
                warning_level=LeverageWarningLevel.OK,
                message=f"Validation error: {str(e)}",
                can_proceed=False
            )

    def estimate_liquidation_price(
        self,
        coin: str,
        entry_price: float,
        size: float,
        leverage: int,
        is_long: bool
    ) -> LiquidationEstimate:
        """
        Estimate liquidation price for a planned position.

        Uses simplified formula based on maintenance margin rate.
        This is an ESTIMATE - actual liquidation price from Hyperliquid
        may differ slightly based on account equity and other positions.

        Formula for cross margin (simplified):
        - Long: liq_price ≈ entry * (1 - 1/leverage + maintenance_rate)
        - Short: liq_price ≈ entry * (1 + 1/leverage - maintenance_rate)

        Args:
            coin: Asset symbol
            entry_price: Expected entry price
            size: Position size in coin units
            leverage: Leverage multiplier
            is_long: True for long, False for short

        Returns:
            LiquidationEstimate with price and risk assessment
        """
        try:
            # Calculate position metrics
            position_value = size * entry_price
            margin_required = position_value / leverage

            # Estimate liquidation price
            # Using conservative maintenance margin rate (5%)
            if is_long:
                # Long: liquidation when price drops
                liq_price = entry_price * (1 - (1 / leverage) + self.MAINTENANCE_MARGIN_RATE)
            else:
                # Short: liquidation when price rises
                liq_price = entry_price * (1 + (1 / leverage) - self.MAINTENANCE_MARGIN_RATE)

            # Calculate distance to liquidation
            if is_long:
                distance_pct = ((entry_price - liq_price) / entry_price) * 100
            else:
                distance_pct = ((liq_price - entry_price) / entry_price) * 100

            # Assess risk level based on distance
            if distance_pct > 50:
                risk_level = "LOW"
                warning = None
            elif distance_pct > 30:
                risk_level = "MODERATE"
                warning = "Monitor price movements closely"
            elif distance_pct > 15:
                risk_level = "HIGH"
                warning = "⚠️ High liquidation risk - consider lower leverage"
            else:
                risk_level = "EXTREME"
                warning = "🚨 EXTREME liquidation risk - strongly recommend lower leverage"

            estimate = LiquidationEstimate(
                coin=coin,
                entry_price=entry_price,
                size=size,
                leverage=leverage,
                is_long=is_long,
                estimated_liquidation_price=round(liq_price, 2),
                liquidation_distance_pct=round(distance_pct, 2),
                position_value=round(position_value, 2),
                margin_required=round(margin_required, 2),
                risk_level=risk_level,
                warning=warning
            )

            logger.debug(
                f"Liquidation estimate for {coin}: "
                f"entry=${entry_price}, liq=${liq_price:.2f}, "
                f"distance={distance_pct:.1f}%, risk={risk_level}"
            )

            return estimate

        except Exception as e:
            logger.error(f"Failed to estimate liquidation price: {e}")
            # Return safe default
            return LiquidationEstimate(
                coin=coin,
                entry_price=entry_price,
                size=size,
                leverage=leverage,
                is_long=is_long,
                estimated_liquidation_price=0,
                liquidation_distance_pct=0,
                position_value=size * entry_price,
                margin_required=(size * entry_price) / leverage,
                risk_level="UNKNOWN",
                warning="⚠️ Could not estimate liquidation price"
            )

    def get_leverage_for_order(
        self,
        coin: str,
        default_leverage: Optional[int] = None
    ) -> Tuple[Optional[int], bool]:
        """
        Get appropriate leverage for placing an order.

        Returns leverage to use and whether it needs to be set.

        Logic:
        1. If position exists: return current leverage, no need to set
        2. If no position: return default_leverage (or from settings), needs to be set

        Args:
            coin: Asset symbol
            default_leverage: Optional default to use if no position exists

        Returns:
            Tuple of (leverage, needs_setting)
            - leverage: int value to use, or None if user must choose
            - needs_setting: True if leverage needs to be set before order
        """
        try:
            # Check if position exists
            current_leverage = self.get_coin_leverage(coin)

            if current_leverage is not None:
                # Position exists - use current leverage
                logger.debug(
                    f"Position exists for {coin} with {current_leverage}x leverage"
                )
                return current_leverage, False

            # No position - need to set leverage before order
            if default_leverage is not None:
                logger.debug(
                    f"No position for {coin}, will use default {default_leverage}x"
                )
                return default_leverage, True

            # Use system default
            system_default = settings.DEFAULT_LEVERAGE
            logger.debug(
                f"No position for {coin}, will use system default {system_default}x"
            )
            return system_default, True

        except Exception as e:
            logger.error(f"Failed to determine leverage for order: {e}")
            return None, True


# Singleton instance
leverage_service = LeverageService()
