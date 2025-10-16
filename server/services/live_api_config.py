"""
Ableton Live API Configuration

This module provides configuration for translating between our internal 0-based
indexing and Ableton Live's actual API indexing scheme.

All fadebender code uses 0-based indexing internally. This config handles the
translation to Live's mixed indexing scheme.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from server.core.deps import get_store


# Default configuration (used if Firestore is unavailable)
DEFAULT_CONFIG = {
    "version": "1.0",
    "description": "Ableton Live API indexing configuration",
    "indexing": {
        "tracks": {
            "internal_base": 0,
            "live_base": 1,
            "description": "Tracks: internal 0-based → Live 1-based (Track 1 = internal 0, Live 1)"
        },
        "returns": {
            "internal_base": 0,
            "live_base": 0,
            "description": "Returns: both 0-based (Return A = internal 0, Live 0)"
        },
        "sends": {
            "internal_base": 0,
            "live_base": 0,
            "description": "Sends: both 0-based (Send A = internal 0, Live 0)"
        },
        "devices": {
            "internal_base": 0,
            "live_base": 0,
            "description": "Devices: both 0-based (Device 1 = internal 0, Live 0)"
        }
    },
    "notes": [
        "Ableton Live uses inconsistent indexing:",
        "- Tracks are 1-based (historical quirk)",
        "- Returns, Sends, Devices are 0-based (standard)",
        "Fadebender uses 0-based everywhere internally for consistency"
    ]
}


class LiveAPIConfig:
    """Configuration for Ableton Live API indexing."""

    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None
        self._load_config()

    def _load_config(self):
        """Load config from Firestore or use defaults."""
        try:
            store = get_store()
            if store.enabled and store._client:
                doc = store._client.collection("api_config").document("live_api").get()
                if doc.exists:
                    self._config = doc.to_dict()
                    return
        except Exception:
            pass

        # Fallback to defaults
        self._config = DEFAULT_CONFIG

    def to_live_index(self, entity_type: str, internal_index: int) -> int:
        """Convert internal 0-based index to Live API index.

        Args:
            entity_type: One of "tracks", "returns", "sends", "devices"
            internal_index: Internal 0-based index

        Returns:
            Index for Live API

        Examples:
            >>> config.to_live_index("tracks", 0)  # Track 1
            1
            >>> config.to_live_index("returns", 0)  # Return A
            0
        """
        if not self._config:
            self._load_config()

        indexing = self._config.get("indexing", {}).get(entity_type, {})
        internal_base = indexing.get("internal_base", 0)
        live_base = indexing.get("live_base", 0)

        # Translate: remove internal offset, add Live offset
        return internal_index - internal_base + live_base

    def from_live_index(self, entity_type: str, live_index: int) -> int:
        """Convert Live API index to internal 0-based index.

        Args:
            entity_type: One of "tracks", "returns", "sends", "devices"
            live_index: Index from Live API

        Returns:
            Internal 0-based index

        Examples:
            >>> config.from_live_index("tracks", 1)  # Track 1 → internal 0
            0
            >>> config.from_live_index("returns", 0)  # Return A → internal 0
            0
        """
        if not self._config:
            self._load_config()

        indexing = self._config.get("indexing", {}).get(entity_type, {})
        internal_base = indexing.get("internal_base", 0)
        live_base = indexing.get("live_base", 0)

        # Translate: remove Live offset, add internal offset
        return live_index - live_base + internal_base

    def get_min_valid_index(self, entity_type: str) -> int:
        """Get minimum valid index for entity type (in internal 0-based).

        Args:
            entity_type: One of "tracks", "returns", "sends", "devices"

        Returns:
            Minimum valid internal index (always 0 for internal indexing)
        """
        return 0  # All internal indices start at 0

    def get_min_live_index(self, entity_type: str) -> int:
        """Get minimum valid Live API index for entity type.

        Args:
            entity_type: One of "tracks", "returns", "sends", "devices"

        Returns:
            Minimum valid Live API index
        """
        if not self._config:
            self._load_config()

        indexing = self._config.get("indexing", {}).get(entity_type, {})
        return indexing.get("live_base", 0)


# Global instance
_config_instance: Optional[LiveAPIConfig] = None


def get_live_api_config() -> LiveAPIConfig:
    """Get the global Live API configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = LiveAPIConfig()
    return _config_instance
