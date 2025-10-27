"""Mixer operation patterns for fallback parser.

Handles track and return mixer controls:
- Volume (absolute & relative)
- Pan
- Solo/Mute toggles
- Sends
"""

from __future__ import annotations

import re
from typing import Any, Dict

from config.llm_config import get_default_model_name


def parse_track_volume_absolute(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set track 1 volume to -6 dB"""
    try:
        # Generalized pattern with optional unit (db|%); if absent, leave unit None (treated as normalized)
        abs_match = re.search(r"(?:set|make|adjust|change)\s+(?:the\s+)?(?:volume\s+of\s+)?track\s+(\d+)\s+(?:volume\s+)?(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if not abs_match:
            # Variant: "track 1 volume to -6 dB" (missing leading verb)
            abs_match = re.search(r"track\s+(\d+)\s+volume\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if abs_match:
            track_num = int(abs_match.group(1))
            value = float(abs_match.group(2))
            unit = abs_match.group(3)
            unit_out = None
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",):
                    unit_out = "dB"
                elif unit_l in ("%", "percent"):
                    unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_track_volume_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: increase track 2 volume by 3 dB"""
    if "volume" in q and any(word in q for word in ["increase", "decrease", "up", "down", "louder", "quieter"]):
        # Try to extract track number
        track_match = re.search(r"track\s+(\d+)", q)
        if track_match:
            track_num = int(track_match.group(1))
            # Determine direction and amount
            value = 3  # default 3dB
            if "decrease" in q or "down" in q or "quieter" in q:
                value = -3

            return {
                "intent": "relative_change",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "relative", "value": value, "unit": "dB"},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    return None


def parse_track_pan(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: pan track 1 left 30%"""
    try:
        m = re.search(r"\b(\d{1,2}|50)\s*([lr])\b", q)
        if m:
            amt = int(m.group(1))
            side = m.group(2)
            # map 25L => -25, 25R => +25
            pan_val = -amt if side == 'l' else amt
            trk = re.search(r"track\s+(\d+)", q)
            track_num = int(trk.group(1)) if trk else 1
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "pan"}],
                "operation": {"type": "absolute", "value": pan_val, "unit": "%"},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_track_solo_mute(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: solo track 1, mute track 2"""
    try:
        m = re.search(r"\b(solo|unsolo|mute|unmute)\s+track\s+(\d+)\b", q)
        if m:
            action = m.group(1).lower()
            track_num = int(m.group(2))
            param = 'solo' if 'solo' in action else 'mute'
            value = 0.0 if action in ('unsolo', 'unmute') else 1.0
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": param}],
                "operation": {"type": "absolute", "value": value, "unit": None},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_track_sends(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set track 1 send A to -12 dB"""
    try:
        m = re.search(r"\bset\s+track\s+(\d+)\s+(?:send\s+)?([a-d])\b.*?\bto\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if m:
            track_num = int(m.group(1))
            send_ref = m.group(2).upper()
            value = float(m.group(3))
            unit = m.group(4)
            unit_out = None
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass

    # Variant without 'to'
    try:
        m = re.search(r"\bset\s+track\s+(\d+)\s+(?:send\s+)?([a-d])\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if not m:
            # Variant: set send A on track 1 to -12 dB
            m = re.search(r"\bset\s+send\s+([a-d])\s+on\s+track\s+(\d+)\s*(?:to|at)?\s*(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
            if m:
                # Rearrange capture groups to unify handling
                track_num = int(m.group(2))
                send_ref = m.group(1).upper()
                value = float(m.group(3))
                unit = m.group(4)
            else:
                track_num = None
        if m and track_num is None:
            track_num = int(m.group(1))
            send_ref = m.group(2).upper()
            value = float(m.group(3))
            unit = m.group(4)
        if m:
            unit_out = None
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass

    return None


def parse_return_sends(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set return A send B to -10 dB"""
    try:
        m = re.search(r"\bset\s+return\s+([a-d])\s+(?:send\s+)?([a-d])\b.*?\bto\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            send_ref = m.group(2).upper()
            value = float(m.group(3))
            unit = m.group(4)
            unit_out = None
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass

    # Variant without 'to'
    try:
        m = re.search(r"\bset\s+return\s+([a-d])\s+(?:send\s+)?([a-d])\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if not m:
            # Variant: set send B on return A to -10 dB
            m = re.search(r"\bset\s+send\s+([a-d])\s+on\s+return\s+([a-d])\s*(?:to|at)?\s*(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
            if m:
                return_ref = m.group(2).upper()
                send_ref = m.group(1).upper()
                value = float(m.group(3))
                unit = m.group(4)
            else:
                return_ref = None
        if m and return_ref is None:
            return_ref = m.group(1).upper()
            send_ref = m.group(2).upper()
            value = float(m.group(3))
            unit = m.group(4)
        if m:
            unit_out = None
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass

    return None


def parse_return_volume(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set return A volume to -3 dB"""
    try:
        m = re.search(r"\bset\s+return\s+([a-d])\s+volume\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            value = float(m.group(2))
            unit = m.group(3)
            unit_out = None
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": get_default_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


# Main mixer parser coordinator
MIXER_PARSERS = [
    parse_track_volume_absolute,
    parse_track_volume_relative,
    parse_track_pan,
    parse_track_solo_mute,
    parse_track_sends,
    parse_return_sends,
    parse_return_volume,
]


def parse_mixer_command(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Try all mixer parsers in order.

    Args:
        q: Lowercase, typo-corrected query
        query: Original user query
        error_msg: LLM error message
        model_preference: Model preference string

    Returns:
        Parsed intent dict or None if no match
    """
    for parser in MIXER_PARSERS:
        try:
            result = parser(q, query, error_msg, model_preference)
            if result:
                return result
        except Exception:
            continue
    return None
