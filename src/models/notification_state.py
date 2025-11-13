"""
Notification state persistence models.

Minimal state tracking for order fill notification recovery.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class NotificationState(BaseModel):
    """
    Persistent state for notification recovery.

    This is the minimal state needed to recover missed fills after bot restart.
    Stored in data/notification_state.json.
    """

    # Primary recovery anchor
    last_processed_timestamp: int = Field(
        ...,
        description="Last processed fill timestamp (milliseconds). "
        "Used to query missed fills on restart.",
    )

    # Deduplication cache (limited size to prevent unbounded growth)
    recent_fill_hashes: set[str] = Field(
        default_factory=set,
        description="Hashes of recently processed fills (last 1000). "
        "Used to prevent duplicate notifications.",
    )

    # WebSocket health tracking
    last_websocket_heartbeat: datetime | None = Field(
        None, description="Last successful WebSocket message received"
    )

    websocket_reconnect_count: int = Field(
        0, description="Number of times WebSocket has reconnected this session"
    )

    # Recovery metadata
    last_recovery_run: datetime | None = Field(
        None, description="Last time recovery process ran (on startup)"
    )

    recovery_fills_found: int = Field(
        0, description="Number of fills recovered in last recovery run"
    )

    class Config:
        """Pydantic model configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            set: lambda v: list(v),  # Serialize set as list
        }

    @classmethod
    def load(cls, file_path: Path) -> "NotificationState":
        """
        Load state from file.

        Args:
            file_path: Path to state file

        Returns:
            NotificationState: Loaded state or default if file doesn't exist

        Raises:
            ValueError: If state file is corrupted
        """
        if not file_path.exists():
            # Return default state (starting from now)
            return cls.create_default()

        try:
            with open(file_path) as f:
                data = json.load(f)

            # Handle set deserialization
            if "recent_fill_hashes" in data and isinstance(data["recent_fill_hashes"], list):
                data["recent_fill_hashes"] = set(data["recent_fill_hashes"])

            # Handle datetime deserialization
            if data.get("last_websocket_heartbeat"):
                data["last_websocket_heartbeat"] = datetime.fromisoformat(
                    data["last_websocket_heartbeat"]
                )
            if data.get("last_recovery_run"):
                data["last_recovery_run"] = datetime.fromisoformat(data["last_recovery_run"])

            return cls(**data)

        except Exception as e:
            raise ValueError(f"Failed to load notification state: {e}") from e

    def save(self, file_path: Path) -> None:
        """
        Save state to file (atomic write).

        Args:
            file_path: Path to state file
        """
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file, then rename
        temp_file = file_path.with_suffix(".tmp")

        try:
            # Get model data and convert sets to lists for JSON serialization
            data = self.model_dump()

            # Convert set to list for JSON
            if isinstance(data.get("recent_fill_hashes"), set):
                data["recent_fill_hashes"] = list(data["recent_fill_hashes"])

            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2, default=str)

            # Atomic rename
            temp_file.replace(file_path)

        except Exception:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise

    @classmethod
    def create_default(cls) -> "NotificationState":
        """
        Create default state (starting from now).

        Returns:
            NotificationState: Default state
        """
        now_ms = int(datetime.now(UTC).timestamp() * 1000)

        return cls(
            last_processed_timestamp=now_ms,
            recent_fill_hashes=set(),
            last_websocket_heartbeat=None,
            websocket_reconnect_count=0,
            last_recovery_run=None,
            recovery_fills_found=0,
        )

    def add_fill_hash(self, fill_hash: str) -> None:
        """
        Add fill hash to recent cache.

        Maintains maximum size of 1000 hashes (FIFO).

        Args:
            fill_hash: Hash of processed fill
        """
        self.recent_fill_hashes.add(fill_hash)

        # Limit cache size (keep most recent 1000)
        if len(self.recent_fill_hashes) > 1000:
            # Convert to list, remove oldest 100, convert back
            hashes_list = list(self.recent_fill_hashes)
            self.recent_fill_hashes = set(hashes_list[100:])

    def is_fill_processed(self, fill_hash: str) -> bool:
        """
        Check if fill has already been processed.

        Args:
            fill_hash: Hash of fill to check

        Returns:
            bool: True if already processed
        """
        return fill_hash in self.recent_fill_hashes

    def update_timestamp(self, timestamp_ms: int) -> None:
        """
        Update last processed timestamp if newer.

        Args:
            timestamp_ms: New timestamp in milliseconds
        """
        if timestamp_ms > self.last_processed_timestamp:
            self.last_processed_timestamp = timestamp_ms

    def record_websocket_heartbeat(self) -> None:
        """Record successful WebSocket message reception."""
        self.last_websocket_heartbeat = datetime.now(UTC)

    def record_websocket_reconnect(self) -> None:
        """Increment reconnect counter."""
        self.websocket_reconnect_count += 1

    def record_recovery(self, fills_found: int) -> None:
        """
        Record recovery run completion.

        Args:
            fills_found: Number of fills recovered
        """
        self.last_recovery_run = datetime.now(UTC)
        self.recovery_fills_found = fills_found

    def get_age_seconds(self) -> float:
        """
        Get age of last processed timestamp in seconds.

        Returns:
            float: Seconds since last processed fill
        """
        now_ms = int(datetime.now(UTC).timestamp() * 1000)
        return (now_ms - self.last_processed_timestamp) / 1000

    def is_websocket_healthy(self, max_silence_seconds: int = 60) -> bool:
        """
        Check if WebSocket is healthy (recent heartbeat).

        Args:
            max_silence_seconds: Maximum seconds without heartbeat

        Returns:
            bool: True if healthy (recent heartbeat)
        """
        if not self.last_websocket_heartbeat:
            return False

        silence_seconds = (datetime.now(UTC) - self.last_websocket_heartbeat).total_seconds()
        return silence_seconds < max_silence_seconds


class StateManager:
    """
    Manager for notification state persistence.

    Provides high-level operations with automatic save.
    """

    def __init__(self, state_file: Path = Path("data/notification_state.json")):
        """
        Initialize state manager.

        Args:
            state_file: Path to state file
        """
        self.state_file = state_file
        self.state = NotificationState.load(state_file)

    def save(self) -> None:
        """Save current state to file."""
        self.state.save(self.state_file)

    def add_processed_fill(self, fill_hash: str, timestamp_ms: int) -> None:
        """
        Add processed fill and update timestamp.

        Automatically saves state.

        Args:
            fill_hash: Hash of processed fill
            timestamp_ms: Fill timestamp in milliseconds
        """
        self.state.add_fill_hash(fill_hash)
        self.state.update_timestamp(timestamp_ms)
        self.save()

    def is_fill_processed(self, fill_hash: str) -> bool:
        """
        Check if fill has been processed.

        Args:
            fill_hash: Hash to check

        Returns:
            bool: True if already processed
        """
        return self.state.is_fill_processed(fill_hash)

    def record_websocket_heartbeat(self) -> None:
        """Record WebSocket heartbeat (don't save for performance)."""
        self.state.record_websocket_heartbeat()

    def record_websocket_reconnect(self) -> None:
        """Record WebSocket reconnection and save."""
        self.state.record_websocket_reconnect()
        self.save()

    def record_recovery(self, fills_found: int) -> None:
        """
        Record recovery completion and save.

        Args:
            fills_found: Number of fills recovered
        """
        self.state.record_recovery(fills_found)
        self.save()

    def get_last_processed_timestamp(self) -> int:
        """
        Get last processed timestamp.

        Returns:
            int: Timestamp in milliseconds
        """
        return self.state.last_processed_timestamp
