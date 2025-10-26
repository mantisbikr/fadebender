"""Fetch device and parameter information from Firestore presets."""

from __future__ import annotations

import os
import sys
from typing import Dict, List


def fetch_preset_devices() -> List[Dict[str, str]] | None:
    """Fetch devices from Firestore presets as fallback.

    Returns:
        List of device dictionaries with 'name' and 'type' keys, or None if unavailable.
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'server'))
        from services.mapping_store import MappingStore

        store = MappingStore()
        presets = store.list_presets()

        if not presets:
            return None

        known_devices = []
        seen = set()

        for p in presets:
            name = p.get("device_name") or p.get("name")
            dtype = p.get("device_type") or "unknown"
            if name and name not in seen:
                known_devices.append({"name": name, "type": dtype})
                seen.add(name)

        return known_devices if known_devices else None
    except Exception:
        return None


def fetch_mixer_params() -> List[str] | None:
    """Fetch mixer parameter names from Firestore.

    Returns:
        List of mixer parameter names, or None if unavailable.
        Falls back to hardcoded list: ["volume", "pan", "mute", "solo", "send"]
    """
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..', 'server'))
        from services.mapping_store import MappingStore

        store = MappingStore()
        mixer_params = store.get_mixer_param_names()

        return mixer_params if mixer_params else None
    except Exception:
        return None
