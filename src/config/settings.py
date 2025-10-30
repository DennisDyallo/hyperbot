"""
Application configuration settings.
Loads configuration from environment variables.
"""
import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""

    # Project
    PROJECT_NAME: str = "Hyperbot"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # API Server
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_KEY: str = os.getenv("API_KEY", "dev-key-change-in-production")

    # Hyperliquid
    HYPERLIQUID_API_KEY: str = os.getenv("HYPERLIQUID_API_KEY", "")
    HYPERLIQUID_SECRET_KEY: str = os.getenv("HYPERLIQUID_SECRET_KEY", "")
    HYPERLIQUID_WALLET_ADDRESS: str = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "")
    HYPERLIQUID_TESTNET: bool = os.getenv("HYPERLIQUID_TESTNET", "true").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/hyperbot.log")

    @classmethod
    def validate(cls) -> None:
        """Validate required settings are present."""
        if not cls.HYPERLIQUID_TESTNET:
            # Only require these for mainnet
            required_fields = [
                ("HYPERLIQUID_API_KEY", cls.HYPERLIQUID_API_KEY),
                ("HYPERLIQUID_SECRET_KEY", cls.HYPERLIQUID_SECRET_KEY),
                ("HYPERLIQUID_WALLET_ADDRESS", cls.HYPERLIQUID_WALLET_ADDRESS),
            ]

            missing = [name for name, value in required_fields if not value]

            if missing:
                raise ValueError(
                    f"Missing required environment variables: {', '.join(missing)}"
                )

    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment."""
        return cls.ENVIRONMENT.lower() == "production"

    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development environment."""
        return cls.ENVIRONMENT.lower() == "development"


# Global settings instance
settings = Settings()
