"""
Order monitoring service for real-time fill notifications.

Monitors Hyperliquid order fills via WebSocket and sends Telegram notifications.
Implements deduplication and state persistence for reliability.

Reference: docs/research/hyperliquid_fills_api.md
"""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config import logger, settings
from src.models.notification_state import StateManager
from src.models.order_fill_event import OrderFillEvent
from src.services.hyperliquid_service import hyperliquid_service


class OrderMonitorService:
    """
    Monitors order fills and sends Telegram notifications.

    Architecture:
    - WebSocket subscription for real-time fills
    - State persistence for deduplication
    - Automatic reconnection with exponential backoff
    - Telegram integration for notifications

    Example:
        >>> monitor = OrderMonitorService()
        >>> await monitor.start()  # Starts WebSocket monitoring
        >>> # ... fills are automatically notified ...
        >>> await monitor.stop()
    """

    def __init__(
        self,
        state_file: Path = Path("data/notification_state.json"),
        telegram_chat_id: int | None = None,
    ):
        """
        Initialize order monitor service.

        Args:
            state_file: Path to state persistence file
            telegram_chat_id: Telegram chat ID for notifications.
                Defaults to first authorized user from settings.
        """
        self.state_manager = StateManager(state_file)
        self.telegram_chat_id = telegram_chat_id or self._get_default_chat_id()
        self._running = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._base_reconnect_delay = 1.0  # seconds
        self._max_reconnect_delay = 300.0  # 5 minutes
        self._backup_polling_task: asyncio.Task[None] | None = None
        self._backup_polling_interval = 300  # 5 minutes in seconds

        logger.info(
            f"OrderMonitorService initialized - "
            f"state_file={state_file}, chat_id={self.telegram_chat_id}"
        )

    def _get_default_chat_id(self) -> int:
        """
        Get default Telegram chat ID from settings.

        Returns:
            First authorized user ID

        Raises:
            ValueError: If no authorized users configured
        """
        if not settings.TELEGRAM_AUTHORIZED_USERS:
            raise ValueError(
                "No Telegram authorized users configured. Set TELEGRAM_AUTHORIZED_USERS in .env"
            )

        # settings.TELEGRAM_AUTHORIZED_USERS can be either list or string
        # If it's a list, use first item; if string, parse comma-separated
        if isinstance(settings.TELEGRAM_AUTHORIZED_USERS, list):
            user_ids = settings.TELEGRAM_AUTHORIZED_USERS
        else:
            user_ids = [int(uid.strip()) for uid in settings.TELEGRAM_AUTHORIZED_USERS.split(",")]

        if not user_ids:
            raise ValueError("TELEGRAM_AUTHORIZED_USERS is empty")

        logger.info(f"Using default chat ID: {user_ids[0]}")
        return user_ids[0]

    async def start(self) -> None:
        """
        Start monitoring order fills via WebSocket.

        This method:
        1. Initializes Hyperliquid WebSocket
        2. Subscribes to userEvents
        3. Starts listening for fill events

        Raises:
            RuntimeError: If already running or Hyperliquid not initialized
        """
        if self._running:
            logger.warning("OrderMonitorService already running")
            return

        # Ensure Hyperliquid is initialized
        if not hyperliquid_service.is_initialized():
            logger.info("Initializing Hyperliquid service...")
            hyperliquid_service.initialize()

        # Initialize WebSocket
        if not hyperliquid_service.is_websocket_initialized():
            logger.info("Initializing WebSocket...")
            hyperliquid_service.initialize_websocket()

        logger.info("Starting order fill monitoring...")

        # Subscribe to user events
        hyperliquid_service.subscribe_user_events(
            callback=self._on_websocket_event,
            user_address=settings.HYPERLIQUID_WALLET_ADDRESS,
        )

        self._running = True
        logger.info("✅ Order fill monitoring started")

        # Run startup recovery to catch any missed fills
        await self._run_startup_recovery()

        # Start periodic backup polling task
        self._backup_polling_task = asyncio.create_task(self._backup_polling_loop())
        logger.info(
            f"📡 Started backup polling (every {self._backup_polling_interval}s)"
        )

    async def _run_startup_recovery(self) -> None:
        """
        Run startup recovery to catch fills missed while bot was offline.

        This queries the user_fills() API for any fills newer than our
        last processed timestamp and notifies them.

        Reference: docs/research/hyperliquid_fills_api.md - Recovery Query Strategy
        """
        logger.info("Running startup recovery...")

        try:
            # Get last processed timestamp from state
            last_timestamp_ms = self.state_manager.get_last_processed_timestamp()

            logger.info(f"Last processed timestamp: {last_timestamp_ms}ms")
            logger.info(
                f"Recovery window: {datetime.fromtimestamp(last_timestamp_ms / 1000, tz=UTC)}"
            )

            # Query all fills from Hyperliquid
            info_client = hyperliquid_service.get_info_client()
            if not settings.HYPERLIQUID_WALLET_ADDRESS:
                logger.error("Cannot run recovery: wallet address not configured")
                return

            all_fills = info_client.user_fills(settings.HYPERLIQUID_WALLET_ADDRESS)

            logger.info(f"Retrieved {len(all_fills)} total fills from API")

            # Filter for fills newer than last processed
            # Note: user_fills() returns newest first, so we can stop early
            missed_fills = []
            for fill_data in all_fills:
                fill_time = fill_data.get("time", 0)

                # Stop once we hit older fills (optimization)
                if fill_time <= last_timestamp_ms:
                    break

                # Parse into OrderFillEvent
                try:
                    fill_event = OrderFillEvent(**fill_data)
                    missed_fills.append(fill_event)
                except Exception as e:
                    logger.error(f"Failed to parse fill during recovery: {e}")
                    continue

            # Sort oldest first for processing
            missed_fills.reverse()

            logger.info(f"Found {len(missed_fills)} missed fills")

            if missed_fills:
                # Process missed fills
                await self._process_missed_fills(missed_fills)

                # Record recovery run
                self.state_manager.record_recovery(len(missed_fills))

                logger.info(f"✅ Recovery complete - processed {len(missed_fills)} missed fills")
            else:
                logger.info("✅ Recovery complete - no missed fills")
                self.state_manager.record_recovery(0)

        except Exception as e:
            logger.exception(f"Startup recovery failed: {e}")
            # Don't raise - recovery failure shouldn't prevent bot startup

    async def _process_missed_fills(self, fills: list[OrderFillEvent]) -> None:
        """
        Process missed fills from recovery.

        If >5 fills, send batch notification. Otherwise send individual.

        Args:
            fills: List of missed fill events (oldest first)
        """
        if not fills:
            return

        # Threshold for batch vs individual notifications
        batch_threshold = 5

        if len(fills) > batch_threshold:
            logger.info(f"Sending batch notification for {len(fills)} fills")
            await self._send_batch_notification(fills)
        else:
            logger.info(f"Sending individual notifications for {len(fills)} fills")
            for fill in fills:
                await self._process_fill(fill, is_recovery=True)

    async def _send_batch_notification(self, fills: list[OrderFillEvent]) -> None:
        """
        Send batch notification for multiple fills.

        Args:
            fills: List of fill events
        """
        # Build summary message
        summary_lines = [
            "🔄 **Recovery: Multiple Fills Detected**",
            "",
            f"Found {len(fills)} fills while bot was offline:",
            "",
        ]

        # Group by coin
        fills_by_coin: dict[str, list[OrderFillEvent]] = {}
        for fill in fills:
            if fill.coin not in fills_by_coin:
                fills_by_coin[fill.coin] = []
            fills_by_coin[fill.coin].append(fill)

        # Summarize by coin
        for coin, coin_fills in fills_by_coin.items():
            buy_fills = [f for f in coin_fills if f.side == "B"]
            sell_fills = [f for f in coin_fills if f.side == "S"]

            summary_lines.append(f"**{coin}**:")

            if buy_fills:
                total_buy = sum(f.size for f in buy_fills)
                summary_lines.append(f"  • {len(buy_fills)} BUY fills - Total: {total_buy} {coin}")

            if sell_fills:
                total_sell = sum(f.size for f in sell_fills)
                summary_lines.append(
                    f"  • {len(sell_fills)} SELL fills - Total: {total_sell} {coin}"
                )

            summary_lines.append("")

        # Add time range
        oldest = fills[0].timestamp
        newest = fills[-1].timestamp
        summary_lines.append(f"Time range: {oldest.strftime('%Y-%m-%d %H:%M')} to {newest.strftime('%H:%M')} UTC")

        summary_text = "\n".join(summary_lines)

        # Send notification
        logger.info(f"📱 [Batch Notification]\n{summary_text}")

        # TODO: Integrate with Telegram (Phase 5D)
        # await bot.send_message(chat_id=self.telegram_chat_id, text=summary_text)

        # Add all fills to state
        for fill in fills:
            fill_hash = fill.calculate_hash()
            self.state_manager.add_processed_fill(fill_hash, fill.timestamp_ms)

    async def _backup_polling_loop(self) -> None:
        """
        Periodic backup polling to catch any fills missed by WebSocket.

        Runs every 5 minutes and queries user_fills() API to ensure no fills
        were missed due to WebSocket issues.

        This is a safety net - under normal operation, WebSocket should catch
        all fills in real-time.
        """
        logger.info("Backup polling loop started")

        try:
            while self._running:
                # Wait for polling interval
                await asyncio.sleep(self._backup_polling_interval)

                if not self._running:
                    break

                logger.debug("Running backup polling check...")

                try:
                    # Query fills since last processed timestamp
                    last_timestamp_ms = self.state_manager.get_last_processed_timestamp()

                    info_client = hyperliquid_service.get_info_client()
                    if not settings.HYPERLIQUID_WALLET_ADDRESS:
                        logger.warning("Backup polling skipped: wallet address not configured")
                        continue

                    all_fills = info_client.user_fills(settings.HYPERLIQUID_WALLET_ADDRESS)

                    # Filter for new fills
                    new_fills = []
                    for fill_data in all_fills:
                        fill_time = fill_data.get("time", 0)

                        if fill_time <= last_timestamp_ms:
                            break  # Optimization: stop at older fills

                        try:
                            fill_event = OrderFillEvent(**fill_data)

                            # Check if already processed (deduplication)
                            fill_hash = fill_event.calculate_hash()
                            if not self.state_manager.is_fill_processed(fill_hash):
                                new_fills.append(fill_event)
                        except Exception as e:
                            logger.error(f"Failed to parse fill in backup polling: {e}")
                            continue

                    if new_fills:
                        logger.warning(
                            f"⚠️ Backup polling found {len(new_fills)} fills missed by WebSocket!"
                        )

                        # Sort oldest first
                        new_fills.reverse()

                        # Process missed fills
                        await self._process_missed_fills(new_fills)

                        logger.info(
                            f"✅ Backup polling processed {len(new_fills)} missed fills"
                        )
                    else:
                        logger.debug("Backup polling: no new fills")

                except Exception as e:
                    logger.exception(f"Error in backup polling: {e}")
                    # Continue polling despite errors

        except asyncio.CancelledError:
            logger.info("Backup polling loop cancelled")
            raise

    async def stop(self) -> None:
        """
        Stop monitoring order fills.

        Saves final state and cleans up resources.
        """
        if not self._running:
            logger.warning("OrderMonitorService not running")
            return

        logger.info("Stopping order fill monitoring...")

        self._running = False

        # Cancel backup polling task
        if self._backup_polling_task:
            self._backup_polling_task.cancel()
            try:
                await self._backup_polling_task
            except asyncio.CancelledError:
                logger.debug("Backup polling task cancelled")
            self._backup_polling_task = None

        # Save final state
        self.state_manager.save()

        logger.info("✅ Order fill monitoring stopped")

    def _on_websocket_event(self, event: dict[str, Any]) -> None:
        """
        Handle WebSocket event (callback from Hyperliquid SDK).

        This is called synchronously by the SDK, so we need to be careful
        about blocking operations.

        Args:
            event: WebSocket event from Hyperliquid
        """
        try:
            # Record heartbeat for health tracking
            self.state_manager.state.record_websocket_heartbeat()

            # Log raw event (for debugging)
            logger.debug(f"WebSocket event received: {event}")

            # Parse and filter for fill events
            fill_event = self._parse_fill_event(event)

            if fill_event:
                logger.info(f"Fill event detected: {fill_event.coin} {fill_event.side_text}")
                # Process the fill (deduplication, notification)
                asyncio.create_task(self._process_fill(fill_event))

        except Exception as e:
            logger.exception(f"Error handling WebSocket event: {e}")

    def _parse_fill_event(self, event: dict[str, Any]) -> OrderFillEvent | None:
        """
        Parse WebSocket event and extract fill if present.

        Reference: docs/research/hyperliquid_fills_api.md - WebSocket API

        Args:
            event: Raw WebSocket event

        Returns:
            OrderFillEvent if this is a fill event, None otherwise
        """
        # Check if this is a userEvents channel event
        if event.get("channel") != "userEvents":
            logger.debug(f"Ignoring non-userEvents channel: {event.get('channel')}")
            return None

        # Get event data
        data = event.get("data", {})

        # Check if this is a fill event (data contains "fills" key)
        # Structure: {"channel": "userEvents", "data": {"fills": [...]}}
        fills = data.get("fills")
        if not fills:
            logger.debug("Event does not contain fills")
            return None

        # Process first fill (usually events contain single fill)
        # If multiple fills, we'll process them separately in future enhancement
        if isinstance(fills, list) and len(fills) > 0:
            fill_data = fills[0]

            try:
                # Parse into OrderFillEvent model
                fill_event = OrderFillEvent(**fill_data)
                logger.debug(f"Parsed fill event: {fill_event.coin} @ ${fill_event.price}")
                return fill_event

            except Exception as e:
                logger.error(f"Failed to parse fill data: {e}")
                logger.debug(f"Fill data: {fill_data}")
                return None

        return None

    async def _process_fill(self, fill: OrderFillEvent, is_recovery: bool = False) -> None:
        """
        Process fill event: deduplication, state update, notification.

        Args:
            fill: Parsed fill event
            is_recovery: Whether this is from recovery (adds recovery tag to notification)
        """
        try:
            # Calculate fill hash for deduplication
            fill_hash = fill.calculate_hash()

            # Check if already processed
            if self.state_manager.is_fill_processed(fill_hash):
                logger.debug(f"Fill already processed (hash={fill_hash}), skipping")
                return

            logger.info(f"Processing new fill: {fill.coin} {fill.side_text} {fill.size}")

            # Send Telegram notification
            await self._send_telegram_notification(fill, is_recovery=is_recovery)

            # Update state (add hash, update timestamp)
            self.state_manager.add_processed_fill(fill_hash, fill.timestamp_ms)

            logger.info(f"✅ Fill processed and notified (hash={fill_hash})")

        except Exception as e:
            logger.exception(f"Error processing fill: {e}")

    async def _send_telegram_notification(
        self, fill: OrderFillEvent, is_recovery: bool = False
    ) -> None:
        """
        Send Telegram notification for fill event.

        Args:
            fill: Fill event to notify
            is_recovery: If True, adds recovery tag to notification

        Raises:
            Exception: If notification fails
        """
        # TODO: Integrate with Telegram bot (Phase 5D)
        # For now, just log the notification text

        notification_text = fill.to_notification_text(include_emoji=True)

        # Add recovery tag if this is from recovery
        if is_recovery:
            notification_text = f"🔄 **[RECOVERY]**\n\n{notification_text}"

        logger.info(
            f"📱 [Telegram Notification{' - Recovery' if is_recovery else ''}]\n"
            f"Chat ID: {self.telegram_chat_id}\n{notification_text}"
        )

        # Placeholder for actual Telegram integration:
        # from src.bot.main import bot
        # await bot.send_message(
        #     chat_id=self.telegram_chat_id,
        #     text=notification_text,
        #     parse_mode="Markdown"
        # )

    async def _reconnect_with_backoff(self) -> None:
        """
        Attempt to reconnect with exponential backoff.

        Called when WebSocket connection drops.
        """
        self._reconnect_attempts += 1

        if self._reconnect_attempts > self._max_reconnect_attempts:
            logger.error(
                f"Max reconnect attempts ({self._max_reconnect_attempts}) reached. Giving up."
            )
            self._running = False
            return

        # Calculate backoff delay (exponential with jitter)
        delay = min(
            self._base_reconnect_delay * (2 ** (self._reconnect_attempts - 1)),
            self._max_reconnect_delay,
        )

        logger.warning(
            f"Reconnecting in {delay:.1f}s (attempt {self._reconnect_attempts}/"
            f"{self._max_reconnect_attempts})"
        )

        await asyncio.sleep(delay)

        try:
            # Re-subscribe to WebSocket
            hyperliquid_service.subscribe_user_events(
                callback=self._on_websocket_event,
                user_address=settings.HYPERLIQUID_WALLET_ADDRESS,
            )

            # Record reconnection
            self.state_manager.record_websocket_reconnect()

            logger.info(f"✅ Reconnected successfully (attempt {self._reconnect_attempts})")

            # Reset reconnect counter on success
            self._reconnect_attempts = 0

        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            # Try again
            await self._reconnect_with_backoff()

    def get_status(self) -> dict[str, Any]:
        """
        Get monitor status and statistics.

        Returns:
            Status dictionary with:
            - running: bool
            - reconnect_attempts: int
            - last_heartbeat: datetime | None
            - websocket_reconnects: int
            - last_processed_timestamp: datetime
            - state_age_seconds: float
        """
        return {
            "running": self._running,
            "reconnect_attempts": self._reconnect_attempts,
            "last_heartbeat": self.state_manager.state.last_websocket_heartbeat,
            "websocket_reconnects": self.state_manager.state.websocket_reconnect_count,
            "last_processed_timestamp": datetime.fromtimestamp(
                self.state_manager.state.last_processed_timestamp / 1000, tz=UTC
            ),
            "state_age_seconds": self.state_manager.state.get_age_seconds(),
            "websocket_healthy": self.state_manager.state.is_websocket_healthy(),
        }


# Global service instance
order_monitor_service = OrderMonitorService()
