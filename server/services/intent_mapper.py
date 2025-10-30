from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from server.config.app_config import get_mixer_param_aliases

# Mixer field aliases (config-driven)
_MIXER_PARAM_ALIASES: Dict[str, str] = {}
try:
    _MIXER_PARAM_ALIASES = get_mixer_param_aliases() or {}
except Exception:
    _MIXER_PARAM_ALIASES = {}

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

    param_raw = (target.get("parameter") or "")
    plugin = target.get("plugin")
    device_ordinal = target.get("device_ordinal")

    # Only normalize mixer params if there's NO plugin (device operations keep original parameter names)
    parameter = str(param_raw).lower() if plugin else _normalize_mixer_param(str(param_raw).lower())
    op_type = (op.get("type") or "").lower()
    value = op.get("value")
    unit = op.get("unit")

    # Handle relative changes: convert to absolute by reading current value
    if op_type == "relative":
        # Import here to avoid circular dependency
        from server.core.deps import get_value_registry

        try:
            registry = get_value_registry()
            mixer_data = registry.get_mixer()

            # Get current value from registry
            current_value = None
            if domain == "track" and "track_index" in target_fields:
                idx = target_fields["track_index"]
                track_data = mixer_data.get("track", {}).get(idx, {})
                param_data = track_data.get(parameter, {})
                current_value = param_data.get("normalized")
            elif domain == "return" and "return_ref" in target_fields:
                # Map return letter to index (A=0, B=1, etc.)
                letter = target_fields["return_ref"]
                idx = ord(letter.upper()) - ord('A')
                return_data = mixer_data.get("return", {}).get(idx, {})
                param_data = return_data.get(parameter, {})
                current_value = param_data.get("normalized")

            if current_value is None:
                # If we don't have a current value, can't do relative change
                errors.append("relative_change_no_current_value")
                return None, errors

            # Calculate new absolute value
            # Need to convert delta to same scale as current (normalized 0-1)
            delta_value = float(value)
            unit_l = (unit or "").lower()

            if parameter == "volume":
                # Import conversion functions
                from server.volume_utils import live_float_to_db

                # Current value is normalized (0-1), convert to dB for calculation
                current_db = live_float_to_db(current_value)

                if unit_l in ("%", "percent"):
                    # Explicit % means multiplicative percentage change
                    # E.g., "increase by 20%" means multiply amplitude by 1.20
                    multiplier = 1.0 + (delta_value / 100.0)
                    new_normalized = current_value * multiplier
                    new_normalized = max(0.0, min(1.0, new_normalized))
                    value = live_float_to_db(new_normalized)
                    unit = "dB"
                else:
                    # No unit, "display", or "dB" → additive in standard unit (dB)
                    # E.g., "increase by 3" or "increase by 3 dB" → add 3 dB
                    new_db = current_db + delta_value
                    value = new_db  # Keep as display value
                    unit = "dB"
            else:
                # For other parameters (pan, etc.), treat as direct normalized delta
                if unit_l in ("%", "percent"):
                    delta_normalized = delta_value / 100.0
                else:
                    # For display values, assume they're already in the right scale
                    delta_normalized = delta_value / 100.0  # Treat as percent

                value = current_value + delta_normalized

            # Now treat as absolute
            op_type = "absolute"

        except Exception as e:
            errors.append(f"relative_change_error:{str(e)}")
            return None, errors

    # Validate operation type and value
    if op_type != "absolute":
        errors.append(f"unsupported_op_type:{op_type}")
        return None, errors

    # For mixer/sends we require numeric; for device we allow display strings
    def _to_float(v: Any) -> Optional[float]:
        try:
            return float(v)
        except Exception:
            return None

    # Helper: detect send letter even when spacing/case is odd (e.g., "sendB", "Send   A")
    def _extract_send_letter(p: str) -> Optional[str]:
        try:
            import re as _re
            s = str(p or "").lower()
            m = _re.search(r"\bsend\s*([a-d])\b", s)
            if m:
                return m.group(1).upper()
            # Very conservative fallback: exact single letter A-D only, and only if plugin is empty/generic
            s_clean = s.strip()
            if s_clean in ("a","b","c","d"):
                return s_clean.upper()
        except Exception:
            pass
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

    # Send controls: "send A", "send B", etc. (prefer this mapping even if a plugin is present)
    send_letter = None
    if parameter.startswith("send "):
        try:
            send_letter = parameter.split()[-1].upper()
        except Exception:
            send_letter = None
    if send_letter is None:
        send_letter = _extract_send_letter(param_raw)
    if (parameter in ("send", "sends")) and send_letter is None:
        # No letter specified; treat as error for now
        errors.append("send_letter_missing")
        return None, errors
    if send_letter is not None:
        amount = _to_float(value)
        if amount is None:
            errors.append("invalid_value_amount")
            return None, errors
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
