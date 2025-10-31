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
from config.nlp_config import get_relative_change_verbs


def _safe_model_name(model_preference: str | None) -> str:
    """Safely get model name without throwing exceptions."""
    try:
        return get_default_model_name(model_preference)
    except Exception:
        return model_preference or "regex"


def parse_track_volume_absolute(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set track 1 volume to -6 dB"""
    try:
        # Generalized pattern with optional unit (db|%); if absent, treat as display value
        abs_match = re.search(r"(?:set|make|adjust|change)\s+(?:the\s+)?(?:volume\s+of\s+)?track\s+(\d+)\s+(?:volume\s+)?(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if not abs_match:
            # Variant: "track 1 volume to -6 dB" (missing leading verb)
            abs_match = re.search(r"track\s+(\d+)\s+volume\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if abs_match:
            track_num = int(abs_match.group(1))
            value = float(abs_match.group(2))
            unit = abs_match.group(3)
            # Default to display value interpretation when no unit specified
            unit_out = "display"
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",):
                    unit_out = "display"
                elif unit_l in ("%", "percent"):
                    unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_track_volume_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: increase track 2 volume by 3 dB, or add 3 dB to track 2 volume"""
    increase_verbs, decrease_verbs = get_relative_change_verbs()
    all_verbs = increase_verbs + decrease_verbs
    if "volume" in q and any(word in q for word in all_verbs):
        # Try to extract track number
        track_match = re.search(r"track\s+(\d+)", q)
        if track_match:
            track_num = int(track_match.group(1))

            # Try to extract "by X" amount with optional unit
            by_match = re.search(r"by\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?", q)

            if by_match:
                value = float(by_match.group(1))
                unit = by_match.group(2)

                # Apply direction using config verbs
                if any(word in q for word in decrease_verbs):
                    value = -abs(value)
                else:
                    value = abs(value)

                # Pass through explicit units, otherwise mark as display for intent_mapper to look up
                if unit:
                    unit_l = unit.lower()
                    if unit_l in ("db",):
                        unit_out = "dB"
                    elif unit_l in ("%", "percent"):
                        unit_out = "%"
                    else:
                        unit_out = "display"
                else:
                    unit_out = "display"
            else:
                # Fallback: use default 3dB if no "by X" found
                value = 3
                if any(word in q for word in decrease_verbs):
                    value = -3
                unit_out = "display"

            return {
                "intent": "relative_change",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "relative", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    return None


def parse_track_pan(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse pan commands: 'set track 1 pan to -25' or 'track 1 pan 25l'"""
    try:
        track_num = 1
        trk = re.search(r"track\s+(\d+)", q)
        if trk:
            track_num = int(trk.group(1))

        # Pattern 1: "set track X pan to VALUE" (like volume)
        # Supports: "to -25", "to 50%", "to 25% left", "to 30% right"
        abs_match = re.search(r"(?:set|make|adjust|change)\s+(?:the\s+)?(?:pan\s+of\s+)?track\s+(\d+)\s+(?:pan\s+)?(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*%)?(?:\s+(left|right))?\b", q)
        if not abs_match:
            # Variant: "track X pan to VALUE" (missing leading verb)
            abs_match = re.search(r"track\s+(\d+)\s+pan\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*%)?(?:\s+(left|right))?\b", q)

        if abs_match:
            track_num = int(abs_match.group(1))
            value = float(abs_match.group(2))
            direction = abs_match.group(3)  # "left" or "right" or None

            # Apply direction if specified
            if direction:
                dir_lower = direction.lower()
                if dir_lower == "left" and value > 0:
                    value = -value
                elif dir_lower == "right" and value < 0:
                    value = -value

            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "pan"}],
                "operation": {"type": "absolute", "value": value, "unit": "%"},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }

        # Pattern 2: Original compact format "25l" or "30r"
        compact_match = re.search(r"\b(\d{1,2}|50)\s*([lr])\b", q)
        if compact_match:
            amt = int(compact_match.group(1))
            side = compact_match.group(2)
            # map 25L => -25, 25R => +25
            pan_val = -amt if side == 'l' else amt
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "pan"}],
                "operation": {"type": "absolute", "value": pan_val, "unit": "%"},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_track_pan_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: pan track 1 20% to the right, or pan track 1 left by 10"""
    increase_verbs, decrease_verbs = get_relative_change_verbs()
    all_verbs = increase_verbs + decrease_verbs

    # Trigger on: explicit verbs OR directional keywords (left/right)
    if "pan" in q and (any(word in q for word in all_verbs) or "left" in q or "right" in q):
        # Try to extract track number
        track_match = re.search(r"track\s+(\d+)", q)
        if track_match:
            track_num = int(track_match.group(1))

            # Try to extract "by X" or "X to the left/right"
            by_match = re.search(r"by\s+(-?\d+(?:\.\d+)?)(?:\s*(%))?", q)

            if by_match:
                value = float(by_match.group(1))
                unit = by_match.group(2)

                # Apply direction using config verbs
                if any(word in q for word in decrease_verbs):
                    value = -abs(value)
                elif "left" in q:
                    value = -abs(value)
                elif "right" in q:
                    value = abs(value)
                else:
                    value = abs(value)

                # Pan always uses %
                unit_out = "%"
            else:
                # Fallback: use default 10% if no "by X" found
                value = 10
                if any(word in q for word in decrease_verbs) or "left" in q:
                    value = -10
                unit_out = "%"

            return {
                "intent": "relative_change",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": "pan"}],
                "operation": {"type": "relative", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
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
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
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
            unit_out = "display"
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
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
            unit_out = "display"
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    except Exception:
        pass

    return None


def parse_track_sends_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: increase track 1 send A by 3 dB, or decrease track 2 send B by 10%"""
    increase_verbs, decrease_verbs = get_relative_change_verbs()
    all_verbs = increase_verbs + decrease_verbs

    # Look for send with increase/decrease verbs
    if "send" in q and any(word in q for word in all_verbs):
        # Match track number and send letter
        track_match = re.search(r"track\s+(\d+)", q)
        send_match = re.search(r"send\s+([a-d])\b", q)

        if track_match and send_match:
            track_num = int(track_match.group(1))
            send_ref = send_match.group(1).upper()

            # Look for "by X dB/%" pattern
            by_match = re.search(r"by\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?", q)

            if by_match:
                value = float(by_match.group(1))
                unit = by_match.group(2)
                # Apply direction
                if any(word in q for word in decrease_verbs):
                    value = -abs(value)
                else:
                    value = abs(value)
                # Pass through explicit units, otherwise mark as display
                if unit:
                    unit_l = unit.lower()
                    if unit_l in ("db",):
                        unit_out = "dB"
                    elif unit_l in ("%", "percent"):
                        unit_out = "%"
                    else:
                        unit_out = "display"
                else:
                    unit_out = "display"
            else:
                # No "by X" found, default to +/- 3 dB
                value = 3 if not any(word in q for word in decrease_verbs) else -3
                unit_out = "display"

            return {
                "intent": "relative_change",
                "targets": [{"track": f"Track {track_num}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "relative", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }

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
            unit_out = "display"
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
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
            unit_out = "display"
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    except Exception:
        pass

    return None


def parse_return_sends_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: increase return A send B by 3 dB, or decrease return B send C by 10%"""
    increase_verbs, decrease_verbs = get_relative_change_verbs()
    all_verbs = increase_verbs + decrease_verbs

    # Look for send with increase/decrease verbs
    if "send" in q and any(word in q for word in all_verbs):
        # Match return letter and send letter
        return_match = re.search(r"return\s+([a-d])\b", q)
        send_match = re.search(r"send\s+([a-d])\b", q)

        if return_match and send_match:
            return_ref = return_match.group(1).upper()
            send_ref = send_match.group(1).upper()

            # Look for "by X dB/%" pattern
            by_match = re.search(r"by\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?", q)

            if by_match:
                value = float(by_match.group(1))
                unit = by_match.group(2)
                # Apply direction
                if any(word in q for word in decrease_verbs):
                    value = -abs(value)
                else:
                    value = abs(value)
                # Pass through explicit units, otherwise mark as display
                if unit:
                    unit_l = unit.lower()
                    if unit_l in ("db",):
                        unit_out = "dB"
                    elif unit_l in ("%", "percent"):
                        unit_out = "%"
                    else:
                        unit_out = "display"
                else:
                    unit_out = "display"
            else:
                # No "by X" found, default to +/- 3 dB
                value = 3 if not any(word in q for word in decrease_verbs) else -3
                unit_out = "display"

            return {
                "intent": "relative_change",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": f"send {send_ref}"}],
                "operation": {"type": "relative", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }

    return None


def parse_return_volume(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set return A volume to -3 dB"""
    try:
        m = re.search(r"\bset\s+return\s+([a-d])\s+volume\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if m:
            return_ref = m.group(1).upper()
            value = float(m.group(2))
            unit = m.group(3)
            unit_out = "display"
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",): unit_out = "dB"
                elif unit_l in ("%", "percent"): unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_return_volume_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: increase return A volume by 3 dB, or add 3 dB to return A volume"""
    increase_verbs, decrease_verbs = get_relative_change_verbs()
    all_verbs = increase_verbs + decrease_verbs
    if "volume" in q and any(word in q for word in all_verbs):
        # Try to extract return letter
        return_match = re.search(r"return\s+([a-d])\b", q)
        if return_match:
            return_ref = return_match.group(1).upper()

            # Try to extract "by X" amount with optional unit
            by_match = re.search(r"by\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?", q)

            if by_match:
                value = float(by_match.group(1))
                unit = by_match.group(2)

                # Apply direction using config verbs
                if any(word in q for word in decrease_verbs):
                    value = -abs(value)
                else:
                    value = abs(value)

                # Pass through explicit units, otherwise mark as display for intent_mapper to look up
                if unit:
                    unit_l = unit.lower()
                    if unit_l in ("db",):
                        unit_out = "dB"
                    elif unit_l in ("%", "percent"):
                        unit_out = "%"
                    else:
                        unit_out = "display"
                else:
                    unit_out = "display"
            else:
                # Fallback: use default 3dB if no "by X" found
                value = 3
                if any(word in q for word in decrease_verbs):
                    value = -3
                unit_out = "display"

            return {
                "intent": "relative_change",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "relative", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    return None


def parse_return_pan_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: pan return A 20% to the right, or pan return A left by 10"""
    increase_verbs, decrease_verbs = get_relative_change_verbs()
    all_verbs = increase_verbs + decrease_verbs

    # Trigger on: explicit verbs OR directional keywords (left/right)
    if "pan" in q and (any(word in q for word in all_verbs) or "left" in q or "right" in q):
        # Try to extract return letter
        return_match = re.search(r"return\s+([a-d])\b", q)
        if return_match:
            return_ref = return_match.group(1).upper()

            # Try to extract "by X" or "X to the left/right"
            by_match = re.search(r"by\s+(-?\d+(?:\.\d+)?)(?:\s*(%))?", q)

            if by_match:
                value = float(by_match.group(1))
                unit = by_match.group(2)

                # Apply direction using config verbs
                if any(word in q for word in decrease_verbs):
                    value = -abs(value)
                elif "left" in q:
                    value = -abs(value)
                elif "right" in q:
                    value = abs(value)
                else:
                    value = abs(value)

                # Pan always uses %
                unit_out = "%"
            else:
                # Fallback: use default 10% if no "by X" found
                value = 10
                if any(word in q for word in decrease_verbs) or "left" in q:
                    value = -10
                unit_out = "%"

            return {
                "intent": "relative_change",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": "pan"}],
                "operation": {"type": "relative", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    return None


def parse_return_solo_mute(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: solo return A, mute return B"""
    try:
        m = re.search(r"\b(solo|unsolo|mute|unmute)\s+return\s+([a-d])\b", q)
        if m:
            action = m.group(1).lower()
            return_ref = m.group(2).upper()
            param = 'solo' if 'solo' in action else 'mute'
            value = 0.0 if action in ('unsolo', 'unmute') else 1.0
            return {
                "intent": "set_parameter",
                "targets": [{"track": f"Return {return_ref}", "plugin": None, "parameter": param}],
                "operation": {"type": "absolute", "value": value, "unit": None},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_master_volume_absolute(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set master volume to -3 dB"""
    try:
        m = re.search(r"\bset\s+master\s+volume\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if m:
            value = float(m.group(1))
            unit = m.group(2)
            unit_out = "display"
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",):
                    unit_out = "display"
                elif unit_l in ("%", "percent"):
                    unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": "Master", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    except Exception:
        pass

    # Variant without 'volume' keyword
    try:
        m = re.search(r"\bset\s+master\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if m:
            value = float(m.group(1))
            unit = m.group(2)
            unit_out = "display"
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",):
                    unit_out = "display"
                elif unit_l in ("%", "percent"):
                    unit_out = "%"
            return {
                "intent": "set_parameter",
                "targets": [{"track": "Master", "plugin": None, "parameter": "volume"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    except Exception:
        pass

    return None


def parse_master_volume_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: increase master volume by 3 dB, or decrease master by 20%"""
    increase_verbs, decrease_verbs = get_relative_change_verbs()
    all_verbs = increase_verbs + decrease_verbs

    # Require 'volume' to avoid catching 'cue' commands
    if "master" in q and "volume" in q and any(word in q for word in all_verbs):
        # Look for "by X dB/%" pattern
        by_match = re.search(r"by\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?", q)

        if by_match:
            value = float(by_match.group(1))
            unit = by_match.group(2)
            # Apply direction
            if any(word in q for word in decrease_verbs):
                value = -abs(value)
            else:
                value = abs(value)
            # Pass through explicit units, otherwise mark as display
            if unit:
                unit_l = unit.lower()
                if unit_l in ("db",):
                    unit_out = "dB"
                elif unit_l in ("%", "percent"):
                    unit_out = "%"
                else:
                    unit_out = "display"
            else:
                unit_out = "display"
        else:
            # No "by X" found, default to +/- 3 display units
            value = 3 if not any(word in q for word in decrease_verbs) else -3
            unit_out = "display"

        return {
            "intent": "relative_change",
            "targets": [{"track": "Master", "plugin": None, "parameter": "volume"}],
            "operation": {"type": "relative", "value": value, "unit": unit_out},
            "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
        }
    return None


# Main mixer parser coordinator
MIXER_PARSERS = [
    parse_track_volume_absolute,
    parse_track_volume_relative,
    parse_track_pan,
    parse_track_pan_relative,
    parse_track_solo_mute,
    parse_track_sends,
    parse_track_sends_relative,
    parse_return_sends,
    parse_return_sends_relative,
    parse_return_volume,
    parse_return_volume_relative,
    parse_return_pan_relative,
    parse_return_solo_mute,
    parse_master_volume_absolute,
    # Master cue and pan handlers should precede volume-relative to avoid misrouting
    # (e.g., "decrease master cue by 5" should not hit volume)
    # Added in this patch:
    # - parse_master_cue_absolute
    # - parse_master_cue_relative
    # - parse_master_pan_relative
    # Then volume-relative last among master handlers
    
    # Placeholders; actual functions defined below
    # They will be appended to the list once defined
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


# ----------------- New: Master cue and pan parsers -----------------

def parse_master_cue_absolute(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: set master cue to -6 dB (defaults to dB)."""
    try:
        m = re.search(r"\bset\s+master\s+cue\s+(?:to|at)\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?\b", q)
        if m:
            value = float(m.group(1))
            unit = m.group(2)
            if unit:
                u = unit.lower()
                unit_out = "dB" if u in ("db",) else "%" if u in ("%", "percent") else "display"
            else:
                # Default for cue is dB semantics
                unit_out = "dB"
            return {
                "intent": "set_parameter",
                "targets": [{"track": "Master", "plugin": None, "parameter": "cue"}],
                "operation": {"type": "absolute", "value": value, "unit": unit_out},
                "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
            }
    except Exception:
        pass
    return None


def parse_master_cue_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: increase/decrease master cue by X [dB|%].

    Defaults to dB if unit not specified.
    """
    increase_verbs, decrease_verbs = get_relative_change_verbs()
    all_verbs = increase_verbs + decrease_verbs

    if "master" in q and "cue" in q and any(word in q for word in all_verbs):
        by_match = re.search(r"by\s+(-?\d+(?:\.\d+)?)(?:\s*(db|dB|%|percent))?", q)
        if by_match:
            value = float(by_match.group(1))
            unit = by_match.group(2)
            value = -abs(value) if any(word in q for word in decrease_verbs) else abs(value)
            if unit:
                u = unit.lower()
                unit_out = "dB" if u in ("db",) else "%" if u in ("%", "percent") else "display"
            else:
                unit_out = "dB"
        else:
            value = -3 if any(word in q for word in decrease_verbs) else 3
            unit_out = "dB"

        return {
            "intent": "relative_change",
            "targets": [{"track": "Master", "plugin": None, "parameter": "cue"}],
            "operation": {"type": "relative", "value": value, "unit": unit_out},
            "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
        }
    return None


def parse_master_pan_relative(q: str, query: str, error_msg: str, model_preference: str | None) -> Dict[str, Any] | None:
    """Parse: pan master left/right by X [%].

    Always uses percent for pan.
    """
    if "pan" in q and "master" in q and ("left" in q or "right" in q or "by" in q):
        by_match = re.search(r"by\s+(-?\d+(?:\.\d+)?)(?:\s*(%|percent))?", q)
        if by_match:
            value = float(by_match.group(1))
        else:
            # Default step if no explicit amount
            value = 10.0
        # Direction
        if "left" in q and value > 0:
            value = -value
        elif "right" in q and value < 0:
            value = -value
        return {
            "intent": "relative_change",
            "targets": [{"track": "Master", "plugin": None, "parameter": "pan"}],
            "operation": {"type": "relative", "value": value, "unit": "%"},
            "meta": {"utterance": query, "fallback": True, "error": error_msg, "model_selected": _safe_model_name(model_preference)}
        }
    return None


# Append new parsers in appropriate order before master volume relative
MIXER_PARSERS.extend([
    parse_master_cue_absolute,
    parse_master_cue_relative,
    parse_master_pan_relative,
    parse_master_volume_relative,
])
