"""
Patching utilities.

Provides context managers and helpers for patching services and dependencies
in a clean, readable way.
"""

from typing import Dict, Any
from unittest.mock import patch, Mock
from contextlib import contextmanager
from collections import namedtuple


# Named tuple for holding patched mocks
PatchedServices = namedtuple('PatchedServices', [])


@contextmanager
def patch_services(**service_paths):
    """
    Context manager for patching multiple services at once.

    This is a convenience wrapper that patches multiple module paths and
    returns a namespace object containing the mocked services.

    Args:
        **service_paths: Keyword arguments mapping names to module paths
                        Example: hyperliquid='src.services.X.hyperliquid_service'

    Yields:
        Namespace object with mocked services accessible as attributes

    Example:
        >>> with patch_services(
        ...     hyperliquid='src.services.leverage_service.hyperliquid_service',
        ...     position='src.services.leverage_service.position_service'
        ... ) as mocks:
        ...     # Configure mocks
        ...     mocks.hyperliquid.is_initialized.return_value = True
        ...     mocks.position.list_positions.return_value = []
        ...
        ...     # Test code using patched services
        ...     service = LeverageService()
        ...     result = service.get_coin_leverage("BTC")
    """
    # Create mock objects
    mock_services = {name: Mock() for name in service_paths.keys()}

    # Create patches
    patches = {
        name: patch(path, mock_obj)
        for name, (path, mock_obj) in zip(
            service_paths.keys(),
            [(path, mock_services[name]) for name, path in service_paths.items()]
        )
    }

    # Enter all patches
    entered_patches = {}
    try:
        for name, p in patches.items():
            entered_patches[name] = p.__enter__()

        # Return namespace with mock objects
        # Use a dynamic namedtuple to allow attribute access
        MockNamespace = namedtuple('MockNamespace', service_paths.keys())
        yield MockNamespace(**mock_services)

    finally:
        # Exit all patches in reverse order
        for p in reversed(list(patches.values())):
            try:
                p.__exit__(None, None, None)
            except Exception:
                pass  # Ignore cleanup errors


@contextmanager
def patch_hyperliquid_service(initialized: bool = True):
    """
    Convenience context manager for patching HyperliquidService.

    This is a specialized version of patch_services for the common case
    of mocking the Hyperliquid service singleton.

    Args:
        initialized: Whether service should report as initialized

    Yields:
        Mock HyperliquidService object

    Example:
        >>> with patch_hyperliquid_service() as mock_hl:
        ...     mock_hl.get_info_client.return_value.user_state.return_value = {...}
        ...     # Test code
    """
    mock_hl = Mock()
    mock_hl.is_initialized = Mock(return_value=initialized)
    mock_hl.get_info_client = Mock()
    mock_hl.get_exchange_client = Mock()

    with patch('src.services.hyperliquid_service.hyperliquid_service', mock_hl):
        yield mock_hl


@contextmanager
def patch_service_dependencies(service_module_path: str, **dependencies):
    """
    Context manager for patching service dependencies.

    This patches multiple dependencies within a service module and yields
    them for configuration.

    Args:
        service_module_path: Full module path of the service (e.g., 'src.services.leverage_service')
        **dependencies: Dependency names to patch

    Yields:
        Namespace with patched dependencies

    Example:
        >>> with patch_service_dependencies(
        ...     'src.services.leverage_service',
        ...     hyperliquid_service=Mock(),
        ...     position_service=Mock()
        ... ) as deps:
        ...     deps.hyperliquid_service.is_initialized.return_value = True
        ...     deps.position_service.list_positions.return_value = []
        ...
        ...     service = LeverageService()
        ...     # Dependencies are now patched
    """
    paths = {
        name: f'{service_module_path}.{name}'
        for name in dependencies.keys()
    }

    with patch_services(**paths) as mocks:
        yield mocks


@contextmanager
def patch_use_case_services(**service_mocks):
    """
    Context manager for patching services used by use cases.

    This is specialized for use case tests where you need to patch
    service singletons that use cases depend on.

    Args:
        **service_mocks: Service names mapped to Mock objects or None (auto-create)

    Yields:
        Namespace with patched services

    Example:
        >>> with patch_use_case_services(
        ...     order_service=Mock(),
        ...     market_data_service=Mock()
        ... ) as services:
        ...     services.order_service.place_market_order.return_value = {...}
        ...     services.market_data_service.get_price.return_value = 50000.0
        ...
        ...     use_case = PlaceOrderUseCase()
        ...     response = await use_case.execute(request)
    """
    # Auto-create mocks if None provided
    mocks = {
        name: (mock if mock is not None else Mock())
        for name, mock in service_mocks.items()
    }

    # Build patch paths (assumes services are in src.services)
    paths = {
        name: f'src.services.{name}.{name}'
        for name in mocks.keys()
    }

    # Create patches
    patches = {
        name: patch(path, mock_obj)
        for name, (path, mock_obj) in zip(paths.keys(), [(p, mocks[n]) for n, p in paths.items()])
    }

    # Enter all patches
    try:
        for p in patches.values():
            p.__enter__()

        # Return namespace
        MockNamespace = namedtuple('MockNamespace', mocks.keys())
        yield MockNamespace(**mocks)

    finally:
        # Exit all patches
        for p in reversed(list(patches.values())):
            try:
                p.__exit__(None, None, None)
            except Exception:
                pass


def create_patched_mock(module_path: str, **attributes):
    """
    Create and return a mock with specified attributes, ready for patching.

    This is useful when you need to create a mock with pre-configured
    attributes before using it in a patch.

    Args:
        module_path: Module path to patch (not used, just for documentation)
        **attributes: Attributes to set on the mock

    Returns:
        Configured Mock object

    Example:
        >>> mock_service = create_patched_mock(
        ...     'src.services.order_service',
        ...     place_market_order=Mock(return_value={"status": "ok"}),
        ...     place_limit_order=Mock(return_value={"order_id": 123})
        ... )
        >>> with patch('src.use_cases.X.order_service', mock_service):
        ...     # Test code
    """
    mock = Mock()
    for attr_name, attr_value in attributes.items():
        setattr(mock, attr_name, attr_value)
    return mock


# Convenience functions for common patching scenarios

@contextmanager
def no_op_patch():
    """
    No-op context manager for conditional patching.

    Useful when you want to conditionally patch based on test parameters.

    Example:
        >>> patch_ctx = patch_services(...) if condition else no_op_patch()
        >>> with patch_ctx as mocks:
        ...     # Test code
    """
    yield None


@contextmanager
def patch_settings(**settings_overrides):
    """
    Context manager for temporarily overriding settings.

    Args:
        **settings_overrides: Settings to override

    Yields:
        None

    Example:
        >>> with patch_settings(TELEGRAM_AUTHORIZED_USERS=[12345]):
        ...     # Test with different authorized users
        ...     result = handler(update, context)
    """
    from src.config import settings

    original_values = {}

    try:
        # Save originals and set overrides
        for key, value in settings_overrides.items():
            if hasattr(settings, key):
                original_values[key] = getattr(settings, key)
            setattr(settings, key, value)

        yield

    finally:
        # Restore originals
        for key, value in original_values.items():
            setattr(settings, key, value)
