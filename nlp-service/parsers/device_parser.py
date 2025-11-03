"""Device operation patterns for fallback parser.

Handles track and return device controls:
- Named devices (reverb, delay, compressor, eq, etc.) with optional ordinals
- Label selections (Mode, Algorithm, Type, etc.)
- Arbitrary device names as fallback
- Generic device ordinal references (device 1, device 2, etc.)
"""

from __future__ import annotations

import re
from typing import Any, Dict

from config.llm_config import get_default_model_name


def _safe_model_name(model_preference: str | None) -> str:
    """Safely get model name without throwing exceptions."""
    try:
        return get_default_model_name(model_preference)
    except Exception:
        return model_preference or "regex"


# Common patterns
UNITS_PAT = r"db|dB|%|percent|ms|millisecond|milliseconds|s|sec|second|seconds|hz|khz|degree|degrees|deg|°"

# Device pattern is built dynamically from config
_DEV_PAT_CACHE = None

# Session snapshot cache (device names + types from current Live session)
_SESSION_SNAPSHOT_CACHE: Dict[str, Any] = {
    "timestamp": 0.0,
    "devices": {
        "tracks": {},  # track_index -> [{index, name, device_type}, ...]
        "returns": {},  # return_index -> [{index, name, device_type}, ...]
        "master": [],  # [{index, name, device_type}, ...]
    },
    "ordinal_map": {
        "tracks": {},  # track_index -> {device_type: [device_index1, device_index2, ...]}
        "returns": {},  # return_index -> {device_type: [device_index1, device_index2, ...]}
        "master": {},  # device_type -> [device_index1, device_index2, ...]
    },
}
_SESSION_SNAPSHOT_TTL = 60  # Cache for 60 seconds


def _fetch_session_snapshot() -> Dict[str, Any] | None:
    """Fetch session snapshot from server with device names and types.

    Returns:
        Snapshot data with tracks/returns/master device lists or None on failure
    """
    try:
        import os
        import requests

        server_host = os.getenv("SERVER_HOST", "127.0.0.1")
        server_port = os.getenv("SERVER_PORT", "8722")
        url = f"http://{server_host}:{server_port}/snapshot"

        response = requests.get(url, timeout=2.0)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"[DEVICE PARSER] Failed to fetch snapshot: {e}")
        return None


def _refresh_session_snapshot_cache() -> None:
    """Refresh session snapshot cache with current Live session devices.

    Fetches snapshot and builds:
    - Device lists for each track/return/master
    - Ordinal maps for device_type references (e.g., "reverb 1", "reverb 2")
    """
    global _SESSION_SNAPSHOT_CACHE

    snapshot = _fetch_session_snapshot()
    if not snapshot:
        return

    # Build devices map
    devices_map: Dict[str, Any] = {
        "tracks": {},
        "returns": {},
        "master": [],
    }

    # Process tracks
    for track in snapshot.get("tracks", []):
        track_idx = int(track.get("index", 0))
        devices_map["tracks"][track_idx] = track.get("devices", [])

    # Process returns
    for ret in snapshot.get("returns", []):
        ret_idx = int(ret.get("index", 0))
        devices_map["returns"][ret_idx] = ret.get("devices", [])

    # Process master
    master = snapshot.get("master", {})
    devices_map["master"] = master.get("devices", [])

    # Build ordinal maps (device_type -> list of device indices)
    ordinal_map: Dict[str, Any] = {
        "tracks": {},
        "returns": {},
        "master": {},
    }

    # Track ordinals
    for track_idx, devices in devices_map["tracks"].items():
        type_map: Dict[str, list] = {}
        for dev in devices:
            dev_type = dev.get("device_type")
            if dev_type:
                type_map.setdefault(dev_type, []).append(dev.get("index", 0))
        ordinal_map["tracks"][track_idx] = type_map

    # Return ordinals
    for ret_idx, devices in devices_map["returns"].items():
        type_map: Dict[str, list] = {}
        for dev in devices:
            dev_type = dev.get("device_type")
            if dev_type:
                type_map.setdefault(dev_type, []).append(dev.get("index", 0))
        ordinal_map["returns"][ret_idx] = type_map

    # Master ordinals
    type_map: Dict[str, list] = {}
    for dev in devices_map["master"]:
        dev_type = dev.get("device_type")
        if dev_type:
            type_map.setdefault(dev_type, []).append(dev.get("index", 0))
    ordinal_map["master"] = type_map

    # Update global cache
    _SESSION_SNAPSHOT_CACHE = {
        "timestamp": __import__("time").time(),
        "devices": devices_map,
        "ordinal_map": ordinal_map,
    }

    print(f"[DEVICE PARSER] Refreshed session snapshot cache: "
          f"{len(devices_map['tracks'])} tracks, "
          f"{len(devices_map['returns'])} returns, "
          f"{len(devices_map['master'])} master devices")


def _get_session_snapshot() -> Dict[str, Any]:
    """Get cached session snapshot, refreshing if stale.

    Returns:
        Session snapshot cache with devices and ordinal_map
    """
    global _SESSION_SNAPSHOT_CACHE

    import time
    cache_age = time.time() - _SESSION_SNAPSHOT_CACHE.get("timestamp", 0)

    # Refresh if cache is stale or empty
    if cache_age > _SESSION_SNAPSHOT_TTL or not _SESSION_SNAPSHOT_CACHE.get("devices", {}).get("tracks"):
        _refresh_session_snapshot_cache()

    return _SESSION_SNAPSHOT_CACHE


def _get_device_pattern() -> str:
    """Get device pattern from config (static device type aliases only).

    Builds regex pattern from device_type_aliases in config (static types: reverb, delay, etc.)

    NOTE: Device name aliases (e.g., "valhalla", "cathedral") are NO LONGER loaded upfront.
    Instead, they are resolved via just-in-time Firestore lookups to support serverless deployment.
    Use arbitrary parsers + JIT validation for specific device names.

    Returns all device aliases as alternation pattern.
    """
    global _DEV_PAT_CACHE
    if _DEV_PAT_CACHE is not None:
        return _DEV_PAT_CACHE

    try:
        from server.config.app_config import get_device_type_aliases

        aliases_map = get_device_type_aliases()
        all_aliases = []

        # Add device type aliases (reverb, delay, eq, etc.)
        for device_type, aliases in aliases_map.items():
            all_aliases.extend(aliases)

        # Special case for "align delay" (multi-word)
        all_aliases.append(r"align\s+delay")

        # Build pattern (sort by length desc to match longer patterns first)
        all_aliases.sort(key=len, reverse=True)
        _DEV_PAT_CACHE = "|".join(all_aliases)

        print(f"[DEVICE PARSER] Loaded {len(all_aliases)} static device type aliases (no Firestore)")
        return _DEV_PAT_CACHE

    except Exception:
        # Fallback if config unavailable
        return r"reverb|delay|amp"


def _normalize_device_name(device_raw: str) -> str | None:
    """Normalize device names (pass through - config will handle resolution)."""
    if not device_raw:
        return None

    dr = device_raw.lower().strip()

    # Special handling for multi-word devices
    if dr.replace(" ", "") == "aligndelay":
        return "align delay"

    # Return as-is - server's intent normalizer will resolve aliases
    return dr


def _normalize_unit(unit_raw: str | None) -> str | None:
    """Normalize unit strings."""
    if not unit_raw:
        return None
    u = unit_raw.lower()
    if u in ('db',):
        return 'dB'
    elif u in ('%', 'percent'):
        return '%'
    elif u in ('ms', 'millisecond', 'milliseconds'):
        return 'ms'
    elif u in ('s', 'sec', 'second', 'seconds'):
        return 's'
    elif u in ('hz',):
        return 'hz'
    elif u in ('khz',):
        return 'khz'
    elif u in ('degree', 'degrees', 'deg', '°'):
        return 'degrees'
    return None


def _normalize_param_name(pname: str) -> str:
    """Normalize common parameter names."""
    pname_norm_map = {
        'stereo image': 'Stereo Image',
        'decay': 'Decay',
        'predelay': 'Predelay',
        'dry / wet': 'Dry/Wet',
        'dry wet': 'Dry/Wet',
    }
    pn = ' '.join(pname.split()).lower()
    pn = pn.replace('dry / wet', 'dry / wet').replace('dry wet', 'dry / wet')
    return pname_norm_map.get(pn, pname)


def _normalize_label_param(pname: str) -> str:
    """Normalize label parameter names (Mode, Algorithm, etc.)."""
    pname_map = {
        'mode': 'Mode',
        'algorithm': 'Algorithm',
        'alg': 'Algorithm',
        'type': 'Type',
        'quality': 'Quality',
        'distunit': 'DistUnit',
        'units': 'Units'
    }
    return pname_map.get(pname.lower(), pname.title())


def parse_track_device_param(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set track 1 reverb decay to 2 s

    IMPORTANT: Device name is REQUIRED (not optional) to distinguish from mixer operations.
    Mixer ops have 1 token (e.g., "volume"), device ops have 2+ tokens (e.g., "reverb decay").
    """
    try:
        # Device name is now REQUIRED (removed trailing ?)
        dev_pat = _get_device_pattern()
        m = re.search(rf"\bset\s+track\s+(\d+)\s+(?:the\s+)?({dev_pat})(?:\s+(\d+))?\s+(?!device\s+\d+\b)(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)
        if m:
            track_num = int(m.group(1))
            device_raw = m.group(2)  # No longer optional
            device_ord = m.group(3)
            pname = m.group(4).strip()
            value = float(m.group(5))
            unit_raw = m.group(6)

            # Device name must be present (no fallback to 'reverb')
            if not device_raw:
                return None

            dev_norm = _normalize_device_name(device_raw)
            unit_out = _normalize_unit(unit_raw)

            out = {
                'intent': 'set_parameter',
                'targets': [{'track': f'Track {track_num}', 'plugin': dev_norm, 'parameter': pname}],
                'operation': {'type': 'absolute', 'value': value, 'unit': unit_out},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }
            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass
            return out
    except Exception:
        pass
    return None


def parse_return_device_param(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set return A reverb decay to 2 s

    IMPORTANT: Device name is REQUIRED (not optional) to distinguish from mixer operations.
    Mixer ops have 1 token (e.g., "volume"), device ops have 2+ tokens (e.g., "reverb decay").
    """
    try:
        # Device name is now REQUIRED (removed trailing ?)
        dev_pat = _get_device_pattern()
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:the\s+)?({dev_pat})(?:\s+(\d+))?\s+(?!device\s+\d+\b)(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_raw = m.group(2)  # No longer optional
            device_ord = m.group(3)
            pname = m.group(4).strip()
            value = float(m.group(5))
            unit_raw = m.group(6)

            # Device name must be present (no fallback to 'reverb')
            if not device_raw:
                return None

            dev_norm = _normalize_device_name(device_raw)
            param_ref = _normalize_param_name(pname)
            unit_out = _normalize_unit(unit_raw)

            out = {
                'intent': 'set_parameter',
                'targets': [{'track': f'Return {return_ref}', 'plugin': dev_norm, 'parameter': param_ref}],
                'operation': {'type': 'absolute', 'value': value, 'unit': unit_out},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }
            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass
            return out
    except Exception:
        pass
    return None


def parse_return_device_label(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set return A align delay mode to Distance"""
    try:
        dev_pat = _get_device_pattern()
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:(?:the\s+)?({dev_pat})(?:\s+(\d+))?\s+)?(mode|quality|type|algorithm|alg|distunit|units?)\s+(?:to|at|=)\s*([a-zA-Z]+)\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_raw = m.group(2) or ''
            device_ord = m.group(3)
            pname = m.group(4).strip()
            label = m.group(5).strip()

            plugin = _normalize_device_name(device_raw) or 'reverb'
            param_ref = _normalize_label_param(pname)

            out = {
                'intent': 'set_parameter',
                'targets': [{'track': f'Return {return_ref}', 'plugin': plugin, 'parameter': param_ref}],
                'operation': {'type': 'absolute', 'value': label, 'unit': 'display'},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }
            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass
            return out
    except Exception:
        pass
    return None


def parse_return_device_label_arbitrary(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set return A valhalla mode to Hall (with optional JIT device resolution)"""
    try:
        m = re.search(r"\bset\s+return\s+([a-d])\s+(?:the\s+)?(.+?)\s+(mode|quality|type|algorithm|alg|distunit|units?)\s+(?:to|at|=)\s*([a-zA-Z]+)\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_name = m.group(2).strip()
            pname = m.group(3).strip()
            label = m.group(4).strip()

            # JIT resolution: check if device exists in Firestore (optional)
            try:
                import sys
                import os
                nlp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                if nlp_path not in sys.path:
                    sys.path.insert(0, nlp_path)

                from learning.preset_cache_store import lookup_device_by_name
                device_info = lookup_device_by_name(device_name)

                if device_info:
                    # Use canonical device name from Firestore
                    device_name = device_info['canonical_name']
                # If not found, use device_name as-is (fallback to arbitrary name)
            except Exception:
                # JIT lookup failed - use device_name as-is
                pass

            param_ref = _normalize_label_param(pname)

            return {
                'intent': 'set_parameter',
                'targets': [{'track': f'Return {return_ref}', 'plugin': device_name, 'parameter': param_ref}],
                'operation': {'type': 'absolute', 'value': label, 'unit': 'display'},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_return_device_numeric_arbitrary(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set return A valhalla feedback to 20 % (with optional JIT device resolution)

    Uses smart splitting: tries to match known parameters first, then splits device/param.
    """
    try:
        # Common parameter patterns (greedy match at end to handle multi-word params)
        PARAM_PATTERNS = r"(?:dry\s*/?\s*wet|feedback|decay|size|predelay|mix|time|rate|depth|resonance|gain|level|volume|pan|width|stereo\s+image)"

        # Try pattern with known parameter names first
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:the\s+)?(.+?)\s+({PARAM_PATTERNS})\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q, re.IGNORECASE)

        if not m:
            # Fallback to generic pattern (device + param)
            m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:the\s+)?(.+?)\s+(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)

        if m:
            return_ref = m.group(1).upper()
            device_name = m.group(2).strip()
            pname = m.group(3).strip()
            value = float(m.group(4))
            unit_raw = m.group(5)

            # JIT resolution: check if device exists in Firestore (optional)
            try:
                import sys
                import os
                nlp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                if nlp_path not in sys.path:
                    sys.path.insert(0, nlp_path)

                from learning.preset_cache_store import lookup_device_by_name
                device_info = lookup_device_by_name(device_name)

                if device_info:
                    # Use canonical device name from Firestore
                    device_name = device_info['canonical_name']
                # If not found, use device_name as-is (fallback to arbitrary name)
            except Exception:
                # JIT lookup failed - use device_name as-is
                pass

            unit_out = _normalize_unit(unit_raw)

            return {
                'intent': 'set_parameter',
                'targets': [{'track': f'Return {return_ref}', 'plugin': device_name, 'parameter': pname}],
                'operation': {'type': 'absolute', 'value': value, 'unit': unit_out},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_track_device_numeric_arbitrary(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set track 2 valhalla feedback to 20 % (with optional JIT device resolution)

    Uses smart splitting: tries to match known parameters first, then splits device/param.
    """
    try:
        # Common parameter patterns (greedy match at end to handle multi-word params)
        PARAM_PATTERNS = r"(?:dry\s*/?\s*wet|feedback|decay|size|predelay|mix|time|rate|depth|resonance|gain|level|volume|pan|width|stereo\s+image)"

        # Try pattern with known parameter names first
        m = re.search(rf"\bset\s+track\s+(\d+)\s+(?:the\s+)?(.+?)\s+({PARAM_PATTERNS})\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q, re.IGNORECASE)

        if not m:
            # Fallback to generic pattern (device + param)
            m = re.search(rf"\bset\s+track\s+(\d+)\s+(?:the\s+)?(.+?)\s+(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)

        if m:
            track_num = int(m.group(1))
            device_name = m.group(2).strip()
            pname = m.group(3).strip()
            value = float(m.group(4))
            unit_raw = m.group(5)

            # JIT resolution: check if device exists in Firestore (optional)
            try:
                import sys
                import os
                nlp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                if nlp_path not in sys.path:
                    sys.path.insert(0, nlp_path)

                from learning.preset_cache_store import lookup_device_by_name
                device_info = lookup_device_by_name(device_name)

                if device_info:
                    # Use canonical device name from Firestore
                    device_name = device_info['canonical_name']
                # If not found, use device_name as-is (fallback to arbitrary name)
            except Exception:
                # JIT lookup failed - use device_name as-is
                pass

            unit_out = _normalize_unit(unit_raw)

            return {
                'intent': 'set_parameter',
                'targets': [{'track': f'Track {track_num}', 'plugin': device_name, 'parameter': pname}],
                'operation': {'type': 'absolute', 'value': value, 'unit': unit_out},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_track_device_label(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set track 1 reverb mode to Distance"""
    try:
        dev_pat = _get_device_pattern()
        m = re.search(rf"\bset\s+track\s+(\d+)\s+(?:(?:the\s+)?({dev_pat})(?:\s+(\d+))?\s+)?(mode|quality|type|algorithm|alg|distunit|units?)\s+(?:to|at|=)\s*([a-zA-Z]+)\b", q)
        if m:
            track_num = int(m.group(1))
            device_raw = m.group(2) or ''
            device_ord = m.group(3)
            pname = m.group(4).strip()
            label = m.group(5).strip()

            plugin = _normalize_device_name(device_raw) or 'reverb'
            param_ref = _normalize_label_param(pname)

            out = {
                'intent': 'set_parameter',
                'targets': [{'track': f'Track {track_num}', 'plugin': plugin, 'parameter': param_ref}],
                'operation': {'type': 'absolute', 'value': label, 'unit': 'display'},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }
            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass
            return out
    except Exception:
        pass
    return None


def parse_return_device_ordinal(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set return A device 2 feedback to 20 %"""
    try:
        m = re.search(rf"\bset\s+return\s+([a-d])\s+device\s+(\d+)\s+(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_ord = m.group(2)
            pname = m.group(3).strip()
            value = float(m.group(4))
            unit_raw = m.group(5)

            unit_out = _normalize_unit(unit_raw)

            return {
                'intent': 'set_parameter',
                'targets': [{'track': f'Return {return_ref}', 'plugin': 'device', 'parameter': pname, 'device_ordinal': int(device_ord)}],
                'operation': {'type': 'absolute', 'value': value, 'unit': unit_out},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_track_device_ordinal(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set track 1 device 2 feedback to 20 %"""
    try:
        m = re.search(rf"\bset\s+track\s+(\d+)\s+device\s+(\d+)\s+(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)
        if m:
            track_num = int(m.group(1))
            device_ord = m.group(2)
            pname = m.group(3).strip()
            value = float(m.group(4))
            unit_raw = m.group(5)

            unit_out = _normalize_unit(unit_raw)

            return {
                'intent': 'set_parameter',
                'targets': [{'track': f'Track {track_num}', 'plugin': 'device', 'parameter': pname, 'device_ordinal': int(device_ord)}],
                'operation': {'type': 'absolute', 'value': value, 'unit': unit_out},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_return_device_generic(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: generic catch-all for return device parameters"""
    try:
        dev_pat = _get_device_pattern()
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:(?:the\s+)?({dev_pat})(?:\s+(\d+))?\s+)?(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_raw = m.group(2) or ''
            device_ord = m.group(3)
            pname = m.group(4).strip()
            value = float(m.group(5))
            unit_raw = m.group(6)

            dev_norm = _normalize_device_name(device_raw)
            unit_out = _normalize_unit(unit_raw)

            out = {
                'intent': 'set_parameter',
                'targets': [{'track': f'Return {return_ref}', 'plugin': (dev_norm or 'reverb'), 'parameter': pname}],
                'operation': {'type': 'absolute', 'value': value, 'unit': unit_out},
                'meta': {'utterance': query, 'fallback': True, 'error': error_msg, 'model_selected': _safe_model_name(model_preference)}
            }
            if device_ord:
                try:
                    out['targets'][0]['device_ordinal'] = int(device_ord)
                except Exception:
                    pass
            return out
    except Exception:
        pass
    return None


# Main device parser coordinator
DEVICE_PARSERS = [
    parse_track_device_param,           # "set track 1 reverb decay to 2 s" (device in DEV_PAT)
    parse_return_device_param,          # "set return A reverb decay to 2 s" (device in DEV_PAT)
    parse_return_device_label,          # "set return A reverb mode to hall" (label selection)
    parse_track_device_label,           # "set track 1 eq type to parametric" (label selection)
    parse_return_device_ordinal,        # "set return A device 2 decay to 1 s" (ordinal reference)
    parse_track_device_ordinal,         # "set track 1 device 3 gain to 5" (ordinal reference)
    # Arbitrary parsers with optional JIT resolution (resolve learned devices, allow unknowns)
    parse_return_device_label_arbitrary,    # "set return A valhalla mode to hall" (JIT: valhalla->canonical)
    parse_return_device_numeric_arbitrary,  # "set return A valhalla decay to 2s" OR "4th bandpass feedback to 20%"
    parse_track_device_numeric_arbitrary,   # "set track 1 valhalla decay to 2s" (learned devices get canonical names)
]


def parse_device_command(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Try all device parsers in order.

    Args:
        q: Lowercase, typo-corrected query
        query: Original user query
        error_msg: LLM error message
        model_preference: Model preference string

    Returns:
        Parsed intent dict or None if no match
    """
    for parser in DEVICE_PARSERS:
        try:
            result = parser(q, query, error_msg, model_preference)
            if result:
                return result
        except Exception:
            continue
    return None
