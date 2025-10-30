"""
Hyperliquid service for interacting with the Hyperliquid API.
Provides a wrapper around the hyperliquid-python-sdk.
"""
from typing import Optional, Dict, Any
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from eth_account import Account

from src.config import logger, settings


class HyperliquidService:
    """Service for interacting with Hyperliquid exchange."""

    def __init__(self):
        """Initialize Hyperliquid service."""
        self.info: Optional[Info] = None
        self.exchange: Optional[Exchange] = None
        self._initialized = False

    def initialize(self) -> None:
        """
        Initialize Hyperliquid SDK clients.

        Raises:
            ValueError: If required configuration is missing
            Exception: If initialization fails
        """
        if self._initialized:
            logger.warning("HyperliquidService already initialized")
            return

        try:
            # Determine base URL
            base_url = (
                constants.TESTNET_API_URL
                if settings.HYPERLIQUID_TESTNET
                else constants.MAINNET_API_URL
            )

            logger.info(f"Initializing Hyperliquid SDK - Testnet: {settings.HYPERLIQUID_TESTNET}")
            logger.info(f"Using base URL: {base_url}")

            # Initialize Info API (read-only, no auth required)
            self.info = Info(base_url, skip_ws=True)
            logger.info("Hyperliquid Info API initialized")

            # Initialize Exchange API (requires wallet credentials)
            # Only initialize if we have credentials
            if settings.HYPERLIQUID_WALLET_ADDRESS and settings.HYPERLIQUID_SECRET_KEY:
                # Create wallet from secret key
                wallet = Account.from_key(settings.HYPERLIQUID_SECRET_KEY)

                self.exchange = Exchange(
                    wallet=wallet,
                    base_url=base_url,
                    account_address=settings.HYPERLIQUID_WALLET_ADDRESS,
                )
                logger.info("Hyperliquid Exchange API initialized")
                logger.info(f"Connected to wallet: {settings.HYPERLIQUID_WALLET_ADDRESS}")
            else:
                logger.warning("Exchange API not initialized - missing wallet credentials")
                logger.warning("Read-only operations will work, but trading will not be available")

            self._initialized = True
            logger.info("HyperliquidService initialization complete")

        except Exception as e:
            logger.error(f"Failed to initialize HyperliquidService: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Hyperliquid connection.

        Returns:
            Dict with health check results
        """
        if not self._initialized:
            return {
                "status": "error",
                "message": "Service not initialized",
                "info_api": False,
                "exchange_api": False,
            }

        result = {
            "status": "healthy",
            "testnet": settings.HYPERLIQUID_TESTNET,
            "info_api": False,
            "exchange_api": False,
            "wallet_address": settings.HYPERLIQUID_WALLET_ADDRESS if settings.HYPERLIQUID_WALLET_ADDRESS else None,
        }

        # Test Info API
        try:
            if self.info:
                # Try to fetch exchange metadata
                meta = self.info.meta()
                result["info_api"] = True
                result["available_pairs"] = len(meta.get("universe", []))
                logger.debug(f"Info API health check passed - {result['available_pairs']} pairs available")
        except Exception as e:
            logger.error(f"Info API health check failed: {e}")
            result["info_api_error"] = str(e)

        # Test Exchange API (if initialized)
        if self.exchange and settings.HYPERLIQUID_WALLET_ADDRESS:
            try:
                # Try to fetch user state
                user_state = self.info.user_state(settings.HYPERLIQUID_WALLET_ADDRESS)
                result["exchange_api"] = True
                result["account_value"] = user_state.get("marginSummary", {}).get("accountValue", "0")
                logger.debug(f"Exchange API health check passed - Account value: ${result['account_value']}")
            except Exception as e:
                logger.error(f"Exchange API health check failed: {e}")
                result["exchange_api_error"] = str(e)

        # Determine overall status
        if not result["info_api"]:
            result["status"] = "unhealthy"
        elif self.exchange and not result["exchange_api"]:
            result["status"] = "degraded"  # Info works but Exchange doesn't

        return result

    def get_info_client(self) -> Info:
        """
        Get the Info API client.

        Returns:
            Info client instance

        Raises:
            RuntimeError: If service not initialized
        """
        if not self._initialized or not self.info:
            raise RuntimeError("HyperliquidService not initialized. Call initialize() first.")
        return self.info

    def get_exchange_client(self) -> Exchange:
        """
        Get the Exchange API client.

        Returns:
            Exchange client instance

        Raises:
            RuntimeError: If service not initialized or Exchange not available
        """
        if not self._initialized:
            raise RuntimeError("HyperliquidService not initialized. Call initialize() first.")
        if not self.exchange:
            raise RuntimeError("Exchange API not available. Check wallet credentials.")
        return self.exchange


# Global service instance
hyperliquid_service = HyperliquidService()
