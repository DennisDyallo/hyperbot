"""
Centralized validation utilities for orders, positions, and trading operations.

This module provides consistent validation logic across API and Bot interfaces.
All validation rules are defined here to ensure they stay in sync.
"""

from src.config import logger, settings


class ValidationError(ValueError):
    """
    Custom exception for validation errors.

    Raised when validation fails. Provides clear error messages
    that can be displayed to users.
    """

    pass


class OrderValidator:
    """
    Validator for trading orders.

    Provides validation for order parameters like size, price, leverage, etc.
    All methods are static since this is a stateless validator class.
    """

    @staticmethod
    def validate_positive_amount(amount: float, field_name: str = "Amount") -> None:
        """
        Validate that amount is positive and non-zero.

        Args:
            amount: Amount to validate
            field_name: Name of the field for error messages

        Raises:
            ValidationError: If amount is invalid

        Examples:
            >>> OrderValidator.validate_positive_amount(100.0, "USD amount")
            >>> OrderValidator.validate_positive_amount(-10.0, "Size")
            ValidationError: Size must be greater than 0
        """
        if amount <= 0:
            raise ValidationError(f"{field_name} must be greater than 0")

    @staticmethod
    def validate_size(size: float, coin: str, min_size: float | None = None) -> None:
        """
        Validate order size.

        Args:
            size: Order size to validate
            coin: Asset symbol
            min_size: Minimum size (if known from asset metadata)

        Raises:
            ValidationError: If size is invalid

        Examples:
            >>> OrderValidator.validate_size(0.01, "BTC")
            >>> OrderValidator.validate_size(0.0, "BTC")
            ValidationError: Order size must be greater than 0
        """
        OrderValidator.validate_positive_amount(size, "Order size")

        if min_size is not None and size < min_size:
            raise ValidationError(f"Order size {size} is below minimum {min_size} for {coin}")

    @staticmethod
    def validate_price(price: float, coin: str, tick_size: float | None = None) -> None:
        """
        Validate order price.

        Args:
            price: Order price to validate
            coin: Asset symbol
            tick_size: Price tick size (if known from asset metadata)

        Raises:
            ValidationError: If price is invalid

        Examples:
            >>> OrderValidator.validate_price(50000.0, "BTC")
            >>> OrderValidator.validate_price(50001.5, "BTC", tick_size=1.0)
            ValidationError: Price 50001.5 is not divisible by tick size 1.0 for BTC
        """
        OrderValidator.validate_positive_amount(price, "Price")

        if tick_size is not None:
            # Check if price is divisible by tick size (within floating point tolerance)
            remainder = price % tick_size
            if remainder > 1e-10:  # Allow for floating point errors
                raise ValidationError(
                    f"Price {price} is not divisible by tick size {tick_size} for {coin}"
                )

    @staticmethod
    def validate_leverage(leverage: int, coin: str | None = None) -> dict:
        """
        Validate leverage value and return risk assessment.

        Args:
            leverage: Leverage value to validate
            coin: Asset symbol (optional, for logging)

        Returns:
            Dict with validation result and warnings:
            {
                "valid": bool,
                "risk_level": str,  # "LOW", "MODERATE", "HIGH", "EXTREME"
                "warnings": List[str]
            }

        Raises:
            ValidationError: If leverage is invalid

        Examples:
            >>> OrderValidator.validate_leverage(3)
            {'valid': True, 'risk_level': 'LOW', 'warnings': []}
            >>> OrderValidator.validate_leverage(15)
            {'valid': True, 'risk_level': 'EXTREME', 'warnings': ['Leverage 15x is extremely high...']}
        """
        # Validate range (1x to 50x on Hyperliquid)
        if leverage < 1:
            raise ValidationError("Leverage must be at least 1x")

        if leverage > 50:
            raise ValidationError("Leverage cannot exceed 50x (Hyperliquid maximum)")

        # Assess risk level and generate warnings
        warnings = []
        risk_level = "LOW"

        if leverage > settings.DEFAULT_LEVERAGE:
            if leverage <= settings.MAX_LEVERAGE_WARNING:
                risk_level = "MODERATE"
                warnings.append(
                    f"Leverage {leverage}x is above recommended default ({settings.DEFAULT_LEVERAGE}x)"
                )
            elif leverage <= 10:
                risk_level = "HIGH"
                warnings.append(
                    f"Leverage {leverage}x is high. Consider using {settings.DEFAULT_LEVERAGE}x or lower"
                )
            else:
                risk_level = "EXTREME"
                warnings.append(
                    f"Leverage {leverage}x is extremely high. Risk of liquidation is very high"
                )

        logger.debug(
            f"Leverage validation: {leverage}x for {coin or 'unknown'} - "
            f"Risk: {risk_level}, Warnings: {len(warnings)}"
        )

        return {"valid": True, "risk_level": risk_level, "warnings": warnings}

    @staticmethod
    def validate_coin_symbol(coin: str, valid_coins: list | None = None) -> None:
        """
        Validate coin symbol.

        Args:
            coin: Asset symbol to validate
            valid_coins: List of valid coin symbols (optional)

        Raises:
            ValidationError: If coin symbol is invalid

        Examples:
            >>> OrderValidator.validate_coin_symbol("BTC")
            >>> OrderValidator.validate_coin_symbol("BTC", ["BTC", "ETH"])
            >>> OrderValidator.validate_coin_symbol("INVALID", ["BTC", "ETH"])
            ValidationError: Invalid coin symbol: INVALID
        """
        if not coin or not coin.strip():
            raise ValidationError("Coin symbol cannot be empty")

        coin = coin.strip().upper()

        if valid_coins is not None and coin not in valid_coins:
            raise ValidationError(
                f"Invalid coin symbol: {coin}. Valid coins: {', '.join(valid_coins)}"
            )

    @staticmethod
    def validate_percentage(percentage: float, field_name: str = "Percentage") -> None:
        """
        Validate percentage value (0-100).

        Args:
            percentage: Percentage to validate
            field_name: Name of the field for error messages

        Raises:
            ValidationError: If percentage is invalid

        Examples:
            >>> OrderValidator.validate_percentage(50.0)
            >>> OrderValidator.validate_percentage(150.0)
            ValidationError: Percentage must be between 0 and 100
        """
        if percentage < 0 or percentage > 100:
            raise ValidationError(f"{field_name} must be between 0 and 100")

    @staticmethod
    def validate_slippage(slippage: float) -> None:
        """
        Validate slippage tolerance (0-100%).

        Args:
            slippage: Slippage tolerance as percentage (e.g., 5.0 for 5%)

        Raises:
            ValidationError: If slippage is invalid

        Examples:
            >>> OrderValidator.validate_slippage(5.0)
            >>> OrderValidator.validate_slippage(150.0)
            ValidationError: Slippage must be between 0 and 100%
        """
        OrderValidator.validate_percentage(slippage, "Slippage")

        if slippage > 10:
            logger.warning(
                f"High slippage tolerance: {slippage}%. Orders may execute at poor prices"
            )

    @staticmethod
    def validate_order_count(count: int, min_count: int = 1, max_count: int = 20) -> None:
        """
        Validate number of orders (e.g., for scale orders).

        Args:
            count: Number of orders
            min_count: Minimum allowed count
            max_count: Maximum allowed count

        Raises:
            ValidationError: If count is invalid

        Examples:
            >>> OrderValidator.validate_order_count(5)
            >>> OrderValidator.validate_order_count(50)
            ValidationError: Order count must be between 1 and 20
        """
        if count < min_count or count > max_count:
            raise ValidationError(f"Order count must be between {min_count} and {max_count}")


class PortfolioValidator:
    """
    Validator for portfolio operations (rebalancing, risk checks, etc.).

    All methods are static since this is a stateless validator class.
    """

    @staticmethod
    def validate_weights(weights: dict) -> None:
        """
        Validate portfolio weights sum to 100%.

        Args:
            weights: Dict of {coin: weight_percentage}

        Raises:
            ValidationError: If weights are invalid

        Examples:
            >>> PortfolioValidator.validate_weights({"BTC": 50.0, "ETH": 50.0})
            >>> PortfolioValidator.validate_weights({"BTC": 40.0, "ETH": 50.0})
            ValidationError: Weights must sum to 100% (got 90.0%)
        """
        if not weights:
            raise ValidationError("Weights cannot be empty")

        total_weight = sum(weights.values())

        # Allow for small floating point errors
        if abs(total_weight - 100.0) > 0.01:
            raise ValidationError(f"Weights must sum to 100% (got {total_weight:.2f}%)")

        # Validate individual weights
        for coin, weight in weights.items():
            if weight < 0:
                raise ValidationError(f"Weight for {coin} cannot be negative")
            if weight > 100:
                raise ValidationError(f"Weight for {coin} cannot exceed 100%")

    @staticmethod
    def validate_margin_ratio(margin_ratio: float) -> dict:
        """
        Validate cross margin ratio and return risk assessment.

        Args:
            margin_ratio: Cross margin ratio as percentage (0-100)

        Returns:
            Dict with risk assessment:
            {
                "safe": bool,
                "risk_level": str,
                "warnings": List[str]
            }

        Examples:
            >>> PortfolioValidator.validate_margin_ratio(10.0)
            {'safe': True, 'risk_level': 'SAFE', 'warnings': []}
            >>> PortfolioValidator.validate_margin_ratio(95.0)
            {'safe': False, 'risk_level': 'CRITICAL', 'warnings': ['Margin ratio is critical...']}
        """
        warnings = []
        safe = True
        risk_level = "SAFE"

        if margin_ratio >= 90:
            safe = False
            risk_level = "CRITICAL"
            warnings.append(
                f"Margin ratio is critical ({margin_ratio:.2f}%). "
                "Liquidation risk is extremely high"
            )
        elif margin_ratio >= 70:
            safe = False
            risk_level = "HIGH"
            warnings.append(
                f"Margin ratio is high ({margin_ratio:.2f}%). "
                "Consider reducing positions or adding margin"
            )
        elif margin_ratio >= 50:
            risk_level = "MODERATE"
            warnings.append(
                f"Margin ratio is moderate ({margin_ratio:.2f}%). Monitor positions closely"
            )
        elif margin_ratio >= 30:
            risk_level = "LOW"

        return {"safe": safe, "risk_level": risk_level, "warnings": warnings}
