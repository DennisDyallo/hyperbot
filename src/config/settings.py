"""
Application configuration settings.
Loads configuration from environment variables or GCP Secret Manager.
"""

import os

from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()


def _get_config_value(key: str, default: str = "") -> str:
    """
    Get configuration value from environment or GCP Secret Manager.

    In cloud environments (GCP Cloud Run), secrets are loaded from Secret Manager.
    In local development, secrets are loaded from .env file.

    Args:
        key: Configuration key (e.g., "TELEGRAM_BOT_TOKEN")
        default: Default value if not found

    Returns:
        Configuration value
    """
    # First check environment variables (works for both local and cloud)
    value = os.getenv(key, default)

    # If in cloud and value not set, try Secret Manager
    if not value and os.getenv("K_SERVICE"):  # Running on Cloud Run
        try:
            from src.config.secrets import get_secret

            # Convert env var name to secret name (e.g., TELEGRAM_BOT_TOKEN -> lb-hyperbot-telegram-bot-token)
            secret_name = "lb-hyperbot-" + key.lower().replace("_", "-")
            secret_value = get_secret(secret_name)
            if secret_value:
                value = secret_value
        except Exception:
            # Secret Manager not available or failed, use env var
            pass

    return value


class Settings:
    """Application settings loaded from environment variables."""

    # Project
    PROJECT_NAME: str = "Hyperbot"
    VERSION: str = "0.1.0+ee7c8fb"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # API Server
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_KEY: str = os.getenv("API_KEY", "dev-key-change-in-production")

    # Hyperliquid
    HYPERLIQUID_SECRET_KEY: str = _get_config_value("HYPERLIQUID_SECRET_KEY", "")
    HYPERLIQUID_WALLET_ADDRESS: str = _get_config_value("HYPERLIQUID_WALLET_ADDRESS", "")
    HYPERLIQUID_TESTNET: bool = os.getenv("HYPERLIQUID_TESTNET", "true").lower() == "true"

    # Trading defaults
    DEFAULT_LEVERAGE: int = int(os.getenv("DEFAULT_LEVERAGE", "3"))  # Conservative default (3x)
    MAX_LEVERAGE_WARNING: int = int(
        os.getenv("MAX_LEVERAGE_WARNING", "5")
    )  # Soft limit for warnings (5x recommended)

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = _get_config_value("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_AUTHORIZED_USERS: list[int] = [
        int(user_id.strip())
        for user_id in _get_config_value("TELEGRAM_AUTHORIZED_USERS", "").split(",")
        if user_id.strip()
    ]

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/hyperbot.log")

    @classmethod
    def validate(cls) -> None:
        """Validate required settings are present."""
        if not cls.HYPERLIQUID_TESTNET:
            # Only require these for mainnet
            required_fields = [
                ("HYPERLIQUID_SECRET_KEY", cls.HYPERLIQUID_SECRET_KEY),
                ("HYPERLIQUID_WALLET_ADDRESS", cls.HYPERLIQUID_WALLET_ADDRESS),
            ]

            missing = [name for name, value in required_fields if not value]

            if missing:
                raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls.ENVIRONMENT.lower() == "production"

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment."""
        return cls.ENVIRONMENT.lower() == "development"

    @classmethod
    def is_cloud_run(cls) -> bool:
        """Check if running on GCP Cloud Run."""
        # Cloud Run sets K_SERVICE environment variable
        return os.getenv("K_SERVICE") is not None

    @classmethod
    def is_cloud_environment(cls) -> bool:
        """Check if running in any cloud environment."""
        return (
            cls.is_cloud_run()
            or os.getenv("AWS_EXECUTION_ENV") is not None  # AWS Lambda/Fargate
            or os.getenv("WEBSITE_INSTANCE_ID") is not None  # Azure
        )


# Global settings instance
settings = Settings()
