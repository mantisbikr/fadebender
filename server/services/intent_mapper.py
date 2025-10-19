from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

_MIXER_PARAM_ALIASES = {
    # mixer field aliases → canonical
    "vol": "volume",
    "level": "volume",
    "gain": "volume",
    "loudness": "volume",
    "pan": "pan",
    "balance": "pan",
    "mute": "mute",
    "unmute": "mute",
    "solo": "solo",
    "unsolo": "solo",
}

def _normalize_mixer_param(name: str) -> str:
    n = (name or "").strip().lower()
    return _MIXER_PARAM_ALIASES.get(n, n)


def _parse_track_target(track_str: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Parse track string and return (domain, target_fields).

    Returns:
        ("track", {"track_index": 1}) for "Track 1"
        ("return", {"return_ref": "A"}) for "Return A"
        ("master", {}) for "Master"
        (None, None) if invalid
    """
    if not track_str:
        return None, None

    try:
        s = str(track_str).strip()

        # Track N → domain "track", track_index
        if s.lower().startswith("track "):
            n = int(s.split()[1])
            return "track", {"track_index": n}

        # Return A/B/C → domain "return", return_ref
        if s.lower().startswith("return "):
            letter = s.split()[1].upper()
            return "return", {"return_ref": letter}

        # Master → domain "master"
        if s.lower() == "master":
            return "master", {}

        # Plain digit → assume track index
        if s.isdigit():
            return "track", {"track_index": int(s)}

        # Otherwise treat as track by index if it's a number
        try:
            idx = int(s)
            return "track", {"track_index": idx}
        except:
            pass

    except Exception:
        pass

    return None, None


def map_llm_to_canonical(llm_intent: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Map the LLM intent JSON into a canonical intent dict.

    Returns (canonical_intent_dict | None, errors[])
    """
    errors: List[str] = []

    kind = (llm_intent or {}).get("intent")
    targets = (llm_intent or {}).get("targets") or []
    op = (llm_intent or {}).get("operation") or {}

    # Only map control intents here; questions/clarifications bubble up to caller
    if kind not in ("set_parameter", "relative_change"):
        errors.append(f"non_control_intent:{kind}")
        return None, errors

    target = targets[0] if targets else {}
    track_str = target.get("track")
    domain, target_fields = _parse_track_target(track_str)

    if not domain or target_fields is None:
        errors.append("missing_or_invalid_track")
        return None, errors

    parameter = (target.get("parameter") or "").lower()
    parameter = _normalize_mixer_param(parameter)
    plugin = target.get("plugin")
    device_ordinal = target.get("device_ordinal")
    op_type = (op.get("type") or "").lower()
    value = op.get("value")
    unit = op.get("unit")

    # Validate operation type and value (only absolute supported for now)
    if op_type != "absolute":
        errors.append(f"unsupported_op_type:{op_type}")
        return None, errors

    # For mixer/sends we require numeric; for device we allow display strings
    def _to_float(v: Any) -> Optional[float]:
        try:
            return float(v)
        except Exception:
            return None

    # Mixer controls: volume, pan, mute, solo
    if parameter in ("volume", "pan", "mute", "solo"):
        amount = _to_float(value)
        if amount is None:
            errors.append("invalid_value_amount")
            return None, errors
        intent = {
            "domain": domain,
            "action": "set",
            "field": parameter,
            "value": amount,
            "unit": unit,
            **target_fields
        }
        return intent, []

    # Send controls: "send A", "send B", etc.
    if parameter.startswith("send ") or parameter in ("send", "sends"):
        amount = _to_float(value)
        if amount is None:
            errors.append("invalid_value_amount")
            return None, errors
        if not parameter.startswith("send "):
            # Try to extract trailing letter from raw text if provided, else require client to add send_ref downstream
            pass
        send_letter = parameter.split()[-1].upper()  # Extract "A", "B", etc.
        intent = {
            "domain": domain,
            "action": "set",
            "field": "send",
            "send_ref": send_letter,
            "value": amount,
            "unit": unit,
            **target_fields
        }
        return intent, []

    # Device parameters: if plugin is specified
    if plugin:
        # Device params support numeric and display label values
        intent: Dict[str, Any] = {
            "domain": "device",
            "action": "set",
            "param_ref": parameter,
            **target_fields
        }
        # Pass through device name as a hint unless it's a generic placeholder
        try:
            pl = str(plugin).strip().lower()
            if pl not in ("device", "fx", "effect", "plugin") and pl:
                intent["device_name_hint"] = str(plugin)
        except Exception:
            pass
        try:
            if device_ordinal is not None:
                intent["device_ordinal_hint"] = int(device_ordinal)
        except Exception:
            pass
        amount = _to_float(value)
        unit_l = (unit or "").strip().lower()
        if amount is not None:
            intent["value"] = amount
            if unit is not None:
                intent["unit"] = unit
        else:
            # Treat as display string selection (e.g., Mode → Distance)
            if isinstance(value, str):
                intent["display"] = value
                # Keep unit if explicitly marked as 'display', else omit
                if unit_l == "display":
                    intent["unit"] = unit
            else:
                errors.append("invalid_value_amount")
                return None, errors
        # Need device_index - for now use 0 (first device on track/return)
        intent["device_index"] = 0
        return intent, []

    errors.append(f"unsupported_parameter:{parameter}")
    return None, errors
