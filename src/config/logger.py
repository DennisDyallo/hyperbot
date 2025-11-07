"""
Logging configuration using loguru.
"""

import sys
from pathlib import Path

from loguru import logger

from src.config.settings import settings


def setup_logger() -> None:
    """Configure application logger."""

    # Remove default handler
    logger.remove()

    # Console handler with custom format
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # File handler (if log file specified)
    if settings.LOG_FILE:
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            settings.LOG_FILE,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
            ),
            level=settings.LOG_LEVEL,
            rotation="100 MB",  # Rotate when file reaches 100MB
            retention="30 days",  # Keep logs for 30 days
            compression="zip",  # Compress rotated logs
        )

    logger.info(f"Logger initialized - Level: {settings.LOG_LEVEL}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")


# Setup logger on import
setup_logger()
