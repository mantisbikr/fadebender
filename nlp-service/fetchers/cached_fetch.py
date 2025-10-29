"""Cached fetchers for devices and mixer params."""

from __future__ import annotations

from typing import Dict, List

from config.nlp_config import get_cache_ttl
from .cache import (
    get_cached_devices,
    set_cached_devices,
    get_cached_mixer_params,
    set_cached_mixer_params
)
from .session_fetcher import fetch_session_devices
from .preset_fetcher import fetch_preset_devices, fetch_mixer_params


def fetch_devices_cached() -> List[Dict[str, str]] | None:
    """Fetch devices with caching.

    Priority:
    1. Check cache (5 second TTL by default)
    2. Fetch from session (Ableton Live)
    3. Fallback to Firestore presets

    Returns:
        List of devices or None
    """
    ttl = get_cache_ttl()

    # Try cache first
    cached = get_cached_devices(ttl)
    if cached is not None:
        return cached

    # Fetch from session (most accurate)
    devices = fetch_session_devices()

    # Fallback to Firestore if session unavailable
    if not devices:
        devices = fetch_preset_devices()

    # Cache the result
    if devices:
        set_cached_devices(devices, ttl)

    return devices


def fetch_mixer_params_cached() -> List[str]:
    """Fetch mixer params with caching.

    Priority:
    1. Check cache (5 second TTL by default)
    2. Fetch from Firestore
    3. Fallback to hardcoded defaults

    Returns:
        List of mixer parameter names
    """
    ttl = get_cache_ttl()

    # Try cache first
    cached = get_cached_mixer_params(ttl)
    if cached is not None:
        return cached

    # Fetch from Firestore
    params = fetch_mixer_params()

    # Fallback to defaults
    if not params:
        params = ["volume", "pan", "mute", "solo", "send"]

    # Cache the result
    set_cached_mixer_params(params, ttl)

    return params
