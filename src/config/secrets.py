"""
GCP Secret Manager integration for loading secrets.

This module provides utilities to load secrets from GCP Secret Manager
instead of using .env files in production.
"""

import os

from loguru import logger


def get_secret(secret_name: str, project_id: str | None = None) -> str | None:
    """
    Get a secret from GCP Secret Manager.

    Args:
        secret_name: Name of the secret (e.g., "lb-hyperbot-telegram-bot-token")
        project_id: GCP project ID (defaults to GCP_PROJECT env var)

    Returns:
        Secret value or None if not found

    Example:
        >>> token = get_secret("lb-hyperbot-telegram-bot-token")
        >>> if token:
        >>>     print(f"Got token: {token[:10]}...")
    """
    # Only import if needed (not required for local development)
    try:
        from google.cloud import secretmanager
    except ImportError:
        logger.warning("google-cloud-secret-manager not installed - using environment variables")
        return os.getenv(secret_name.upper().replace("-", "_"))

    project_id = project_id or os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        logger.warning("GCP_PROJECT not set - falling back to environment variables")
        return os.getenv(secret_name.upper().replace("-", "_"))

    try:
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"

        response = client.access_secret_version(name=secret_path)
        secret_value: str = response.payload.data.decode("UTF-8")

        logger.info(f"Loaded secret: {secret_name}")
        return secret_value

    except Exception as e:
        logger.warning(f"Failed to load secret {secret_name} from GCP: {e}")
        # Fallback to environment variable
        return os.getenv(secret_name.upper().replace("-", "_"))


def load_secrets_from_gcp() -> dict[str, str]:
    """
    Load all application secrets from GCP Secret Manager.

    Returns:
        Dictionary of secret name -> value

    Secrets loaded:
        - lb-hyperbot-telegram-bot-token
        - lb-hyperbot-hyperliquid-secret-key
        - lb-hyperbot-hyperliquid-wallet-address
        - lb-hyperbot-api-key (optional)
    """
    secrets = {}

    # Required secrets
    secret_names = [
        "lb-hyperbot-telegram-bot-token",
        "lb-hyperbot-hyperliquid-secret-key",
        "lb-hyperbot-hyperliquid-wallet-address",
    ]

    # Optional secrets
    optional_secrets = ["lb-hyperbot-api-key"]

    for secret_name in secret_names:
        value = get_secret(secret_name)
        if value:
            secrets[secret_name] = value
        else:
            logger.error(f"Required secret {secret_name} not found!")

    for secret_name in optional_secrets:
        value = get_secret(secret_name)
        if value:
            secrets[secret_name] = value

    return secrets
