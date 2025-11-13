"""
Unit tests for notification state models.
"""

import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.models.notification_state import NotificationState, StateManager


class TestNotificationState:
    """Test NotificationState model."""

    def test_create_default(self):
        """Test creating default state."""
        state = NotificationState.create_default()

        assert state.last_processed_timestamp > 0
        assert len(state.recent_fill_hashes) == 0
        assert state.last_websocket_heartbeat is None
        assert state.websocket_reconnect_count == 0
        assert state.last_recovery_run is None
        assert state.recovery_fills_found == 0

    def test_add_fill_hash(self):
        """Test adding fill hash to cache."""
        state = NotificationState.create_default()

        # Add single hash
        state.add_fill_hash("hash1")
        assert "hash1" in state.recent_fill_hashes
        assert len(state.recent_fill_hashes) == 1

        # Add multiple hashes
        state.add_fill_hash("hash2")
        state.add_fill_hash("hash3")
        assert len(state.recent_fill_hashes) == 3

    def test_add_fill_hash_deduplication(self):
        """Test that adding same hash doesn't create duplicates."""
        state = NotificationState.create_default()

        state.add_fill_hash("hash1")
        state.add_fill_hash("hash1")
        state.add_fill_hash("hash1")

        assert len(state.recent_fill_hashes) == 1

    def test_add_fill_hash_lru_eviction(self):
        """Test that cache is limited to 1000 entries."""
        state = NotificationState.create_default()

        # Add 1100 hashes
        for i in range(1100):
            state.add_fill_hash(f"hash{i}")

        # Should be capped at 1000
        assert len(state.recent_fill_hashes) == 1000

        # Note: Since sets are unordered, we can't test which specific hashes were evicted
        # The implementation converts to list, removes first 100, then converts back to set

    def test_is_fill_processed(self):
        """Test checking if fill is processed."""
        state = NotificationState.create_default()

        state.add_fill_hash("hash1")

        assert state.is_fill_processed("hash1") is True
        assert state.is_fill_processed("hash2") is False

    def test_update_timestamp(self):
        """Test updating last processed timestamp."""
        state = NotificationState.create_default()
        initial_timestamp = state.last_processed_timestamp

        # Update with newer timestamp
        new_timestamp = initial_timestamp + 1000
        state.update_timestamp(new_timestamp)
        assert state.last_processed_timestamp == new_timestamp

        # Update with older timestamp (should be ignored)
        old_timestamp = initial_timestamp - 1000
        state.update_timestamp(old_timestamp)
        assert state.last_processed_timestamp == new_timestamp  # Unchanged

    def test_record_websocket_heartbeat(self):
        """Test recording WebSocket heartbeat."""
        state = NotificationState.create_default()

        assert state.last_websocket_heartbeat is None

        state.record_websocket_heartbeat()

        assert state.last_websocket_heartbeat is not None
        assert isinstance(state.last_websocket_heartbeat, datetime)

    def test_record_websocket_reconnect(self):
        """Test recording WebSocket reconnect."""
        state = NotificationState.create_default()

        assert state.websocket_reconnect_count == 0

        state.record_websocket_reconnect()
        assert state.websocket_reconnect_count == 1

        state.record_websocket_reconnect()
        assert state.websocket_reconnect_count == 2

    def test_record_recovery(self):
        """Test recording recovery run."""
        state = NotificationState.create_default()

        assert state.last_recovery_run is None
        assert state.recovery_fills_found == 0

        state.record_recovery(5)

        assert state.last_recovery_run is not None
        assert state.recovery_fills_found == 5

    def test_get_age_seconds(self):
        """Test getting age of last processed timestamp."""
        state = NotificationState.create_default()

        age = state.get_age_seconds()

        # Should be very small (just created)
        assert 0 <= age < 1

    def test_is_websocket_healthy_no_heartbeat(self):
        """Test WebSocket health check with no heartbeat."""
        state = NotificationState.create_default()

        assert state.is_websocket_healthy() is False

    def test_is_websocket_healthy_recent_heartbeat(self):
        """Test WebSocket health check with recent heartbeat."""
        state = NotificationState.create_default()

        state.record_websocket_heartbeat()

        assert state.is_websocket_healthy() is True

    def test_save_and_load(self):
        """Test saving and loading state from file."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_state.json"

            # Create state with data
            state = NotificationState.create_default()
            state.add_fill_hash("hash1")
            state.add_fill_hash("hash2")
            state.record_websocket_heartbeat()
            state.record_websocket_reconnect()
            state.record_recovery(3)

            # Save state
            state.save(file_path)

            # Load state
            loaded_state = NotificationState.load(file_path)

            # Verify data
            assert loaded_state.last_processed_timestamp == state.last_processed_timestamp
            assert len(loaded_state.recent_fill_hashes) == 2
            assert "hash1" in loaded_state.recent_fill_hashes
            assert "hash2" in loaded_state.recent_fill_hashes
            assert loaded_state.websocket_reconnect_count == 1
            assert loaded_state.recovery_fills_found == 3

    def test_save_creates_directory(self):
        """Test that save creates parent directory if needed."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "subdir" / "test_state.json"

            state = NotificationState.create_default()
            state.save(file_path)

            assert file_path.exists()

    def test_save_atomic_write(self):
        """Test that save uses atomic write (temp file + rename)."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_state.json"

            state = NotificationState.create_default()
            state.save(file_path)

            # Temp file should not exist after successful save
            temp_file = file_path.with_suffix(".tmp")
            assert not temp_file.exists()

            # Final file should exist
            assert file_path.exists()

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file returns default state."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "nonexistent.json"

            state = NotificationState.load(file_path)

            # Should return default state
            assert state.last_processed_timestamp > 0
            assert len(state.recent_fill_hashes) == 0

    def test_load_corrupted_file(self):
        """Test loading corrupted file raises ValueError."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "corrupted.json"

            # Write invalid JSON
            with open(file_path, "w") as f:
                f.write("invalid json {{{")

            with pytest.raises(ValueError, match="Failed to load notification state"):
                NotificationState.load(file_path)

    def test_set_serialization(self):
        """Test that sets are properly serialized to lists in JSON."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_state.json"

            # Create state with fill hashes
            state = NotificationState.create_default()
            state.add_fill_hash("hash1")
            state.add_fill_hash("hash2")

            # Save state
            state.save(file_path)

            # Read raw JSON
            with open(file_path) as f:
                data = json.load(f)

            # Verify recent_fill_hashes is a list, not the string "set()"
            assert isinstance(data["recent_fill_hashes"], list)
            assert len(data["recent_fill_hashes"]) == 2


class TestStateManager:
    """Test StateManager class."""

    def test_init_creates_state(self):
        """Test that initialization creates or loads state."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_state.json"

            manager = StateManager(file_path)

            assert manager.state is not None
            assert isinstance(manager.state, NotificationState)

    def test_save(self):
        """Test saving state."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_state.json"

            manager = StateManager(file_path)
            manager.save()

            assert file_path.exists()

    def test_add_processed_fill(self):
        """Test adding processed fill (with automatic save)."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_state_add_fill.json"

            manager = StateManager(file_path)

            # Set a baseline timestamp first
            manager.state.last_processed_timestamp = 500
            manager.save()

            # Now add a fill with timestamp 1000
            manager.add_processed_fill("hash1", 1000)

            # Verify in memory
            assert manager.is_fill_processed("hash1") is True
            assert manager.state.last_processed_timestamp == 1000

            # Verify saved to disk
            assert file_path.exists()

            # Load new manager and verify persistence
            manager2 = StateManager(file_path)
            assert manager2.is_fill_processed("hash1") is True
            assert manager2.state.last_processed_timestamp == 1000

    def test_is_fill_processed(self):
        """Test checking if fill is processed."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_state_is_processed.json"

            manager = StateManager(file_path)
            manager.add_processed_fill("hash1", 1000)

            assert manager.is_fill_processed("hash1") is True
            assert manager.is_fill_processed("hash2") is False

    def test_record_websocket_heartbeat_no_save(self):
        """Test that heartbeat recording doesn't save (performance)."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_state.json"

            manager = StateManager(file_path)

            # Delete file if it exists
            if file_path.exists():
                file_path.unlink()

            # Record heartbeat
            manager.record_websocket_heartbeat()

            # File should not be created (no save)
            assert not file_path.exists()

    def test_record_websocket_reconnect_saves(self):
        """Test that reconnect recording saves state."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_state.json"

            manager = StateManager(file_path)

            # Delete file
            if file_path.exists():
                file_path.unlink()

            # Record reconnect
            manager.record_websocket_reconnect()

            # File should be created (auto-save)
            assert file_path.exists()

    def test_record_recovery_saves(self):
        """Test that recovery recording saves state."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_state.json"

            manager = StateManager(file_path)

            # Delete file
            if file_path.exists():
                file_path.unlink()

            # Record recovery
            manager.record_recovery(5)

            # File should be created (auto-save)
            assert file_path.exists()

    def test_get_last_processed_timestamp(self):
        """Test getting last processed timestamp."""
        with TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_state_timestamp.json"

            manager = StateManager(file_path)

            # Set baseline timestamp first
            manager.state.last_processed_timestamp = 500
            manager.save()

            # Add fill with specific timestamp
            manager.add_processed_fill("hash1", 12345)

            assert manager.get_last_processed_timestamp() == 12345
