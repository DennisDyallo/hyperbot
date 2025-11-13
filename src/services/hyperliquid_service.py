"""
Hyperliquid service for interacting with the Hyperliquid API.
Provides a wrapper around the hyperliquid-python-sdk.
"""

from collections.abc import Callable
from typing import Any

from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

from src.config import logger, settings


class HyperliquidService:
    """Service for interacting with Hyperliquid exchange."""

    def __init__(self):
        """Initialize Hyperliquid service."""
        self.info: Info | None = None
        self.info_ws: Info | None = None  # WebSocket-enabled Info client
        self.exchange: Exchange | None = None
        self._initialized = False
        self._websocket_initialized = False

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

    def health_check(self) -> dict[str, Any]:
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
            "wallet_address": settings.HYPERLIQUID_WALLET_ADDRESS
            if settings.HYPERLIQUID_WALLET_ADDRESS
            else None,
        }

        # Test Info API
        try:
            if self.info:
                # Try to fetch exchange metadata
                meta = self.info.meta()
                result["info_api"] = True
                result["available_pairs"] = len(meta.get("universe", []))
                logger.debug(
                    f"Info API health check passed - {result['available_pairs']} pairs available"
                )
        except Exception as e:
            logger.error(f"Info API health check failed: {e}")
            result["info_api_error"] = str(e)

        # Test Exchange API (if initialized)
        if self.exchange and settings.HYPERLIQUID_WALLET_ADDRESS and self.info:
            try:
                # Try to fetch user state
                user_state = self.info.user_state(settings.HYPERLIQUID_WALLET_ADDRESS)
                result["exchange_api"] = True
                result["account_value"] = user_state.get("marginSummary", {}).get(
                    "accountValue", "0"
                )
                logger.debug(
                    f"Exchange API health check passed - Account value: ${result['account_value']}"
                )
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

    def is_initialized(self) -> bool:
        """
        Check if service is initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized

    async def place_limit_order(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        price: float,
        reduce_only: bool = False,
        time_in_force: str = "Gtc",
    ) -> dict[str, Any]:
        """
        Place a limit order.

        Args:
            coin: Asset symbol (e.g., 'BTC', 'ETH')
            is_buy: True for buy, False for sell
            size: Order size
            price: Limit price
            reduce_only: Only reduce existing position
            time_in_force: Time in force ('Gtc', 'Ioc', 'Alo')

        Returns:
            Order result from API

        Raises:
            RuntimeError: If exchange not initialized

        Example:
            >>> result = await service.place_limit_order(
            ...     coin="BTC",
            ...     is_buy=True,
            ...     size=0.1,
            ...     price=50000.0
            ... )
        """
        if not self._initialized or not self.exchange:
            raise RuntimeError("Exchange API not initialized")

        logger.info(
            f"Placing limit order: {coin} {'BUY' if is_buy else 'SELL'} "
            f"{size} @ ${price:.2f} (TIF={time_in_force}, reduce_only={reduce_only})"
        )

        try:
            result = self.exchange.order(
                name=coin,
                is_buy=is_buy,
                sz=size,
                limit_px=price,
                order_type={"limit": {"tif": time_in_force}},
                reduce_only=reduce_only,
            )

            logger.debug(f"Limit order result: {result}")
            return result  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            raise

    async def cancel_order(self, coin: str, order_id: int) -> dict[str, Any]:
        """
        Cancel an order.

        Args:
            coin: Asset symbol
            order_id: Order ID to cancel

        Returns:
            Cancellation result from API

        Raises:
            RuntimeError: If exchange not initialized

        Example:
            >>> result = await service.cancel_order(coin="BTC", order_id=12345)
        """
        if not self._initialized or not self.exchange:
            raise RuntimeError("Exchange API not initialized")

        logger.info(f"Cancelling order: {coin} order_id={order_id}")

        try:
            result = self.exchange.cancel(name=coin, oid=order_id)

            logger.debug(f"Cancel result: {result}")
            return result  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise

    async def get_open_orders(self) -> list:
        """
        Get all open orders for the user.

        Returns:
            List of open orders

        Raises:
            RuntimeError: If service not initialized

        Example:
            >>> orders = await service.get_open_orders()
            >>> print(f"Found {len(orders)} open orders")
        """
        if not self._initialized or not self.info:
            raise RuntimeError("Service not initialized")

        if not settings.HYPERLIQUID_WALLET_ADDRESS:
            raise RuntimeError("Wallet address not configured")

        logger.debug(f"Fetching open orders for {settings.HYPERLIQUID_WALLET_ADDRESS}")

        try:
            orders = self.info.open_orders(settings.HYPERLIQUID_WALLET_ADDRESS)

            logger.debug(f"Retrieved {len(orders)} open orders")
            return orders  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            raise

    def initialize_websocket(self) -> None:
        """
        Initialize WebSocket-enabled Info client for real-time subscriptions.

        This creates a separate Info client with WebSocket support (skip_ws=False).
        The regular Info client (self.info) remains WebSocket-free for polling.

        Raises:
            RuntimeError: If base service not initialized
            Exception: If WebSocket initialization fails

        Example:
            >>> service.initialize()
            >>> service.initialize_websocket()
            >>> service.subscribe_user_events(my_callback)
        """
        if not self._initialized:
            raise RuntimeError(
                "Base service must be initialized first. Call initialize() before "
                "initialize_websocket()"
            )

        if self._websocket_initialized:
            logger.warning("WebSocket already initialized")
            return

        try:
            # Determine base URL (same as regular initialization)
            base_url = (
                constants.TESTNET_API_URL
                if settings.HYPERLIQUID_TESTNET
                else constants.MAINNET_API_URL
            )

            logger.info("Initializing WebSocket-enabled Info client")

            # Create Info client with WebSocket support (skip_ws=False)
            self.info_ws = Info(base_url, skip_ws=False)

            self._websocket_initialized = True
            logger.info("WebSocket Info client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize WebSocket: {e}")
            raise

    def subscribe_user_events(
        self, callback: Callable[[dict[str, Any]], None], user_address: str | None = None
    ) -> None:
        """
        Subscribe to user events (fills, funding, liquidations) via WebSocket.

        Reference: docs/research/hyperliquid_fills_api.md - WebSocket API

        Args:
            callback: Function called for each event. Receives event dict with:
                - channel: "userEvents"
                - data: Event data (fills, orders, funding, etc.)
            user_address: Wallet address to monitor. Defaults to configured wallet.

        Raises:
            RuntimeError: If WebSocket not initialized
            ValueError: If user_address not provided and not configured

        Example:
            >>> def on_event(event: dict):
            ...     if event.get("channel") == "userEvents":
            ...         print(f"User event: {event['data']}")
            >>> service.subscribe_user_events(on_event)
        """
        if not self._websocket_initialized or not self.info_ws:
            raise RuntimeError("WebSocket not initialized. Call initialize_websocket() first.")

        # Use provided address or fall back to configured address
        address = user_address or settings.HYPERLIQUID_WALLET_ADDRESS
        if not address:
            raise ValueError(
                "user_address must be provided or HYPERLIQUID_WALLET_ADDRESS must be configured"
            )

        logger.info(f"Subscribing to userEvents for {address}")

        try:
            # Subscribe to userEvents channel
            # The callback will be invoked for each event received
            self.info_ws.subscribe(
                subscription={"type": "userEvents", "user": address}, callback=callback
            )

            logger.info(f"Successfully subscribed to userEvents for {address}")

        except Exception as e:
            logger.error(f"Failed to subscribe to userEvents: {e}")
            raise

    def is_websocket_initialized(self) -> bool:
        """
        Check if WebSocket is initialized.

        Returns:
            True if WebSocket initialized, False otherwise
        """
        return self._websocket_initialized


# Global service instance
hyperliquid_service = HyperliquidService()
