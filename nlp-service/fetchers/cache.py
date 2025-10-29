"""Simple TTL cache for device and mixer parameter data."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class TTLCache:
    """Time-To-Live cache for fetched data."""

    def __init__(self):
        self._device_cache: Dict[str, Any] = {
            "data": None,
            "expires": None
        }
        self._mixer_cache: Dict[str, Any] = {
            "data": None,
            "expires": None
        }

    def get_devices(self, ttl_seconds: int) -> Optional[List[Dict[str, str]]]:
        """Get cached devices if not expired.

        Args:
            ttl_seconds: Time-to-live in seconds

        Returns:
            Cached device list or None if expired
        """
        now = datetime.now()
        if (self._device_cache["expires"] and
                now < self._device_cache["expires"]):
            return self._device_cache["data"]
        return None

    def set_devices(self, devices: List[Dict[str, str]], ttl_seconds: int):
        """Cache devices with TTL.

        Args:
            devices: Device list to cache
            ttl_seconds: Time-to-live in seconds
        """
        self._device_cache["data"] = devices
        self._device_cache["expires"] = datetime.now() + timedelta(seconds=ttl_seconds)

    def get_mixer_params(self, ttl_seconds: int) -> Optional[List[str]]:
        """Get cached mixer params if not expired.

        Args:
            ttl_seconds: Time-to-live in seconds

        Returns:
            Cached mixer param list or None if expired
        """
        now = datetime.now()
        if (self._mixer_cache["expires"] and
                now < self._mixer_cache["expires"]):
            return self._mixer_cache["data"]
        return None

    def set_mixer_params(self, params: List[str], ttl_seconds: int):
        """Cache mixer params with TTL.

        Args:
            params: Mixer param list to cache
            ttl_seconds: Time-to-live in seconds
        """
        self._mixer_cache["data"] = params
        self._mixer_cache["expires"] = datetime.now() + timedelta(seconds=ttl_seconds)

    def invalidate_devices(self):
        """Invalidate device cache immediately."""
        self._device_cache["expires"] = None
        self._device_cache["data"] = None

    def invalidate_mixer_params(self):
        """Invalidate mixer param cache immediately."""
        self._mixer_cache["expires"] = None
        self._mixer_cache["data"] = None

    def invalidate_all(self):
        """Invalidate all caches immediately."""
        self.invalidate_devices()
        self.invalidate_mixer_params()


# Global cache instance
_cache = TTLCache()


def get_cached_devices(ttl_seconds: int = 5) -> Optional[List[Dict[str, str]]]:
    """Get cached devices.

    Args:
        ttl_seconds: Cache time-to-live (default 5 seconds)

    Returns:
        Cached device list or None if expired
    """
    return _cache.get_devices(ttl_seconds)


def set_cached_devices(devices: List[Dict[str, str]], ttl_seconds: int = 5):
    """Set cached devices.

    Args:
        devices: Device list to cache
        ttl_seconds: Cache time-to-live (default 5 seconds)
    """
    _cache.set_devices(devices, ttl_seconds)


def get_cached_mixer_params(ttl_seconds: int = 5) -> Optional[List[str]]:
    """Get cached mixer params.

    Args:
        ttl_seconds: Cache time-to-live (default 5 seconds)

    Returns:
        Cached mixer param list or None if expired
    """
    return _cache.get_mixer_params(ttl_seconds)


def set_cached_mixer_params(params: List[str], ttl_seconds: int = 5):
    """Set cached mixer params.

    Args:
        params: Mixer param list to cache
        ttl_seconds: Cache time-to-live (default 5 seconds)
    """
    _cache.set_mixer_params(params, ttl_seconds)


def invalidate_cache():
    """Invalidate all caches."""
    _cache.invalidate_all()
