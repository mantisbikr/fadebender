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
DEV_PAT = r"reverb|align\s+delay|delay|compressor|eq|equalizer"
UNITS_PAT = r"db|dB|%|percent|ms|millisecond|milliseconds|s|sec|second|seconds|hz|khz|degree|degrees|deg|°"


def _normalize_device_name(device_raw: str) -> str | None:
    """Normalize common device names."""
    if not device_raw:
        return None
    dr = device_raw.lower().strip()
    if dr in ("eq", "equalizer"):
        return "eq"
    elif dr == "compressor":
        return "compressor"
    elif dr == "delay":
        return "delay"
    elif dr.replace(" ", "") == "aligndelay":
        return "align delay"
    else:
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
        m = re.search(rf"\bset\s+track\s+(\d+)\s+(?:the\s+)?({DEV_PAT})(?:\s+(\d+))?\s+(?!device\s+\d+\b)(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)
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
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:the\s+)?({DEV_PAT})(?:\s+(\d+))?\s+(?!device\s+\d+\b)(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)
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
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:(?:the\s+)?({DEV_PAT})(?:\s+(\d+))?\s+)?(mode|quality|type|algorithm|alg|distunit|units?)\s+(?:to|at|=)\s*([a-zA-Z]+)\b", q)
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
    """Parse: set return A screamer mode to Tube (arbitrary device name fallback)"""
    try:
        m = re.search(r"\bset\s+return\s+([a-d])\s+(?:the\s+)?(.+?)\s+(mode|quality|type|algorithm|alg|distunit|units?)\s+(?:to|at|=)\s*([a-zA-Z]+)\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_name = m.group(2).strip()
            pname = m.group(3).strip()
            label = m.group(4).strip()

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
    """Parse: set return A 4th bandpass feedback to 20 %"""
    try:
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:the\s+)?(.+?)\s+(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            device_name = m.group(2).strip()
            pname = m.group(3).strip()
            value = float(m.group(4))
            unit_raw = m.group(5)

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
    """Parse: set track 2 4th bandpass feedback to 20 %"""
    try:
        m = re.search(rf"\bset\s+track\s+(\d+)\s+(?:the\s+)?(.+?)\s+(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)
        if m:
            track_num = int(m.group(1))
            device_name = m.group(2).strip()
            pname = m.group(3).strip()
            value = float(m.group(4))
            unit_raw = m.group(5)

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
        m = re.search(rf"\bset\s+track\s+(\d+)\s+(?:(?:the\s+)?({DEV_PAT})(?:\s+(\d+))?\s+)?(mode|quality|type|algorithm|alg|distunit|units?)\s+(?:to|at|=)\s*([a-zA-Z]+)\b", q)
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
        m = re.search(rf"\bset\s+return\s+([a-d])\s+(?:(?:the\s+)?({DEV_PAT})(?:\s+(\d+))?\s+)?(.+?)\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*({UNITS_PAT}))?\b", q)
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
    # REMOVED: Arbitrary parsers too greedy - match unknown device names & keep typos
    # Let LLM handle these, then learn corrections for typo dictionary
    # parse_return_device_label_arbitrary,
    # parse_return_device_numeric_arbitrary,
    # parse_track_device_numeric_arbitrary,
    # parse_return_device_generic,
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
