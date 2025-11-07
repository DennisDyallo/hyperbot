"""
Use cases package.

Use cases encapsulate business logic and orchestrate service calls.
They provide a clean separation between presentation layer (API/Bot)
and service layer, preventing code duplication and feature divergence.
"""

from src.use_cases.base import BaseUseCase, SyncBaseUseCase

__all__ = ["BaseUseCase", "SyncBaseUseCase"]
