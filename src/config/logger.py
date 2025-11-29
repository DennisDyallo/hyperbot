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

    # Determine if running in cloud environment
    is_cloud = settings.ENVIRONMENT in ("production", "staging") or settings.is_cloud_run()

    # Console/stdout handler
    # Cloud environments (GCP Cloud Run, AWS, Azure) capture stdout
    # Use simpler format for cloud (better for log aggregation)
    if is_cloud:
        # Structured logging for cloud (JSON-like, easier to parse)
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level=settings.LOG_LEVEL,
            colorize=False,  # No colors in cloud logs
            serialize=False,  # Could set to True for JSON format
        )
    else:
        # Colorized output for local development
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

    # File handler (only for local/development)
    # In cloud, stdout is captured by the platform (GCP Cloud Logging, CloudWatch, etc.)
    if settings.LOG_FILE and not is_cloud:
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
    if is_cloud:
        logger.info("Cloud environment detected - logging to stdout only")


# Setup logger on import
setup_logger()
