"""Fetch device information from current Live session."""

from __future__ import annotations

from typing import Dict, List


def fetch_session_devices() -> List[Dict[str, str]] | None:
    """Fetch all devices from current Live session snapshot.

    Returns:
        List of device dictionaries with 'name' and 'type' keys, or None if unavailable.
    """
    try:
        import requests

        resp = requests.get("http://127.0.0.1:8722/snapshot", timeout=2.0)
        if not resp.ok:
            return None

        snapshot = resp.json()
        if not snapshot or not snapshot.get("ok"):
            return None

        devices = []
        seen = set()

        # Extract from data.devices structure (more detailed)
        data = snapshot.get("data", {})
        device_data = data.get("devices", {})

        # Process track devices
        for track_idx, track_info in device_data.get("tracks", {}).items():
            for dev in track_info.get("devices", []):
                name = dev.get("name", "").strip()
                if name and name not in seen:
                    devices.append({"name": name, "type": "unknown"})
                    seen.add(name)

        # Process return devices
        for return_idx, return_info in device_data.get("returns", {}).items():
            for dev in return_info.get("devices", []):
                name = dev.get("name", "").strip()
                if name and name not in seen:
                    devices.append({"name": name, "type": "unknown"})
                    seen.add(name)

        return devices if devices else None
    except Exception:
        return None
