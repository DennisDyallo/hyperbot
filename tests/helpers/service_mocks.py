"""
Service mocking utilities.

Implements the Service Singleton Mocking Pattern from CLAUDE.md to avoid common pitfalls:
- Services created at module import time as singletons
- Simply patching the module won't work
- Must explicitly assign mocked dependencies to service instance

Reference: docs/CLAUDE.md - Testing Best Practices > Service Singleton Mocking Pattern
"""

from contextlib import contextmanager
from typing import Any
from unittest.mock import AsyncMock, Mock, patch


def create_service_with_mocks(
    service_class: type, module_path: str, dependencies: dict[str, Mock]
) -> Any:
    """
    Factory for creating service instances with properly mocked dependencies.

    This implements the CRITICAL Service Singleton Mocking Pattern from CLAUDE.md.

    Args:
        service_class: The service class to instantiate (e.g., LeverageService)
        module_path: Full module path where service is defined (e.g., 'src.services.leverage_service')
        dependencies: Dict mapping dependency names to Mock objects
                     (e.g., {'hyperliquid_service': mock_hl, 'position_service': mock_pos})

    Returns:
        Service instance with mocked dependencies properly assigned

    Example:
        >>> mock_hl = Mock(is_initialized=Mock(return_value=True))
        >>> mock_pos = Mock()
        >>> service = create_service_with_mocks(
        ...     LeverageService,
        ...     'src.services.leverage_service',
        ...     {'hyperliquid_service': mock_hl, 'position_service': mock_pos}
        ... )
        >>> # Service now has mocked dependencies properly assigned

    Why this is needed:
        Services are singletons created at module import time. Simply using patch()
        doesn't work because the service instance already holds a reference to the
        real dependency. We must BOTH patch the module AND explicitly assign to the
        service instance.

    Reference:
        CLAUDE.md - Testing Best Practices > Service Singleton Mocking Pattern
    """
    # Build nested context managers for all patches
    patches = [
        patch(f"{module_path}.{dep_name}", mock_obj) for dep_name, mock_obj in dependencies.items()
    ]

    # Enter all patch contexts
    for p in patches:
        p.__enter__()

    try:
        # Create service instance
        service = service_class()

        # CRITICAL: Explicitly assign mocked dependencies
        # This is what makes the pattern work!
        for dep_name, mock_obj in dependencies.items():
            # Handle common attribute name mappings
            # e.g., 'hyperliquid_service' -> 'hyperliquid'
            attr_name = (
                dep_name.replace("_service", "") if dep_name.endswith("_service") else dep_name
            )
            if hasattr(service, attr_name):
                setattr(service, attr_name, mock_obj)
            elif hasattr(service, dep_name):
                setattr(service, dep_name, mock_obj)
            # If neither exists, service might use different name - let it fail naturally in tests

        return service
    finally:
        # Exit all patch contexts
        for p in reversed(patches):
            p.__exit__(None, None, None)


class ServiceMockBuilder:
    """
    Fluent builder for creating commonly used service mocks with realistic defaults.

    This provides pre-configured mocks for services to reduce boilerplate.

    Example:
        >>> mock_hl = ServiceMockBuilder.hyperliquid_service()
        >>> mock_hl.is_initialized.return_value  # True by default
        True
    """

    @staticmethod
    def hyperliquid_service(initialized: bool = True) -> Mock:
        """
        Create a mock HyperliquidService.

        Args:
            initialized: Whether service should report as initialized

        Returns:
            Mock HyperliquidService with common methods configured
        """
        mock = Mock()
        mock.is_initialized = Mock(return_value=initialized)
        mock.get_info_client = Mock()
        mock.get_exchange_client = Mock()
        mock.initialize = Mock()
        mock.health_check = Mock(return_value={"status": "healthy"})
        return mock

    @staticmethod
    def position_service() -> Mock:
        """Create a mock PositionService with common methods."""
        mock = Mock()
        mock.list_positions = Mock(return_value=[])
        mock.get_position = Mock(return_value=None)
        mock.close_position = Mock()
        mock.get_position_summary = Mock()
        return mock

    @staticmethod
    def account_service() -> Mock:
        """Create a mock AccountService with common methods."""
        mock = Mock()
        mock.get_account_info = Mock(return_value={})
        mock.get_account_summary = Mock()
        return mock

    @staticmethod
    def order_service() -> Mock:
        """
        Create a mock OrderService with common methods.

        Note: Uses AsyncMock to support both sync and async usage patterns.
        Some code awaits these methods (use cases), others call synchronously (services).
        """
        mock = Mock()
        mock.place_market_order = AsyncMock()
        mock.place_limit_order = AsyncMock()
        mock.cancel_order = AsyncMock()
        return mock

    @staticmethod
    def market_data_service(prices: dict[str, float] | None = None) -> Mock:
        """
        Create a mock MarketDataService.

        Args:
            prices: Optional dict of coin -> price mappings

        Returns:
            Mock MarketDataService with get_price configured
        """
        if prices is None:
            prices = {
                "BTC": 104088.0,
                "ETH": 3850.50,
                "SOL": 161.64,
            }

        mock = Mock()
        mock.get_price = Mock(side_effect=lambda coin: prices.get(coin, 0.0))
        mock.get_all_prices = Mock(return_value=prices)
        mock.get_asset_metadata = Mock()
        return mock

    @staticmethod
    def leverage_service() -> Mock:
        """Create a mock LeverageService with common methods."""
        mock = Mock()
        mock.get_coin_leverage = Mock()
        mock.set_coin_leverage = Mock()
        mock.validate_leverage = Mock()
        mock.estimate_liquidation_price = Mock()
        mock.get_all_leverage_settings = Mock(return_value=[])
        mock.get_leverage_for_order = Mock(return_value=(3, False))
        return mock

    @staticmethod
    def rebalance_service() -> Mock:
        """Create a mock RebalanceService with common methods."""
        mock = Mock()
        mock.validate_target_weights = Mock()
        mock.calculate_current_allocation = Mock(return_value={})
        mock.calculate_required_trades = Mock(return_value=[])
        mock.preview_rebalance = Mock()
        mock.execute_trade = Mock()
        return mock


@contextmanager
def service_fixture(service_class: type, module_path: str, **dependencies):
    """
    Context manager for creating service with mocked dependencies.

    Convenience wrapper around create_service_with_mocks for use in test methods.

    Example:
        >>> with service_fixture(
        ...     LeverageService,
        ...     'src.services.leverage_service',
        ...     hyperliquid_service=Mock(),
        ...     position_service=Mock()
        ... ) as service:
        ...     # Use service in test
        ...     result = service.get_coin_leverage("BTC")
    """
    service = create_service_with_mocks(service_class, module_path, dependencies)
    try:
        yield service
    finally:
        pass  # Cleanup if needed
