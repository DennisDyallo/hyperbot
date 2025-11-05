"""
Base class for all use cases.

Use cases encapsulate business logic and orchestrate service calls.
They are independent of presentation layer (API/Bot) and can be tested in isolation.
"""
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

# Generic type variables for request and response
TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')


class BaseUseCase(ABC, Generic[TRequest, TResponse]):
    """
    Base class for all use cases.

    Use cases follow the Single Responsibility Principle and contain
    business logic that is shared between API and Bot interfaces.

    Example:
        >>> class PlaceOrderUseCase(BaseUseCase[PlaceOrderRequest, PlaceOrderResponse]):
        ...     async def execute(self, request: PlaceOrderRequest) -> PlaceOrderResponse:
        ...         # Business logic here
        ...         return PlaceOrderResponse(...)
    """

    @abstractmethod
    async def execute(self, request: TRequest) -> TResponse:
        """
        Execute the use case with the given request.

        Args:
            request: Input data for the use case

        Returns:
            Result of the use case execution

        Raises:
            ValueError: If request validation fails
            RuntimeError: If operation fails
        """
        pass


class SyncBaseUseCase(ABC, Generic[TRequest, TResponse]):
    """
    Base class for synchronous use cases.

    Use this for use cases that don't require async operations.
    Most use cases should prefer BaseUseCase (async) since services
    use async/await patterns.
    """

    @abstractmethod
    def execute(self, request: TRequest) -> TResponse:
        """
        Execute the use case with the given request (synchronous).

        Args:
            request: Input data for the use case

        Returns:
            Result of the use case execution

        Raises:
            ValueError: If request validation fails
            RuntimeError: If operation fails
        """
        pass
